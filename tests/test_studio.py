import io
import json
import tempfile
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from app import create_app
from courses import COURSES
from database import get_generation, list_attempts, list_documents, save_generation

EXCERPT = 'L’énergie solaire alimente le chauffage. Le rayonnement réchauffe le capteur solaire.'


def fake_search_results(documents, query, **kwargs):
    if not documents:
        return []
    document = documents[0]
    return [
        {
            'document_id': document['id'],
            'title': document['title'],
            'text': document['content'][:300],
            'chunk_index': 0,
            'score': 0.85,
        }
    ]


def fake_material(kind, query, sources, config):
    content = {
        'summary': {'content': 'Résumé de test.'},
        'flashcards': {'cards': [{'front': 'Question de test ?', 'back': 'Réponse de test.'}]},
        'quiz': {
            'questions': [
                {
                    'question': 'Quel terme ?',
                    'options': ['un', 'deux', 'trois', 'quatre'],
                    'answer': 2,
                    'explanation': 'Correction de test.',
                }
            ]
        },
    }[kind]
    return {'mode': 'llm', 'kind': kind, 'title': 'Support de test', **content}


class StudioTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.database = str(Path(folder.name) / 'studio.sqlite')
        self.index_dir = Path(folder.name) / 'indexes'
        self.app = create_app(
            {
                'TESTING': True,
                'SECRET_KEY': 'test-only',
                'DATABASE': self.database,
                'AI_SERVICE_URL': '',
                'EMBEDDING_MODEL': 'modele-de-test',
                'RAG_INDEX_DIR': self.index_dir,
                'LLM_API_KEY': 'cle-de-test-confidentielle',
                'LLM_MODEL': 'llm-de-test',
            }
        )
        self.client = self.app.test_client()
        self.search = self.enterContext(
            patch('studio.search_documents', side_effect=fake_search_results)
        )
        self.generation = self.enterContext(
            patch('studio.generate_material', side_effect=fake_material)
        )

    def post(self, client, url, data):
        client.get(url if url == '/inscription' else '/studio')
        with client.session_transaction() as session:
            token = session['csrf_token']
        return client.post(url, data={**data, 'csrf_token': token})

    def register(self, client, username='meryem'):
        self.assertEqual(
            self.post(
                client,
                '/inscription',
                {
                    'username': username,
                    'password': 'Phrase de test 234!',
                },
            ).status_code,
            302,
        )
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
        self.assertEqual(
            self.client.post('/studio', data={'kind': 'summary', 'query': 'Python'}).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                '/documents', data={'title': 'Physique', 'content': EXCERPT}
            ).status_code,
            400,
        )

    def test_generates_and_exports_all_llm_formats(self):
        self.register(self.client)
        self.assertEqual(self.import_document(self.client).status_code, 302)
        for kind, output in [
            ('summary', 'content'),
            ('flashcards', 'cards'),
            ('quiz', 'questions'),
        ]:
            with self.subTest(kind=kind):
                response = self.generate(self.client, kind=kind)
                self.assertEqual(response.status_code, 302)
                page = self.client.get(response.location).get_data(as_text=True)
                self.assertIn('Mode LLM', page)
                self.assertIn('[1] Physique', page)
                self.assertIn('Similarité sémantique', page)
                export = self.client.get(response.location + '/export.json')
                self.assertIn('attachment', export.headers['Content-Disposition'])
                result = export.get_json()
                self.assertEqual(result['material']['kind'], kind)
                self.assertEqual(result['material']['retrieval_method'], 'semantic')
                self.assertIn(output, result['material'])
                self.assertEqual(result['sources'][0]['text'], EXCERPT)
                self.assertNotIn('user_id', result)
                if kind == 'quiz':
                    self.assertEqual(
                        set(result['material']['questions'][0]), {'question', 'options'}
                    )

    def test_source_scopes_pass_owned_corpus_and_private_namespaces(self):
        user_id = self.register(self.client)
        self.import_document(self.client)
        document = list_documents(self.database, user_id)[0]
        other = self.app.test_client()
        other_id = self.register(other, 'salma')
        self.import_document(other, 'Titre de Salma')
        other_document = list_documents(self.database, other_id)[0]
        courses = {'course:' + course['id'] for course in COURSES}
        cases = [
            (self.client, user_id, 'personal', {document['id']}),
            (self.client, user_id, 'courses', courses),
            (self.client, user_id, 'all', courses | {document['id']}),
            (other, other_id, 'all', courses | {other_document['id']}),
        ]
        for client, owner, scope, expected in cases:
            with self.subTest(owner=owner, scope=scope):
                response = self.generate(client, query='variable', scope=scope)
                self.assertEqual(response.status_code, 302)
                args, kwargs = self.search.call_args
                self.assertEqual({source['id'] for source in args[0]}, expected)
                self.assertEqual(args[1], 'variable')
                self.assertEqual(kwargs['namespace'], f'{owner}:{scope}')
                self.assertIs(kwargs['config'], self.app.config)
                sources = client.get(response.location + '/export.json').get_json()['sources']
                self.assertTrue(all(source['document_id'] in expected for source in sources))

        self.assertEqual(
            self.post(self.client, f'/documents/{document["id"]}/supprimer', {}).status_code, 302
        )
        self.assertEqual(self.generate(self.client, scope='all').status_code, 302)
        self.assertEqual({source['id'] for source in self.search.call_args.args[0]}, courses)
        self.assertEqual(self.search.call_args.kwargs['namespace'], f'{user_id}:all')
        self.import_document(self.client, 'Nouvelle leçon')
        replacement = list_documents(self.database, user_id)[0]
        self.assertEqual(self.generate(self.client, scope='all').status_code, 302)
        self.assertEqual(
            {source['id'] for source in self.search.call_args.args[0]},
            courses | {replacement['id']},
        )

    def test_irrelevant_query_and_invalid_input(self):
        self.register(self.client)
        self.import_document(self.client)
        with patch('studio.search_documents', return_value=[]) as search:
            response = self.generate(self.client, query='guitare')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Aucun extrait pertinent', response.get_data(as_text=True))
        search.assert_called_once()
        self.assertEqual(self.generate(self.client, query='Python\0', scope='all').status_code, 400)
        self.assertEqual(self.generate(self.client, scope='unknown').status_code, 400)
        self.search.assert_not_called()
        self.generation.assert_not_called()

    def test_index_error_returns_502_without_saving_material(self):
        from retrieval import RetrievalError

        self.register(self.client)
        self.import_document(self.client)
        self.search.side_effect = RetrievalError('L’index de recherche est indisponible.')
        response = self.generate(self.client)
        self.assertEqual(response.status_code, 502)
        self.assertIn('index de recherche est indisponible', response.get_data(as_text=True))
        self.assertIn('Aucune production enregistrée', response.get_data(as_text=True))
        self.generation.assert_not_called()

    def test_configuration_feedback_keeps_form_available_without_exposing_secrets(self):
        self.register(self.client)
        page = self.client.get('/studio').get_data(as_text=True)
        self.assertNotIn('cle-de-test-confidentielle', page)
        self.assertNotIn('Configurez le modèle', page)
        self.app.config.update(EMBEDDING_MODEL='', LLM_API_KEY='', LLM_MODEL='')
        page = self.client.get('/studio').get_data(as_text=True)
        self.assertIn('Configurez le modèle d’embeddings', page)
        self.assertIn('Configurez le modèle de langage', page)
        self.assertIn('Toutes les sources', page)
        self.assertIn('Générer le support', page)

        self.app.config.update(
            EMBEDDING_MODEL='modele-de-test',
            AI_SERVICE_URL='http://ai:8001',
            AI_SERVICE_TOKEN='jeton-invisible',
        )
        page = self.client.get('/studio').get_data(as_text=True)
        self.assertIn('Le service IA configure le modèle de langage', page)
        self.assertNotIn('Configurez le modèle de langage', page)
        self.assertNotIn('jeton-invisible', page)

    def test_historical_material_remains_available(self):
        user_id = self.register(self.client)
        sources = [
            {
                'document_id': 'course:python',
                'title': 'Leçon',
                'text': EXCERPT,
                'chunk_index': 0,
                'score': 0.85,
            }
        ]
        for mode, label in [('local', 'Génération historique'), ('llm', 'Mode LLM')]:
            with self.subTest(mode=mode):
                old_material = {
                    'mode': mode,
                    'kind': 'summary',
                    'title': 'Ancien résumé',
                    'content': EXCERPT,
                }
                record_id = save_generation(
                    self.database, user_id, 'solaire', old_material, sources
                )
                path = f'/productions/{record_id}'
                page = self.client.get(path).get_data(as_text=True)
                self.assertIn(label, page)
                self.assertIn('Score historique', page)
                self.assertNotIn('Similarité sémantique', page)
                self.assertEqual(
                    self.client.get(path + '/export.json').get_json()['material'], old_material
                )
        self.assertIn('Génération historique', self.client.get('/studio').get_data(as_text=True))

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
        self.assertEqual(
            self.post(other, response.location + '/quiz', {'q0': '0'}).status_code, 404
        )
        delete_path = f'/documents/{document["id"]}/supprimer'
        self.assertEqual(self.post(other, delete_path, {}).status_code, 404)
        self.assertEqual(self.post(self.client, delete_path, {}).status_code, 302)
        self.assertEqual(list_documents(self.database, user_id), [])
        self.assertIn(
            'Titre confidentiel', self.client.get(response.location).get_data(as_text=True)
        )

    def test_malformed_private_ids_return_404_before_sql_lookup(self):
        self.register(self.client)
        with (
            patch('studio.get_generation', return_value=None) as get_generation,
            patch('studio.remove_document', return_value=False) as remove_document,
        ):
            for identifier in ('abc', 'abc%00def'):
                with self.subTest(identifier=identifier):
                    base = f'/productions/{identifier}'
                    for suffix in ('', '/export.json', '/quiz'):
                        self.assertEqual(self.client.get(base + suffix).status_code, 404)
                    self.assertEqual(
                        self.post(self.client, base + '/quiz', {'q0': '0'}).status_code, 404
                    )
                    delete_path = f'/documents/{identifier}/supprimer'
                    self.assertEqual(self.post(self.client, delete_path, {}).status_code, 404)
        get_generation.assert_not_called()
        remove_document.assert_not_called()

    def test_text_file_import_and_input_limits(self):
        user_id = self.register(self.client)
        cases = [
            ('', EXCERPT),
            ('T' * 501, EXCERPT),
            ('Titre\0', EXCERPT),
            ('Titre', 'Énergie\0solaire'),
            ('Titre', 'a' * 50001),
            ('Titre', '   '),
        ]
        for title, content in cases:
            with self.subTest(title=len(title), content=len(content)):
                self.assertEqual(self.import_document(self.client, title, content).status_code, 400)
        for filename, data, status in [
            ('texte.txt', b'\xff', 400),
            ('fichier.exe', b'abc', 400),
            ('nul.txt', b'abc\0def', 400),
            ('surrogate.txt', b'\xed\xa0\x80', 400),
            ('long.txt', b'a' * (1024 * 1024 + 1), 413),
            ('texte.MD', b'\xef\xbb\xbf' + EXCERPT.encode(), 302),
        ]:
            with self.subTest(filename=filename):
                response = self.post(
                    self.client,
                    '/documents',
                    {
                        'title': 'Texte UTF-8',
                        'file': (io.BytesIO(data), filename),
                    },
                )
                self.assertEqual(response.status_code, status)
        self.assertEqual(
            self.post(
                self.client,
                '/documents',
                {
                    'title': 'Import ambigu',
                    'content': EXCERPT,
                    'file': (io.BytesIO(b'Autre texte'), 'texte.txt'),
                },
            ).status_code,
            400,
        )
        self.assertEqual(
            [doc['content'] for doc in list_documents(self.database, user_id)], [EXCERPT]
        )

    def test_pdf_import_extracts_text_and_rejects_scan(self):
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

        user_id = self.register(self.client)
        writer = PdfWriter()
        page = writer.add_blank_page(width=200, height=200)
        scan = io.BytesIO()
        writer.write(scan)
        font = DictionaryObject(
            {
                NameObject('/Type'): NameObject('/Font'),
                NameObject('/Subtype'): NameObject('/Type1'),
                NameObject('/BaseFont'): NameObject('/Helvetica'),
            }
        )
        page[NameObject('/Resources')] = DictionaryObject(
            {
                NameObject('/Font'): DictionaryObject({NameObject('/F1'): font}),
            }
        )
        text = DecodedStreamObject()
        text.set_data(b'BT /F1 12 Tf 10 100 Td (Variables Python) Tj ET')
        page[NameObject('/Contents')] = text
        pdf = io.BytesIO()
        writer.write(pdf)

        encrypted = io.BytesIO()
        writer.encrypt('mot-de-passe')
        writer.write(encrypted)

        for data, expected in [
            (pdf.getvalue(), 302),
            (scan.getvalue(), 400),
            (b'Bad file', 400),
            (encrypted.getvalue(), 400),
        ]:
            response = self.post(
                self.client,
                '/documents',
                {
                    'title': 'Leçon PDF',
                    'file': (io.BytesIO(data), 'lecon.pdf'),
                },
            )
            self.assertEqual(response.status_code, expected)
        self.assertEqual(
            [doc['content'] for doc in list_documents(self.database, user_id)], ['Variables Python']
        )

    def test_document_count_limit(self):
        from database import add_document

        user_id = self.register(self.client)
        for index in range(30):
            add_document(self.database, user_id, f'Import {index}', EXCERPT)
        self.assertEqual(self.import_document(self.client).status_code, 400)
        self.assertEqual(len(list_documents(self.database, user_id)), 30)

    def test_document_changes_clear_only_the_owners_private_indexes(self):
        user_id = self.register(self.client)
        expected = [f'{user_id}:all', f'{user_id}:personal']
        with patch('studio.clear_indexes') as clear:
            self.assertEqual(self.import_document(self.client, title='').status_code, 400)
            clear.assert_not_called()
            self.assertEqual(self.import_document(self.client).status_code, 302)
            self.assertEqual([args.args[0] for args in clear.call_args_list], expected)
            self.assertTrue(all(args.args[1] is self.app.config for args in clear.call_args_list))
            clear.reset_mock()

            (document,) = list_documents(self.database, user_id)
            path = f'/documents/{document["id"]}/supprimer'
            other = self.app.test_client()
            self.register(other, 'salma')
            self.assertEqual(self.post(other, path, {}).status_code, 404)
            clear.assert_not_called()
            self.assertEqual(self.post(self.client, path, {}).status_code, 302)
            self.assertEqual([args.args[0] for args in clear.call_args_list], expected)
            self.assertTrue(all(args.args[1] is self.app.config for args in clear.call_args_list))

    def test_reports_index_purge_failure_after_successful_document_changes(self):
        from retrieval import RetrievalError

        user_id = self.register(self.client)
        for change in ('import', 'delete'):
            with self.subTest(change=change), patch('studio.clear_indexes') as clear:
                clear.side_effect = [RetrievalError('détail interne'), None]
                if change == 'import':
                    response = self.import_document(self.client)
                    (document,) = list_documents(self.database, user_id)
                else:
                    response = self.post(self.client, f'/documents/{document["id"]}/supprimer', {})
                    self.assertEqual(list_documents(self.database, user_id), [])
                self.assertEqual(response.status_code, 302)
                self.assertEqual(clear.call_count, 2)
                page = self.client.get(response.location).get_data(as_text=True)
                self.assertIn('Modification enregistrée', page)
                self.assertIn('nettoyer les index de recherche', page)
                self.assertNotIn('détail interne', page)

    def test_last_document_deletion_purges_private_index_files_immediately(self):
        from langchain_core.embeddings import Embeddings

        from retrieval import search_documents

        class StaticEmbeddings(Embeddings):
            def embed_documents(self, texts):
                return [self.embed_query(text) for text in texts]

            def embed_query(self, text):
                return [1.0, 0.0]

        user_id = self.register(self.client)
        self.assertEqual(self.import_document(self.client).status_code, 302)
        (document,) = list_documents(self.database, user_id)
        with patch(
            'studio.search_documents',
            side_effect=partial(search_documents, embeddings=StaticEmbeddings()),
        ):
            for scope in ('personal', 'all'):
                self.assertEqual(self.generate(self.client, scope=scope).status_code, 302)
            private_indexes = set(self.index_dir.rglob('index.json'))
            self.assertEqual(self.generate(self.client, scope='courses').status_code, 302)

        indexes = set(self.index_dir.rglob('index.json'))
        self.assertEqual(len(indexes), 3)
        self.assertEqual(len(private_indexes), 2)
        response = self.post(self.client, f'/documents/{document["id"]}/supprimer', {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(set(self.index_dir.rglob('index.json')), indexes - private_indexes)

    def test_generated_quiz_grades_on_server_and_stays_out_of_course_statistics(self):
        user_id = self.register(self.client)
        self.import_document(self.client)
        response = self.generate(self.client, kind='quiz')
        generation_id = response.location.rsplit('/', 1)[1]
        material = get_generation(self.database, user_id, generation_id)['material']
        quiz_path = response.location + '/quiz'

        self.assertEqual(self.post(self.client, quiz_path, {'q0': '4'}).status_code, 400)
        self.assertEqual(list_attempts(self.database, user_id), [])
        correct = {
            f'q{index}': question['answer'] for index, question in enumerate(material['questions'])
        }
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
        result = {
            'mode': 'llm',
            'kind': 'quiz',
            'title': '<script>Quatre termes</script>',
            'questions': [
                {
                    'question': 'Quel terme ?',
                    'options': ['un', 'deux', 'trois', 'quatre'],
                    'answer': 2,
                    'explanation': 'CORRIGE_CONFIDENTIEL',
                },
            ],
        }
        with patch(
            'ai_client.urlopen', return_value=io.BytesIO(json.dumps(result).encode())
        ) as transport:
            response = self.generate(self.client, kind='quiz')
        self.assertEqual(response.status_code, 302)
        request = transport.call_args.args[0]
        self.assertEqual(request.full_url, 'http://ai:8001/generate')
        self.assertEqual(request.get_header('Authorization'), 'Bearer service-secret')
        self.assertEqual(transport.call_args.kwargs['timeout'], 55)
        self.assertEqual(json.loads(request.data)['kind'], 'quiz')
        self.generation.assert_not_called()
        for suffix in ('', '/quiz', '/export.json'):
            body = self.client.get(response.location + suffix).get_data(as_text=True)
            self.assertNotIn('CORRIGE_CONFIDENTIEL', body)
            if suffix != '/export.json':
                self.assertNotIn('<script>Quatre termes', body)
                self.assertIn('&lt;script&gt;', body)
        self.assertIn('LLM', self.client.get(response.location).get_data(as_text=True))
        correction = self.post(self.client, response.location + '/quiz', {'q0': '2'})
        self.assertIn(
            'CORRIGE_CONFIDENTIEL', self.client.get(correction.location).get_data(as_text=True)
        )

    def test_service_errors_do_not_fall_back_or_expose_secret(self):
        self.register(self.client)
        self.import_document(self.client)
        self.app.config.update(AI_SERVICE_URL='http://ai:8001', AI_SERVICE_TOKEN='service-secret')
        invalid = [
            b'{"error":"service-secret"}',
            b'x' * (128 * 1024 + 1),
            b'{"mode":"local","kind":"summary","title":"Ancien","content":"Extrait"}',
            b'{"mode":"llm","kind":"summary","title":"Un","title":"Deux","content":"Extrait"}',
        ]
        for data in invalid:
            with (
                self.subTest(length=len(data)),
                patch('ai_client.urlopen', return_value=io.BytesIO(data)),
            ):
                response = self.generate(self.client)
                self.assertEqual(response.status_code, 502)
                self.assertNotIn('service-secret', response.get_data(as_text=True))
        with patch('ai_client.urlopen', side_effect=URLError('service-secret')):
            response = self.generate(self.client)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn('service-secret', response.get_data(as_text=True))
        redirect_body = io.BytesIO(b'placeholder')
        failure = HTTPError('http://ai:8001/generate', 302, 'Found', {}, redirect_body)
        with patch('ai_client.urlopen', side_effect=failure):
            self.assertEqual(self.generate(self.client).status_code, 502)
        self.assertTrue(redirect_body.closed)
        self.assertNotIn('/productions/', self.client.get('/studio').get_data(as_text=True))
        self.generation.assert_not_called()

    def test_service_rejects_invalid_credentials_or_url_before_transport(self):
        self.register(self.client)
        self.import_document(self.client)
        for url, token in [
            ('http://ai:8001', ''),
            ('http://ai:8001', 'secret texte'),
            ('ftp://ai:8001', 'secret'),
            ('https://user:secret@ai:8001', 'secret'),
        ]:
            self.app.config.update(AI_SERVICE_URL=url, AI_SERVICE_TOKEN=token)
            with self.subTest(url=url), patch('ai_client.urlopen') as transport:
                response = self.generate(self.client)
                self.assertEqual(response.status_code, 502)
                self.assertNotIn('secret', response.get_data(as_text=True))
                transport.assert_not_called()
        self.generation.assert_not_called()

    def test_service_input_errors_display_safe_user_feedback(self):
        self.register(self.client)
        self.import_document(self.client)
        self.app.config.update(AI_SERVICE_URL='http://ai:8001', AI_SERVICE_TOKEN='service-secret')
        for status, feedback in [(400, 'Reformulez'), (413, 'taille')]:
            with self.subTest(status=status):
                upstream_body = io.BytesIO(b'{"error":"service-secret"}')
                failure = HTTPError(
                    'http://ai:8001/generate', status, 'service-secret', {}, upstream_body
                )
                with patch('ai_client.urlopen', side_effect=failure):
                    response = self.generate(self.client, kind='quiz')
                self.assertEqual(response.status_code, 400)
                self.assertIn(feedback, response.get_data(as_text=True))
                self.assertNotIn('service-secret', response.get_data(as_text=True))
                self.assertTrue(upstream_body.closed)
