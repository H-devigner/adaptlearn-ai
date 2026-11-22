"""Recherche sémantique locale dans les documents du studio."""

import hashlib
import json
import math
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tokenizers import Tokenizer

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
TOKEN_BUDGET = 120
TOKEN_OVERLAP = 24
DEFAULT_EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
DEFAULT_MIN_SCORE = 0.35
INSTANCE_DIR = Path(__file__).resolve().parent / 'instance'
DEFAULT_INDEX_DIR = INSTANCE_DIR / 'rag'
DEFAULT_MODEL_CACHE_DIR = INSTANCE_DIR / 'models'
INDEX_VERSION = 2

_models = {}
_model_lock = Lock()


class RetrievalError(RuntimeError):
    """Le modèle ou l'index sémantique est indisponible."""


class FastEmbedEmbeddings(Embeddings):
    """Adapte les vecteurs FastEmbed à l'interface de LangChain."""

    def __init__(self, model):
        self.model = model
        self.revision = str(model.model._model_dir)
        tokenizer = model.model.tokenizer
        self.token_budget = None
        if tokenizer.truncation:
            self.tokenizer = Tokenizer.from_str(tokenizer.to_str())
            self.tokenizer.no_truncation()
            self.tokenizer.no_padding()
            special_tokens = self.tokenizer.num_special_tokens_to_add(is_pair=False)
            self.token_budget = min(
                TOKEN_BUDGET, tokenizer.truncation['max_length'] - special_tokens
            )
            self.token_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.token_budget,
                chunk_overlap=min(TOKEN_OVERLAP, self.token_budget // 4),
                length_function=self.token_count,
            )

    def token_count(self, text):
        return len(self.tokenizer.encode(text, add_special_tokens=False).ids)

    def split_tokens(self, text):
        if self.token_budget is None or self.token_count(text) <= self.token_budget:
            return [text]
        chunks = self.token_splitter.split_text(text)
        if chunks == [text]:
            midpoint = len(text) // 2
            chunks = [text[:midpoint].strip(), text[midpoint:].strip()]
        return [passage for chunk in chunks for passage in self.split_tokens(chunk)]

    def embed_documents(self, texts):
        try:
            return [vector.tolist() for vector in self.model.passage_embed(texts, batch_size=16)]
        except Exception:  # noqa: BLE001 - errors from the local inference engine
            raise RetrievalError('Le modèle sémantique ne peut pas indexer les extraits.') from None

    def embed_query(self, text):
        try:
            return next(self.model.query_embed(text)).tolist()
        except Exception:  # noqa: BLE001 - errors from the local inference engine
            raise RetrievalError('Le modèle sémantique ne peut pas traiter la question.') from None


def _local_embeddings(model_name, cache_dir):
    key = (model_name, Path(cache_dir).resolve())
    with _model_lock:
        if key not in _models:
            try:
                from fastembed import TextEmbedding

                _models[key] = FastEmbedEmbeddings(
                    TextEmbedding(
                        model_name=model_name,
                        cache_dir=str(key[1]),
                        threads=2,
                    )
                )
            except Exception:  # noqa: BLE001 - download and native model-loading errors
                raise RetrievalError('Impossible de charger le modèle sémantique local.') from None
        return _models[key]


def _write_index(path, data):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            json.dump(data, temporary, ensure_ascii=False)
            temporary.close()
            temporary_path.replace(path)
        finally:
            temporary_path.unlink(missing_ok=True)


def _index_path(namespace, config):
    scope = hashlib.sha256(str(namespace).encode('utf-8')).hexdigest()
    return Path(config.get('RAG_INDEX_DIR', DEFAULT_INDEX_DIR)) / scope / 'index.json'


def clear_indexes(namespace, config=None):
    """Supprime le cache du compte et du périmètre donnés."""
    try:
        _index_path(namespace, config or {}).unlink(missing_ok=True)
    except OSError:
        raise RetrievalError("Impossible de supprimer l'index sémantique local.") from None


def _valid_vectors(vectors, corpus, dimensions):
    if not isinstance(vectors, dict) or not vectors:
        return False
    documents = {doc_id: (title, content) for doc_id, title, content in corpus}
    for key, entry in vectors.items():
        if not isinstance(entry, dict) or entry.get('id') != key:
            return False
        metadata = entry.get('metadata')
        if not isinstance(metadata, dict) or metadata.keys() != {
            'document_id',
            'title',
            'chunk_index',
        }:
            return False
        doc_id = metadata['document_id']
        position = metadata['chunk_index']
        if type(doc_id) not in (int, str) or type(position) is not int or position < 0:
            return False
        title, content = documents.get(doc_id, (None, ''))
        text = entry.get('text')
        valid_text = isinstance(text, str) and 0 < len(text) <= CHUNK_SIZE and text in content
        if metadata['title'] != title or not valid_text:
            return False
        vector = entry.get('vector')
        if (
            not isinstance(vector, list)
            or len(vector) != dimensions
            or not all(type(value) in (int, float) and -1e100 <= value <= 1e100 for value in vector)
        ):
            return False
    return True


def _vector_index(path, fingerprint, corpus, embeddings, dimensions):
    index = InMemoryVectorStore(embeddings)
    try:
        saved = json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError):
        saved = None
    except OSError:
        raise RetrievalError("Impossible de lire l'index sémantique local.") from None

    if (
        isinstance(saved, dict)
        and saved.get('fingerprint') == fingerprint
        and _valid_vectors(saved.get('vectors'), corpus, dimensions)
    ):
        index.store = saved['vectors']
        return index

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = []
    for doc_id, title, content in corpus:
        passages = splitter.split_text(content)
        if isinstance(embeddings, FastEmbedEmbeddings):
            passages = [chunk for passage in passages for chunk in embeddings.split_tokens(passage)]
        chunks.extend(
            Document(
                page_content=chunk,
                metadata={'document_id': doc_id, 'title': title, 'chunk_index': position},
            )
            for position, chunk in enumerate(passages)
        )
    if chunks:
        index.add_documents(chunks)
    try:
        _write_index(path, {'fingerprint': fingerprint, 'vectors': index.store})
    except OSError:
        raise RetrievalError("Impossible d'enregistrer l'index sémantique local.") from None
    return index


def search_documents(
    documents, query, limit=4, *, config=None, namespace='public', embeddings=None
):
    """Classe les passages du corpus autorisé par similarité cosinus."""
    if not isinstance(query, str) or not query.strip() or limit <= 0:
        return []
    corpus = [
        (doc['id'], doc['title'], doc['content']) for doc in documents if doc['content'].strip()
    ]
    if not corpus:
        clear_indexes(namespace, config)
        return []

    config = config or {}
    model_name = config.get('EMBEDDING_MODEL', DEFAULT_EMBEDDING_MODEL)
    model_cache_dir = Path(config.get('EMBEDDING_CACHE_DIR', DEFAULT_MODEL_CACHE_DIR)).resolve()
    minimum = float(config.get('RAG_MIN_SCORE', DEFAULT_MIN_SCORE))
    if not 0.0 <= minimum <= 1.0:
        raise ValueError('RAG_MIN_SCORE doit être compris entre 0 et 1.')

    if embeddings is None:
        embeddings = _local_embeddings(model_name, model_cache_dir)
    embedding_type = type(embeddings)
    payload = [
        INDEX_VERSION,
        model_name,
        str(model_cache_dir),
        getattr(embeddings, 'revision', None),
        embedding_type.__module__,
        embedding_type.__qualname__,
        CHUNK_SIZE,
        CHUNK_OVERLAP,
        getattr(embeddings, 'token_budget', None),
        TOKEN_OVERLAP,
        corpus,
    ]
    fingerprint = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False).encode('utf-8')
    ).hexdigest()
    path = _index_path(namespace, config)
    query_vector = embeddings.embed_query(query.strip())
    index = _vector_index(path, fingerprint, corpus, embeddings, len(query_vector))
    return [
        {**document.metadata, 'text': document.page_content, 'score': min(1.0, float(score))}
        for document, score in index.similarity_search_with_score_by_vector(query_vector, k=limit)
        if math.isfinite(score) and score > 0.0 and score >= minimum
    ]
