import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from app import create_app
from database import get_generation, list_attempts, list_documents


EXCERPT = 'L’énergie solaire alimente le chauffage. Le rayonnement réchauffe le capteur solaire.'


class StudioTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.database = str(Path(folder.name) / 'studio.sqlite')
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'test-only',
            'DATABASE': self.database,
            'AI_MODE': 'local',
            'AI_SERVICE_URL': '',
        })
        self.client = self.app.test_client()

    def post(self, client, url, data):
        client.get(url if url == '/inscription' else '/studio')
        with client.session_transaction() as session:
            token = session['csrf_token']
        return client.post(url, data={**data, 'csrf_token': token})

    def register(self, client, username='meryem'):
        self.assertEqual(self.post(client, '/inscription', {
            'username': username, 'password': 'Phrase de test 234!',
        }).status_code, 302)
        with client.session_transaction() as session:
            return session['user_id']

    def import_document(self, client, title='Physique', content=EXCERPT):
        return self.post(client, '/documents', {'title': title, 'content': content})

    def generate(self, client, kind='summary', query='énergie solaire', scope='personal'):
        return self.post(client, '/studio', {'kind': kind, 'query': query, 'scope': scope})

    def test_studio_requires_authentication_and_csrf(self):
        for path in ('/studio', '/documents'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.endswith('/connexion'))
        self.register(self.client)
        self.assertEqual(self.client.post('/studio', data={'kind': 'summary', 'query': 'Python'}).status_code, 400)
        self.assertEqual(self.client.post('/documents', data={'title': 'Physique', 'content': EXCERPT}).status_code, 400)

    def test_generates_and_exports_all_local_formats(self):
        self.register(self.client)
        self.assertEqual(self.import_document(self.client).status_code, 302)
        for kind, output in [('summary', 'content'), ('flashcards', 'cards'), ('quiz', 'questions')]:
            with self.subTest(kind=kind):
                response = self.generate(self.client, kind=kind)
                self.assertEqual(response.status_code, 302)
                page = self.client.get(response.location).get_data(as_text=True)
                self.assertIn('Mode local extractif', page)
                self.assertIn('Physique', page)
                self.assertIn('Pertinence', page)
                export = self.client.get(response.location + '/export.json')
                self.assertIn('attachment', export.headers['Content-Disposition'])
                result = export.get_json()
                self.assertEqual(result['material']['kind'], kind)
                self.assertIn(output, result['material'])
                self.assertEqual(result['sources'][0]['text'], EXCERPT)
                self.assertNotIn('user_id', result)
                if kind == 'quiz':
                    self.assertEqual(set(result['material']['questions'][0]), {'question', 'options'})

    def test_source_scope_and_irrelevant_query(self):
        self.register(self.client)
        self.import_document(self.client)
        self.assertEqual(self.generate(self.client, query='guitare').status_code, 400)
        self.assertEqual(self.generate(self.client, scope='courses').status_code, 400)
        response = self.generate(self.client, query='variable', scope='courses')
        self.assertEqual(response.status_code, 302)
        sources = self.client.get(response.location + '/export.json').get_json()['sources']
        self.assertTrue(all(s['document_id'].startswith('course:') for s in sources))
        self.assertEqual(self.generate(self.client, query='Python\0', scope='all').status_code, 400)
        self.assertEqual(self.generate(self.client, scope='unknown').status_code, 400)

    def test_document_and_production_are_visible_only_to_owner(self):
        user_id = self.register(self.client)
        self.assertEqual(self.import_document(self.client, 'Titre confidentiel').status_code, 302)
        document = list_documents(self.database, user_id)[0]
        response = self.generate(self.client, kind='quiz')
        other = self.app.test_client()
        self.register(other, 'salma')
        self.assertNotIn('Titre confidentiel', other.get('/documents').get_data(as_text=True))
        self.assertEqual(self.generate(other).status_code, 400)
        self.assertEqual(other.get(response.location).status_code, 404)
        self.assertEqual(other.get(response.location + '/export.json').status_code, 404)
        self.assertEqual(other.get(response.location + '/quiz').status_code, 404)
        self.assertEqual(self.post(other, response.location + '/quiz', {'q0': '0'}).status_code, 404)
        delete_path = f"/documents/{document['id']}/supprimer"
        self.assertEqual(self.post(other, delete_path, {}).status_code, 404)
        self.assertEqual(self.post(self.client, delete_path, {}).status_code, 302)
        self.assertEqual(list_documents(self.database, user_id), [])
        self.assertIn('Titre confidentiel', self.client.get(response.location).get_data(as_text=True))

    def test_text_file_import_and_input_limits(self):
        user_id = self.register(self.client)
        cases = [('', EXCERPT), ('T' * 501, EXCERPT), ('Titre\0', EXCERPT), ('Titre', 'Énergie\0solaire'),
                 ('Titre', 'a' * 50001), ('Titre', '   ')]
        for title, content in cases:
            with self.subTest(title=len(title), content=len(content)):
                self.assertEqual(self.import_document(self.client, title, content).status_code, 400)
        for filename, data, status in [('texte.txt', b'\xff', 400), ('fichier.exe', b'abc', 400),
                                       ('long.txt', b'a' * (1024 * 1024 + 1), 413),
                                       ('texte.MD', b'\xef\xbb\xbf' + EXCERPT.encode(), 302)]:
            with self.subTest(filename=filename):
                response = self.post(self.client, '/documents', {
                    'title': 'Texte UTF-8', 'file': (io.BytesIO(data), filename),
                })
                self.assertEqual(response.status_code, status)
        self.assertEqual([doc['content'] for doc in list_documents(self.database, user_id)], [EXCERPT])

    def test_pdf_import_extracts_text_and_rejects_scan(self):
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

        user_id = self.register(self.client)
        writer = PdfWriter()
        page = writer.add_blank_page(width=200, height=200)
        scan = io.BytesIO()
        writer.write(scan)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                                 NameObject('/Subtype'): NameObject('/Type1'),
                                 NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({
            NameObject('/Font'): DictionaryObject({NameObject('/F1'): font}),
        })
        text = DecodedStreamObject()
        text.set_data(b'BT /F1 12 Tf 10 100 Td (Variables Python) Tj ET')
        page[NameObject('/Contents')] = text
        pdf = io.BytesIO()
        writer.write(pdf)

        for data, expected in [(pdf.getvalue(), 302), (scan.getvalue(), 400), (b'Bad file', 400)]:
            response = self.post(self.client, '/documents', {
                'title': 'Leçon PDF', 'file': (io.BytesIO(data), 'lecon.pdf'),
            })
            self.assertEqual(response.status_code, expected)
        self.assertEqual([doc['content'] for doc in list_documents(self.database, user_id)], ['Variables Python'])

    def test_document_count_limit(self):
        from database import add_document

        user_id = self.register(self.client)
        for index in range(30):
            add_document(self.database, user_id, f'Import {index}', EXCERPT)
        self.assertEqual(self.import_document(self.client).status_code, 400)
        self.assertEqual(len(list_documents(self.database, user_id)), 30)

    def test_generated_quiz_grades_on_server_and_stays_out_of_course_statistics(self):
        user_id = self.register(self.client)
        self.import_document(self.client)
        response = self.generate(self.client, kind='quiz')
        generation_id = response.location.rsplit('/', 1)[1]
        material = get_generation(self.database, user_id, generation_id)['material']
        quiz_path = response.location + '/quiz'

        self.assertEqual(self.post(self.client, quiz_path, {'q0': '4'}).status_code, 400)
        self.assertEqual(list_attempts(self.database, user_id), [])
        correct = {f'q{index}': question['answer'] for index, question in enumerate(material['questions'])}
        result = self.post(self.client, quiz_path, correct)
        self.assertEqual(result.status_code, 302)
        self.assertIn('Bonne réponse', self.client.get(result.location).get_data(as_text=True))
        attempt = list_attempts(self.database, user_id)[0]
        self.assertEqual(attempt['score'], attempt['total'])
        self.assertIsNone(attempt['course_id'])
        self.assertEqual(attempt['generation_id'], generation_id)
        progress = self.client.get('/progression').get_data(as_text=True)
        self.assertIn('<strong>0</strong><span>Tentatives sur les cours', progress)
        self.assertIn('Quiz généré', progress)

    def test_service_generation_uses_returned_mode_and_keeps_corrections_private(self):
        self.register(self.client)
        self.import_document(self.client)
        self.app.config.update(AI_SERVICE_URL='http://ai:8001/', AI_SERVICE_TOKEN='service-secret')
        result = {'mode': 'llm', 'kind': 'quiz', 'title': '<script>Quatre termes</script>', 'questions': [
            {'question': 'Quel terme ?', 'options': ['un', 'deux', 'trois', 'quatre'], 'answer': 2,
             'explanation': 'CORRIGE_CONFIDENTIEL'},
        ]}
        with patch('studio.urlopen', return_value=io.BytesIO(json.dumps(result).encode())) as transport:
            response = self.generate(self.client, kind='quiz')
        self.assertEqual(response.status_code, 302)
        request = transport.call_args.args[0]
        self.assertEqual(request.full_url, 'http://ai:8001/generate')
        self.assertEqual(request.get_header('Authorization'), 'Bearer service-secret')
        self.assertEqual(transport.call_args.kwargs['timeout'], 55)
        self.assertEqual(json.loads(request.data)['kind'], 'quiz')
        for suffix in ('', '/quiz', '/export.json'):
            body = self.client.get(response.location + suffix).get_data(as_text=True)
            self.assertNotIn('CORRIGE_CONFIDENTIEL', body)
            if suffix != '/export.json':
                self.assertNotIn('<script>Quatre termes', body)
                self.assertIn('&lt;script&gt;', body)
        self.assertIn('LLM', self.client.get(response.location).get_data(as_text=True))
        correction = self.post(self.client, response.location + '/quiz', {'q0': '2'})
        self.assertIn('CORRIGE_CONFIDENTIEL', self.client.get(correction.location).get_data(as_text=True))

    def test_service_errors_do_not_fall_back_or_expose_secret(self):
        self.register(self.client)
        self.import_document(self.client)
        self.app.config.update(AI_SERVICE_URL='http://ai:8001', AI_SERVICE_TOKEN='service-secret')
        invalid = [b'{"error":"service-secret"}', b'x' * (128 * 1024 + 1)]
        for data in invalid:
            with self.subTest(length=len(data)), patch('studio.urlopen', return_value=io.BytesIO(data)):
                response = self.generate(self.client)
                self.assertEqual(response.status_code, 502)
                self.assertNotIn('service-secret', response.get_data(as_text=True))
        with patch('studio.urlopen', side_effect=URLError('service-secret')):
            response = self.generate(self.client)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn('service-secret', response.get_data(as_text=True))
        redirect_body = io.BytesIO(b'placeholder')
        failure = HTTPError('http://ai:8001/generate', 302, 'Found', {}, redirect_body)
        with patch('studio.urlopen', side_effect=failure):
            self.assertEqual(self.generate(self.client).status_code, 502)
        self.assertTrue(redirect_body.closed)
        self.assertNotIn('/productions/', self.client.get('/studio').get_data(as_text=True))
