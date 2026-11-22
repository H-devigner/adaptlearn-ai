"""Contrats des leçons, des quiz et du suivi pédagogique."""

import unittest

from courses import COURSES, LEVELS


def attempt(course_id, score, total, date):
    return {'course_id': course_id, 'score': score, 'total': total, 'created_at': date}


class CatalogueTests(unittest.TestCase):
    def test_cinq_lecons_et_quiz_editoriaux(self):
        from courses import get_course

        self.assertEqual(
            [course['id'] for course in COURSES],
            [
                'python-debut',
                'variables',
                'conditions-boucles',
                'fonctions-collections',
                'generateurs',
            ],
        )
        previous_ids = set()
        for course in COURSES:
            with self.subTest(course=course['id']):
                self.assertIs(get_course(course['id']), course)
                self.assertIn(course['level'], LEVELS)
                self.assertTrue(course['description'])
                self.assertGreater(len(course['content']), 200)
                self.assertTrue(set(course['prerequisites']) <= previous_ids)
                self.assertGreaterEqual(len(course['questions']), 3)
                for question in course['questions']:
                    self.assertEqual(len(set(question['options'])), 4)
                    self.assertTrue(all(isinstance(option, str) for option in question['options']))
                    self.assertIn(question['answer'], range(4))
                    self.assertTrue(question['question'])
                    self.assertTrue(question['explanation'])
                previous_ids.add(course['id'])
        self.assertIsNone(get_course('cours-inconnu'))


class QuizTests(unittest.TestCase):
    questions = [
        {
            'question': 'Question A',
            'options': ['a', 'b', 'c', 'd'],
            'answer': 1,
            'explanation': 'Explication A',
        },
        {
            'question': 'Question B',
            'options': ['e', 'f', 'g', 'h'],
            'answer': 3,
            'explanation': 'Explication B',
        },
    ]

    def test_score_et_corrections(self):
        from pedagogy import grade_quiz

        result = grade_quiz(self.questions, ['1', 2])
        self.assertEqual(
            result,
            {
                'score': 1,
                'total': 2,
                'percentage': 50.0,
                'corrections': [
                    {
                        'question': 'Question A',
                        'selected': 1,
                        'answer': 1,
                        'correct': True,
                        'explanation': 'Explication A',
                    },
                    {
                        'question': 'Question B',
                        'selected': 2,
                        'answer': 3,
                        'correct': False,
                        'explanation': 'Explication B',
                    },
                ],
            },
        )
        self.assertIsInstance(result['percentage'], float)

    def test_nombre_de_reponses_invalide(self):
        from pedagogy import grade_quiz

        for answers in ([1], [1, 3, 0]):
            with self.subTest(answers=answers), self.assertRaises(ValueError):
                grade_quiz(self.questions, answers)

    def test_indices_invalides(self):
        from pedagogy import grade_quiz

        for invalid in (-1, 4, '4', '', '01', ' 1 ', '1.0', 1.0, True, None):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                grade_quiz(self.questions, [invalid, 3])

    def test_quiz_vide(self):
        from pedagogy import grade_quiz

        self.assertEqual(
            grade_quiz([], []),
            {
                'score': 0,
                'total': 0,
                'percentage': 0.0,
                'corrections': [],
            },
        )


class ParcoursTests(unittest.TestCase):
    def test_niveau_avance_commence_par_les_bases(self):
        from pedagogy import build_path

        path = build_path(COURSES, [], 'Avancé')
        self.assertEqual([entry['status'] for entry in path], ['next'] + ['locked'] * 4)
        self.assertIs(path[0]['course'], COURSES[0])
        self.assertIsNone(path[0]['percentage'])
        self.assertIn(COURSES[0]['title'], path[1]['reason'])

    def test_derniere_tentative_et_seuil_conditionnent_le_parcours(self):
        from pedagogy import build_path

        attempts = [
            attempt('variables', 8, 10, '2026-11-19'),
            attempt('python-debut', 10, 10, '2026-11-18'),
            attempt('variables', 6, 10, '2026-11-20'),
            attempt('python-debut', 7, 10, '2026-11-22'),
        ]
        path = build_path(COURSES, attempts, 'Débutant')
        self.assertEqual(
            [entry['status'] for entry in path],
            [
                'mastered',
                'review',
                'locked',
                'locked',
                'locked',
            ],
        )
        self.assertEqual([entry['percentage'] for entry in path[:2]], [70.0, 60.0])
        self.assertIn('60', path[1]['reason'])
        attempts.append(attempt('variables', 9, 10, '2026-11-23'))
        path = build_path(COURSES, attempts, 'Débutant')
        self.assertEqual(path[2]['status'], 'next')

    def test_une_seule_prochaine_lecon_parmi_les_lecons_accessibles(self):
        from pedagogy import build_path

        courses = [COURSES[0], {**COURSES[1], 'prerequisites': []}]
        path = build_path(courses, [], 'Débutant')
        self.assertEqual([entry['status'] for entry in path], ['next', 'available'])

    def test_recommandations_expliquent_revision_niveau_et_objectif(self):
        from pedagogy import recommend_resources

        attempts = [attempt('python-debut', 2, 3, '2026-11-22')]
        suggestions = recommend_resources(
            COURSES, attempts, 'Intermédiaire', 'Étudier les generateurs'
        )
        ids = [item['course']['id'] for item in suggestions]
        self.assertEqual(
            ids, ['python-debut', 'conditions-boucles', 'fonctions-collections', 'generateurs']
        )
        self.assertIn('niveau', suggestions[1]['reason'])
        self.assertIn('objectif', suggestions[-1]['reason'])

    def test_prochaine_lecon_prioritaire_sur_le_niveau(self):
        from pedagogy import recommend_resources

        suggestions = recommend_resources(COURSES, [], 'Avancé', 'générateurs')
        self.assertEqual(
            [item['course']['id'] for item in suggestions], ['python-debut', 'generateurs']
        )
        self.assertIn('maîtriser', suggestions[-1]['reason'])


class StatistiquesTests(unittest.TestCase):
    def test_aucune_tentative(self):
        from pedagogy import learning_stats

        stats = learning_stats(COURSES, [])
        self.assertEqual(stats['attempt_count'], 0)
        self.assertEqual(stats['average_percentage'], 0.0)
        self.assertEqual(stats['mastered_count'], 0)
        self.assertEqual(stats['completion_percentage'], 0.0)
        self.assertEqual(stats['timeline'], [])
        self.assertEqual(
            stats['by_course'][0],
            {
                'course_id': 'python-debut',
                'title': COURSES[0]['title'],
                'attempt_count': 0,
                'last_percentage': None,
                'best_percentage': None,
            },
        )

    def test_statistiques_agregent_les_tentatives_en_ordre_chronologique(self):
        from pedagogy import learning_stats

        attempts = [
            attempt('variables', 3, 4, '2026-11-22T12:00:00'),
            attempt('python-debut', 9, 10, '2026-11-20T12:00:00'),
            attempt('python-debut', 1, 2, '2026-11-21T12:00:00'),
        ]
        stats = learning_stats(COURSES, attempts)
        self.assertEqual(stats['attempt_count'], 3)
        self.assertAlmostEqual(stats['average_percentage'], (90.0 + 50.0 + 75.0) / 3)
        self.assertEqual(stats['mastered_count'], 1)
        self.assertEqual(stats['completion_percentage'], 20.0)
        self.assertEqual(
            stats['by_course'][0],
            {
                'course_id': 'python-debut',
                'title': COURSES[0]['title'],
                'attempt_count': 2,
                'last_percentage': 50.0,
                'best_percentage': 90.0,
            },
        )
        self.assertEqual(
            stats['timeline'],
            [
                {'date': '2026-11-20T12:00:00', 'percentage': 90.0},
                {'date': '2026-11-21T12:00:00', 'percentage': 50.0},
                {'date': '2026-11-22T12:00:00', 'percentage': 75.0},
            ],
        )
