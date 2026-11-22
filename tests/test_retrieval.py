import itertools
import json
import stat
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import retrieval

DOCUMENTS = [
    {
        'id': 1,
        'title': 'Physique',
        'content': 'Les cellules photovoltaïques produisent du courant.',
    },
    {'id': 2, 'title': 'Cuisine', 'content': 'La levure fait gonfler la pâte.'},
    {'id': 3, 'title': 'Mécanique', 'content': 'Une turbine entraîne un alternateur.'},
]
QUERY = 'Comment convertir la lumière en électricité ?'


class EmptyRetrievalTests(unittest.TestCase):
    def test_empty_query_accepts_index_configuration_without_using_model(self):
        self.assertEqual(
            retrieval.search_documents(DOCUMENTS, '', config={}, namespace='42_all'), []
        )


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.index_dir = Path(temporary.name) / 'index'
        self.config = {'RAG_INDEX_DIR': self.index_dir}
        self.embeddings = self.make_embeddings()

    def make_embeddings(self):
        from langchain_core.embeddings import Embeddings

        class DeterministicEmbeddings(Embeddings):
            embedded_corpora = 0

            def embed_documents(self, texts):
                self.embedded_corpora += 1
                return [self.embed_query(text) for text in texts]

            def embed_query(self, text):
                if text == QUERY or text == DOCUMENTS[0]['content']:
                    return [1.0, 0.0]
                if text == DOCUMENTS[1]['content']:
                    return [0.0, 1.0]
                if text == DOCUMENTS[2]['content']:
                    return [0.6, 0.8]
                return [-1.0, 0.0]

        return DeterministicEmbeddings()

    def search(self, documents=DOCUMENTS, query=QUERY, **options):
        options.setdefault('embeddings', self.embeddings)
        return retrieval.search_documents(documents, query, config=self.config, **options)

    def test_ranks_by_vector_similarity_instead_of_shared_words(self):
        matches = self.search()
        self.assertEqual([match['document_id'] for match in matches], [1, 3])
        self.assertEqual(
            matches[0],
            {
                'document_id': 1,
                'title': 'Physique',
                'text': DOCUMENTS[0]['content'],
                'chunk_index': 0,
                'score': 1.0,
            },
        )
        self.assertAlmostEqual(matches[1]['score'], 0.6)
        self.assertEqual(self.search(limit=1), matches[:1])

    def test_threshold_excludes_weak_matches(self):
        self.config['RAG_MIN_SCORE'] = 0.7
        self.assertEqual([match['document_id'] for match in self.search()], [1])
        self.assertEqual(self.search(query='Sujet sans rapport'), [])

    def test_zero_threshold_still_excludes_nonpositive_scores(self):
        self.config['RAG_MIN_SCORE'] = 0.0
        self.assertEqual([match['document_id'] for match in self.search()], [1, 3])

    def test_empty_search_needs_no_embeddings(self):
        self.assertEqual(self.search(query=' \t'), [])
        self.assertEqual(self.search(limit=0), [])
        self.assertEqual(self.search(documents=[]), [])
        self.assertEqual(self.embeddings.embedded_corpora, 0)

    def test_persisted_index_is_private_json_and_reuses_vectors(self):
        results = self.search(namespace='42_all')
        (index,) = self.index_dir.rglob('*.json')
        self.assertTrue(json.loads(index.read_text()))
        self.assertEqual(stat.S_IMODE(index.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(index.parent.stat().st_mode), 0o700)
        new_embeddings = self.make_embeddings()
        self.assertEqual(self.search(namespace='42_all', embeddings=new_embeddings), results)
        self.assertEqual(new_embeddings.embedded_corpora, 0)

    def test_corpus_title_content_and_removal_invalidate_index(self):
        self.search(namespace='42_all')
        revised = [dict(DOCUMENTS[0], title='Optique'), DOCUMENTS[2]]
        self.assertEqual(self.search(revised, namespace='42_all')[0]['title'], 'Optique')
        revised[0]['content'] = 'Un tout autre contenu.'
        self.assertEqual(
            [match['document_id'] for match in self.search(revised, namespace='42_all')], [3]
        )
        self.assertEqual(self.search(revised[:1], namespace='42_all'), [])
        self.assertEqual(self.embeddings.embedded_corpora, 4)

    def test_model_change_invalidates_index(self):
        self.search()
        self.config['EMBEDDING_MODEL'] = 'other/model'
        self.search()
        self.config['EMBEDDING_CACHE_DIR'] = self.index_dir.parent / 'other-model-cache'
        self.search()
        self.assertEqual(self.embeddings.embedded_corpora, 3)

    def test_index_with_matching_fingerprint_and_invalid_vectors_is_rebuilt(self):
        results = self.search()
        (index,) = self.index_dir.rglob('*.json')
        fingerprint = json.loads(index.read_text())['fingerprint']
        for vectors in (None, {'broken': {'vector': [0.3, 'bad']}}):
            with self.subTest(vectors=vectors):
                cached = {'fingerprint': fingerprint}
                if vectors is not None:
                    cached['vectors'] = vectors
                index.write_text(json.dumps(cached))
                self.assertEqual(self.search(), results)
        self.assertEqual(self.embeddings.embedded_corpora, 3)

    def test_empty_corpus_discards_only_its_index(self):
        self.search(namespace='42_all')
        self.search(namespace='77_all')
        self.assertEqual(self.search([], namespace='42_all'), [])
        self.assertEqual(len(list(self.index_dir.rglob('*.json'))), 1)

    def test_indexes_are_separate_for_accounts_and_scopes(self):
        for namespace, expected_docs in (
            ('42_all', DOCUMENTS),
            ('77_all', DOCUMENTS[1:]),
            ('42_document-3', DOCUMENTS[2:]),
        ):
            with self.subTest(namespace=namespace):
                matches = self.search(expected_docs, namespace=namespace)
                self.assertTrue(
                    {match['document_id'] for match in matches}
                    <= {document['id'] for document in expected_docs}
                )
        self.assertEqual(len(list(self.index_dir.rglob('*.json'))), 3)
        retrieval.clear_indexes('42_all', self.config)
        self.assertEqual(len(list(self.index_dir.rglob('*.json'))), 2)

    def test_recursive_chunks_are_bounded_and_share_context(self):
        content = ' '.join(f'phrase{index}' for index in range(250))
        self.config['RAG_MIN_SCORE'] = 0.0
        matches = self.search(
            [{'id': 1, 'title': 'Texte', 'content': content}], query='Sujet sans rapport'
        )
        ordered = sorted(matches, key=lambda match: match['chunk_index'])
        self.assertGreater(len(ordered), 1)
        self.assertEqual([match['chunk_index'] for match in ordered], list(range(len(ordered))))
        for match in ordered:
            self.assertLessEqual(len(match['text']), 1200)
            self.assertIn(match['text'], content)
        for first, second in itertools.pairwise(ordered):
            self.assertTrue(set(first['text'].split()) & set(second['text'].split()))

    def test_concurrent_requests_keep_their_own_corpus(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self.search, DOCUMENTS[:1])
            second = pool.submit(self.search, DOCUMENTS[2:])
            self.assertEqual([match['document_id'] for match in first.result()], [1])
            self.assertEqual([match['document_id'] for match in second.result()], [3])
        (index,) = (file for file in self.index_dir.rglob('*') if file.is_file())
        self.assertTrue(json.loads(index.read_text()))

    def test_reports_model_failure_without_exposing_internal_error(self):
        def unavailable_model(**options):
            raise RuntimeError('private-token')

        with (
            patch.dict(
                sys.modules, {'fastembed': SimpleNamespace(TextEmbedding=unavailable_model)}
            ),
            self.assertRaisesRegex(RuntimeError, 'modèle') as failure,
        ):
            self.search(embeddings=None)
        self.assertIsInstance(failure.exception, retrieval.RetrievalError)
        self.assertNotIn('private-token', str(failure.exception))

    def test_reports_unwritable_cache(self):
        self.index_dir.write_text('Un fichier empêche de créer le dossier.')
        with self.assertRaisesRegex(RuntimeError, 'index') as failure:
            self.search()
        self.assertIsInstance(failure.exception, retrieval.RetrievalError)
