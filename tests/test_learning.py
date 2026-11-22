import tempfile
import unittest
from pathlib import Path

from app import create_app
from courses import COURSES
from database import list_attempts


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / 'db.sqlite')
        self.app = create_app(
            {
                'TESTING': True,
                'SECRET_KEY': 'test-only',
                'CSRF_ENABLED': False,
                'DATABASE': self.path,
            }
        )
        self.client = self.app.test_client()
        self.client.post(
            '/inscription', data={'username': 'sara', 'password': 'Une phrase test 123!'}
        )
        self.client.post('/profil', data={'name': 'Sara', 'level': 'Débutant', 'goal': 'Python'})

    def test_quiz_result_path_and_real_analytics(self):
        course = COURSES[0]
        response = self.client.post(
            '/cours/' + course['id'] + '/quiz',
            data={'q' + str(i): str(q['answer']) for i, q in enumerate(course['questions'])},
        )
        self.assertEqual(response.status_code, 302)
        result = self.client.get(response.location)
        self.assertIn('100', result.get_data(as_text=True))
        self.assertIn('Maîtrisé', self.client.get('/parcours').get_data(as_text=True))
        self.assertIn('100', self.client.get('/progression').get_data(as_text=True))
        self.assertIn('Les variables', self.client.get('/ressources').get_data(as_text=True))

    def test_invalid_answers_do_not_save_attempt(self):
        response = self.client.post('/cours/python-debut/quiz', data={'q0': '99'})
        self.assertEqual(response.status_code, 400)
        with self.client.session_transaction() as session:
            user_id = session['user_id']
        self.assertEqual(list_attempts(self.path, user_id), [])

    def test_multiple_answers_for_one_question_are_rejected(self):
        data = {'q' + str(i): '0' for i in range(len(COURSES[0]['questions']))}
        data['q0'] = ['0', '1']
        response = self.client.post('/cours/python-debut/quiz', data=data)
        self.assertEqual(response.status_code, 400)
        with self.client.session_transaction() as session:
            self.assertEqual(list_attempts(self.path, session['user_id']), [])

    def test_results_belong_to_one_account(self):
        course = COURSES[0]
        response = self.client.post(
            '/cours/python-debut/quiz',
            data={'q' + str(i): '0' for i in range(len(course['questions']))},
        )
        other = self.app.test_client()
        other.post('/inscription', data={'username': 'amine', 'password': 'Une phrase test 123!'})
        self.assertEqual(other.get(response.location).status_code, 404)

    def test_invalid_result_identifiers_return_not_found(self):
        for identifier in ['invalide', 'test%00null']:
            self.assertEqual(self.client.get('/resultats/' + identifier).status_code, 404)

    def test_lesson_and_empty_dashboard(self):
        for url in [
            '/cours/python-debut',
            '/cours/python-debut/quiz',
            '/parcours',
            '/ressources',
            '/progression',
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(self.client.get('/cours/inconnu').status_code, 404)
