import os
import tempfile
import unittest
from pathlib import Path

from retrieval import DEFAULT_MODEL_CACHE_DIR, search_documents

DOCUMENTS = [
    {
        'id': 1,
        'title': 'Physique',
        'content': 'Les cellules photovoltaïques transforment le rayonnement solaire en courant continu.',
    },
    {
        'id': 2,
        'title': 'Biologie',
        'content': 'Les végétaux utilisent la photosynthèse pour fabriquer du glucose à partir du dioxyde de carbone.',
    },
    {
        'id': 3,
        'title': 'Histoire',
        'content': 'La prise de la Bastille en 1789 marque le début de la Révolution française.',
    },
]
QUESTIONS = [
    ('Comment obtenir de l’électricité grâce à la lumière du soleil ?', 1),
    ('Par quel mécanisme les plantes produisent-elles des sucres ?', 2),
]


@unittest.skipUnless(
    os.environ.get('RUN_SEMANTIC_TESTS') == '1', 'Modèle multilingue activé sur demande'
)
class MultilingualRetrievalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.config = {
            'RAG_INDEX_DIR': Path(temporary.name) / 'index',
            'EMBEDDING_CACHE_DIR': os.environ.get('EMBEDDING_CACHE_DIR', DEFAULT_MODEL_CACHE_DIR),
        }

    def test_french_paraphrases_retrieve_relevant_passages(self):
        for query, expected_id in QUESTIONS:
            with self.subTest(query=query):
                matches = search_documents(DOCUMENTS, query, limit=1, config=self.config)
                self.assertEqual([match['document_id'] for match in matches], [expected_id])

    def test_unrelated_question_returns_no_sources(self):
        query = 'Combien de planètes orbitent autour de Jupiter ?'
        self.assertEqual(search_documents(DOCUMENTS, query, config=self.config), [])

    def test_retrieves_end_of_long_passage_and_reuses_index_afterward(self):
        prefix = (
            'Les rituels politiques occupaient une place importante dans les villes médiévales. '
            * 13
        )
        note = (
            'Les cellules photovoltaïques transforment le rayonnement solaire en courant continu.'
        )
        document = {'id': 4, 'title': 'Notes', 'content': prefix + '\n\n' + note}
        self.assertLessEqual(len(document['content']), 1200)
        query = QUESTIONS[0][0]
        matches = search_documents([document], query, limit=1, config=self.config)
        self.assertEqual(len(matches), 1)
        self.assertGreater(matches[0]['chunk_index'], 0)
        self.assertIn(note, matches[0]['text'])
        self.assertEqual(search_documents([document], query, limit=1, config=self.config), matches)
        self.assertEqual(search_documents([], query, limit=1, config=self.config), [])
        self.assertFalse(list(self.config['RAG_INDEX_DIR'].rglob('*.json')))
