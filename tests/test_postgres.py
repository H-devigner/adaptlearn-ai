"""Test d’intégration optionnel : base dédiée fournie par TEST_DATABASE_URL."""

import os
import unittest
from uuid import uuid4

from database import (
    add_document,
    connect,
    create_user,
    get_attempt,
    get_generation,
    get_profile,
    init_database,
    list_documents,
    save_attempt,
    save_generation,
    save_profile,
)


@unittest.skipUnless(
    os.environ.get('TEST_DATABASE_URL'), 'TEST_DATABASE_URL absent : PostgreSQL non exécuté'
)
class PostgresTests(unittest.TestCase):
    def test_full_storage_cycle_and_isolation(self):
        path = os.environ['TEST_DATABASE_URL']
        init_database(path)
        user = create_user(path, 'test_' + uuid4().hex[:20], 'not-a-real-password-hash')
        other = create_user(path, 'test_' + uuid4().hex[:20], 'not-a-real-password-hash')
        try:
            save_profile(path, user['id'], 'Élève', 'Débutant', 'Comprendre les variables')
            self.assertEqual(get_profile(path, user['id'])['name'], 'Élève')
            self.assertIsNone(get_profile(path, other['id']))
            add_document(path, user['id'], 'Cours test', 'Une variable désigne une valeur.')
            self.assertEqual(len(list_documents(path, user['id'])), 1)
            self.assertEqual(list_documents(path, other['id']), [])
            material = {'kind': 'quiz', 'mode': 'local', 'title': 'Quiz test', 'questions': []}
            generation = save_generation(path, user['id'], 'Variables', material, [])
            self.assertIsNone(get_generation(path, other['id'], generation))
            result = {'score': 1, 'total': 1, 'corrections': []}
            attempt = save_attempt(path, user['id'], None, result, ['0'], generation)
            self.assertEqual(get_attempt(path, user['id'], attempt)['percentage'], 100)
            self.assertIsNone(get_attempt(path, other['id'], attempt))
        finally:
            with connect(path) as db:
                db.execute('DELETE FROM attempts WHERE user_id = ?', (user['id'],))
                db.execute('DELETE FROM users WHERE id = ?', (user['id'],))
                db.execute('DELETE FROM users WHERE id = ?', (other['id'],))
