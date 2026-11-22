"""Service HTTP facultatif pour la génération pédagogique."""

import hmac
import os

from flask import Flask, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

from generation import (
    DEFAULT_LLM_BASE_URL,
    DEFAULT_LLM_TIMEOUT,
    FORMATS,
    MAX_QUERY_LENGTH,
    GenerationError,
    generate_material,
    parse_strict_json,
    valid_text,
)
from retrieval import CHUNK_SIZE


REQUEST_LIMIT = 200 * 1024


def _valid_source(source):
    if not isinstance(source, dict) or source.keys() != {'document_id', 'title', 'text', 'chunk_index', 'score'}:
        return False
    document_id = source['document_id']
    score = source['score']
    return (
        ((type(document_id) is int and document_id > 0) or valid_text(document_id, 120))
        and valid_text(source['title'], 500)
        and valid_text(source['text'], CHUNK_SIZE)
        and type(source['chunk_index']) is int
        and source['chunk_index'] >= 0
        and type(score) in (int, float)
        and 0 < score <= 1
    )


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        AI_SERVICE_TOKEN=os.environ.get('AI_SERVICE_TOKEN'),
        AI_MODE=os.environ.get('AI_MODE', 'local'),
        LLM_BASE_URL=os.environ.get('LLM_BASE_URL', DEFAULT_LLM_BASE_URL),
        LLM_API_KEY=os.environ.get('LLM_API_KEY'),
        LLM_MODEL=os.environ.get('LLM_MODEL'),
        LLM_TIMEOUT=os.environ.get('LLM_TIMEOUT', DEFAULT_LLM_TIMEOUT),
        MAX_CONTENT_LENGTH=REQUEST_LIMIT,
    )
    if test_config is not None:
        app.config.update(test_config)
    token = app.config['AI_SERVICE_TOKEN']
    if not isinstance(token, str) or not token or any(char.isspace() for char in token):
        raise RuntimeError('Définissez AI_SERVICE_TOKEN avec une valeur non vide et sans espace.')
    token_bytes = token.encode('utf-8')

    @app.get('/health')
    def health():
        return jsonify(status='ok')

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(_error):
        return jsonify(error='La requête dépasse 200 Kio.'), 413

    @app.post('/generate')
    def generate():
        auth = request.headers.get('Authorization', '').split()
        if len(auth) != 2 or auth[0].lower() != 'bearer' or not hmac.compare_digest(auth[1].encode('utf-8'), token_bytes):
            return jsonify(error='Jeton du service IA absent ou invalide.'), 401, {'WWW-Authenticate': 'Bearer'}
        body = request.get_data()
        try:
            data = parse_strict_json(body) if request.is_json else None
        except (RecursionError, ValueError):
            return jsonify(error='Corps JSON invalide.'), 400
        if not isinstance(data, dict) or data.keys() != {'kind', 'query', 'sources'}:
            return jsonify(error='Fournissez un objet JSON contenant kind, query et sources.'), 400
        kind, query, sources = data['kind'], data['query'], data['sources']
        if not isinstance(kind, str) or kind not in FORMATS:
            return jsonify(error='Format de support inconnu.'), 400
        if not valid_text(query, MAX_QUERY_LENGTH):
            return jsonify(error=f'Saisissez une requête de 1 à {MAX_QUERY_LENGTH} caractères.'), 400
        if not isinstance(sources, list) or not 1 <= len(sources) <= 16 or not all(map(_valid_source, sources)):
            return jsonify(error='Fournissez de 1 à 16 extraits de recherche valides.'), 400
        try:
            return jsonify(generate_material(kind, query, sources, app.config))
        except ValueError as error:
            return jsonify(error=str(error)), 400
        except GenerationError as error:
            return jsonify(error=str(error)), 502

    return app
