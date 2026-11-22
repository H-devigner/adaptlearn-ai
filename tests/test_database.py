"""Invariants des tentatives, avec une véritable base SQLite temporaire."""

import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from database import (
    add_document,
    connect,
    create_user,
    get_attempt,
    init_database,
    list_attempts,
    list_documents,
    save_attempt,
    save_generation,
)


class AttemptTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.database = str(Path(folder.name) / 'test.sqlite')
        init_database(self.database)
        self.user_id = create_user(self.database, 'sara', 'test-hash')['id']
        self.other_id = create_user(self.database, 'amine', 'test-hash')['id']
        self.result = {'score': 1, 'total': 2, 'corrections': []}
        self.quiz_id = self.generation(self.user_id, 'quiz')

    def generation(self, user_id, kind):
        return save_generation(
            self.database, user_id, 'Python', {'kind': kind, 'mode': 'local'}, []
        )

    def test_saves_editorial_and_generated_attempts_for_owner(self):
        editorial = save_attempt(self.database, self.user_id, 'variables', self.result, [1, 0])
        generated = save_attempt(
            self.database, self.user_id, None, self.result, [1, 0], self.quiz_id
        )
        self.assertEqual(
            get_attempt(self.database, self.user_id, editorial)['course_id'], 'variables'
        )
        self.assertEqual(
            get_attempt(self.database, self.user_id, generated)['generation_id'], self.quiz_id
        )
        self.assertIsNone(get_attempt(self.database, self.other_id, generated))

    def test_attempt_requires_exactly_one_assessment(self):
        for course_id, generation_id in [(None, None), ('variables', self.quiz_id)]:
            with self.subTest(course_id=course_id, generation_id=generation_id):
                with self.assertRaises(ValueError):
                    save_attempt(
                        self.database, self.user_id, course_id, self.result, [], generation_id
                    )
        self.assertEqual(list_attempts(self.database, self.user_id), [])

    def test_generated_attempt_requires_owned_quiz(self):
        other_quiz = self.generation(self.other_id, 'quiz')
        own_summary = self.generation(self.user_id, 'summary')
        for generation_id in [other_quiz, own_summary, 'absent']:
            with self.subTest(generation_id=generation_id):
                with self.assertRaises(ValueError):
                    save_attempt(self.database, self.user_id, None, self.result, [], generation_id)
        self.assertEqual(list_attempts(self.database, self.user_id), [])

    def test_attempt_rejects_invalid_score_or_total(self):
        for score, total in [(-1, 2), (3, 2), (0, 0), (0, -1), (True, 2), (0, 2.0)]:
            with self.subTest(score=score, total=total), self.assertRaises(ValueError):
                result = {**self.result, 'score': score, 'total': total}
                save_attempt(self.database, self.user_id, 'variables', result, [])
        self.assertEqual(list_attempts(self.database, self.user_id), [])

    def test_new_schema_enforces_exclusive_assessment(self):
        for course_id, generation_id in [(None, None), ('variables', self.quiz_id)]:
            with self.subTest(course_id=course_id, generation_id=generation_id):
                with self.assertRaises(sqlite3.IntegrityError), connect(self.database) as db:
                    db.execute(
                        'INSERT INTO attempts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (
                            'attempt',
                            self.user_id,
                            course_id,
                            generation_id,
                            1,
                            2,
                            '[]',
                            '[]',
                            '2026-11-22',
                        ),
                    )


class DocumentLimitTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.database = str(Path(folder.name) / 'test.sqlite')
        init_database(self.database)
        self.user_id = create_user(self.database, 'sara', 'test-hash')['id']

    def test_document_limit_is_per_account(self):
        other_id = create_user(self.database, 'amine', 'test-hash')['id']
        add_document(self.database, self.user_id, 'Introduction', 'Python', limit=1)
        with self.assertRaises(ValueError):
            add_document(self.database, self.user_id, 'Autre document', 'Python', limit=1)
        add_document(self.database, other_id, 'Introduction', 'Python', limit=1)
        self.assertEqual(len(list_documents(self.database, self.user_id)), 1)
        self.assertEqual(len(list_documents(self.database, other_id)), 1)

    def test_concurrent_uploads_respect_document_limit(self):
        ready = Barrier(2)

        def import_document(title):
            ready.wait(timeout=5)
            try:
                return add_document(self.database, self.user_id, title, 'Python', limit=1)
            except ValueError:
                return None

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(import_document, ['Introduction', 'Variables']))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(len(list_documents(self.database, self.user_id)), 1)
