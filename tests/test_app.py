"""Tests de comportement : HTTP et véritable base SQLite temporaire."""
import tempfile
import unittest
from pathlib import Path

from app import create_app


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.config = {'TESTING': True, 'SECRET_KEY': 'test-only', 'CSRF_ENABLED': False, 'DATABASE': str(Path(self.folder.name) / 'test.sqlite')}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.client.post('/inscription', data={'username': 'sara', 'password': 'Une phrase test 123!'})
        self.profile = {'name': 'Sara', 'level': 'Débutant', 'goal': 'Apprendre Python'}

    def test_pages_accessibles_sans_profil(self):
        for url in ['/', '/profil', '/cours']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertIn('Les variables', self.client.get('/cours').get_data(as_text=True))

    def test_profil_persistant_apres_redemarrage(self):
        response = self.client.post('/profil', data=self.profile)
        self.assertEqual(response.status_code, 302)
        other_client = create_app(self.config).test_client()
        other_client.post('/connexion', data={'username': 'sara', 'password': 'Une phrase test 123!'})
        page = other_client.get('/profil').get_data(as_text=True)
        self.assertIn('Sara', page)
        self.assertIn('Apprendre Python', page)
        self.assertIn('Sara', other_client.get('/').get_data(as_text=True))

    def test_modification_du_profil_unique(self):
        self.client.post('/profil', data=self.profile)
        self.client.post('/profil', data={**self.profile, 'name': 'Amine'})
        page = self.client.get('/profil').get_data(as_text=True)
        self.assertIn('Amine', page)
        self.assertNotIn('value="Sara"', page)

    def test_entrees_invalides_ne_modifient_pas_le_profil(self):
        self.client.post('/profil', data=self.profile)
        for field, value in [('name', '  '), ('name', 'a' * 81),
                             ('level', 'Expert inconnu'), ('goal', ''),
                             ('goal', 'a' * 501), ('name', 'Sara\x00'), ('goal', 'Python\x00')]:
            with self.subTest(field=field, value=value[:20]):
                response = self.client.post('/profil', data={**self.profile, field: value})
                self.assertEqual(response.status_code, 400)
                self.assertIn('Sara', self.client.get('/profil').get_data(as_text=True))
        self.assertEqual(self.client.post('/profil', data={}).status_code, 400)

    def test_texte_utilisateur_echappe(self):
        name = "<script>alert('bonjour')</script>"
        self.client.post('/profil', data={**self.profile, 'name': name})
        page = self.client.get('/').get_data(as_text=True)
        self.assertNotIn(name, page)
        self.assertIn('&lt;script&gt;', page)
        self.assertEqual(self.client.get('/cours').status_code, 200)


if __name__ == '__main__':
    unittest.main()
