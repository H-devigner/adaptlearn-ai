import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import create_app


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = {'TESTING': True, 'SECRET_KEY': 'test-only', 'CSRF_ENABLED': False,
                       'DATABASE': str(Path(self.temp.name) / 'db.sqlite')}
        self.app = create_app(self.config)
        self.client = self.app.test_client()

    def register(self, client, username='sara'):
        return client.post('/inscription', data={'username': username, 'password': 'Une phrase test 123!'})

    def test_authentication_and_private_profile(self):
        self.assertEqual(self.client.get('/profil').status_code, 302)
        self.assertEqual(self.register(self.client).status_code, 302)
        self.assertEqual(self.client.get('/profil').status_code, 200)
        self.client.post('/profil', data={'name': 'Sara', 'level': 'Débutant', 'goal': 'Python'})
        other = self.app.test_client()
        self.register(other, 'amine')
        self.assertNotIn('value="Sara"', other.get('/profil').get_data(as_text=True))
        self.client.post('/deconnexion')
        self.assertEqual(self.client.get('/profil').status_code, 302)
        self.assertEqual(self.client.post('/connexion', data={'username': 'sara', 'password': 'wrong'}).status_code, 400)
        self.assertEqual(self.client.post('/connexion', data={'username': 'sara', 'password': 'Une phrase test 123!'}).status_code, 302)
        self.assertIn('value="Sara"', self.client.get('/profil').get_data(as_text=True))

    def test_validation_and_unique_username(self):
        self.assertEqual(self.register(self.client).status_code, 302)
        self.client.post('/deconnexion')
        self.assertEqual(self.register(self.client).status_code, 400)
        self.assertEqual(self.client.post('/inscription', data={'username': 'ab', 'password': 'short'}).status_code, 400)

    def test_csrf_rejects_post_without_matching_token(self):
        app = create_app({**self.config, 'CSRF_ENABLED': True})
        client = app.test_client()
        client.get('/inscription')
        self.assertEqual(self.register(client).status_code, 400)
        with client.session_transaction() as session:
            token = session['csrf_token']
        response = client.post('/inscription', data={'username': 'lina', 'password': 'Une phrase test 123!', 'csrf_token': token})
        self.assertEqual(response.status_code, 302)

    def test_csrf_rejects_malformed_token_as_bad_request(self):
        app = create_app({**self.config, 'CSRF_ENABLED': True})
        client = app.test_client()
        client.get('/inscription')
        response = client.post('/inscription', data={'csrf_token': 'clé invalide'})
        self.assertEqual(response.status_code, 400)

    def test_registration_rejects_null_in_credentials(self):
        for username, password in [('sa\x00ra', 'Une phrase test 123!'),
                                   ('sara', 'Une phrase\x00 test 123!')]:
            with self.subTest(username=username):
                response = self.client.post('/inscription', data={'username': username, 'password': password})
                self.assertEqual(response.status_code, 400)

    def test_authenticated_session_cookie_expires_in_eight_hours(self):
        username = 'sara'
        password = 'Une phrase test 123!'
        for endpoint in ('/inscription', '/connexion'):
            with self.subTest(endpoint=endpoint):
                result = self.client.post(endpoint, data={'username': username, 'password': password})
                self.assertEqual(result.status_code, 302)
                with self.client.session_transaction() as session:
                    self.assertTrue(session.permanent)
                expiration = self.client.get_cookie('session').expires
                self.assertIsNotNone(expiration)
                remaining = expiration - datetime.now(timezone.utc)
                self.assertLess(abs(remaining - timedelta(hours=8)), timedelta(seconds=10))
                self.client.post('/deconnexion')

    def test_production_requires_stable_secret(self):
        with self.assertRaises(ValueError):
            create_app({**self.config, 'APP_ENV': 'production', 'SECRET_KEY': ''})
