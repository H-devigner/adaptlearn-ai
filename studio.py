"""Imports privés, recherche documentaire et supports pédagogiques sauvegardés."""

import http.client
import json
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request

from flask import Blueprint, abort, current_app, g, jsonify, redirect, render_template, request, url_for
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from auth import login_required
from courses import COURSES
from database import (
    add_document, delete_document as remove_document, get_generation, list_documents,
    list_generations, save_attempt, save_generation,
)
from generation import (
    MAX_QUERY_LENGTH, GenerationError, generate_material, parse_strict_json, urlopen, valid_text, validate_material,
)
from pedagogy import grade_quiz
from retrieval import search_documents


bp = Blueprint('studio', __name__)
FORMATS = {'summary': 'Résumé', 'flashcards': 'Fiches de révision', 'quiz': 'Quiz'}
SCOPES = {'all': 'Toutes les sources', 'personal': 'Mes documents', 'courses': 'Leçons Python'}
MAX_IMPORT_BYTES = 1024 * 1024
MAX_DOCUMENT_LENGTH = 50_000
MAX_TITLE_LENGTH = 500
MAX_DOCUMENTS = 30
MAX_SERVICE_RESPONSE_BYTES = 128 * 1024


def _checked_text(text, limit, message):
    if not valid_text(text, limit):
        raise ValueError(message)
    return text.strip()


def _pdf_text(payload):
    if not payload.startswith(b'%PDF-'):
        raise ValueError('Ce fichier ne contient pas de PDF lisible.')
    pages = []
    total = 0
    try:
        reader = PdfReader(BytesIO(payload), strict=True)
        encrypted = reader.is_encrypted
        if not encrypted:
            for page in reader.pages:
                content = (page.extract_text() or '').strip()
                if content:
                    total += len(content) + bool(pages)
                    if total > MAX_DOCUMENT_LENGTH:
                        break
                    pages.append(content)
    except (PyPdfError, OSError, ValueError, RecursionError, TypeError, KeyError, IndexError, OverflowError):
        raise ValueError('Ce fichier ne contient pas de PDF lisible.') from None
    if encrypted:
        raise ValueError('Retirez le mot de passe du PDF avant de l’importer.')
    if total > MAX_DOCUMENT_LENGTH:
        raise ValueError('Le texte du document dépasse 50 000 caractères.')
    if not pages:
        raise ValueError('Ce PDF ne contient pas de texte extractible. Utilisez un PDF textuel ou collez le texte.')
    return '\n'.join(pages)


def _import_text(content, upload):
    if upload and upload.filename:
        if content.strip():
            raise ValueError('Collez du texte ou choisissez un fichier. Utilisez une seule méthode à la fois.')
        payload = upload.stream.read(MAX_IMPORT_BYTES + 1)
        if len(payload) > MAX_IMPORT_BYTES:
            abort(413)
        extension = Path(upload.filename).suffix.lower()
        if extension == '.pdf':
            content = _pdf_text(payload)
        elif extension in ('.txt', '.md'):
            try:
                content = payload.decode('utf-8-sig')
            except UnicodeDecodeError:
                raise ValueError('Le fichier texte doit être encodé en UTF-8.') from None
        else:
            raise ValueError('Importez un fichier .txt, .md ou .pdf.')
    return _checked_text(content, MAX_DOCUMENT_LENGTH, 'Fournissez 1 à 50 000 caractères de texte valide, sans caractère nul.')


def _service_material(kind, query, sources, config):
    address = config['AI_SERVICE_URL']
    token = config['AI_SERVICE_TOKEN']
    if not isinstance(token, str) or not token or any(char.isspace() for char in token):
        raise GenerationError('Le jeton du service IA est absent ou invalide.')
    try:
        base = urlsplit(address)
        if base.scheme not in ('http', 'https') or not base.hostname or base.username or base.password or base.query or base.fragment:
            raise ValueError('URL de service invalide.')
        http_request = Request(
            address.rstrip('/') + '/generate',
            data=json.dumps({'kind': kind, 'query': query, 'sources': sources}, ensure_ascii=False).encode('utf-8'),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            method='POST',
        )
        with urlopen(http_request, timeout=55) as remote:
            body = remote.read(MAX_SERVICE_RESPONSE_BYTES + 1)
    except HTTPError as error:
        error.close()
        raise GenerationError('Le service IA a refusé la demande.') from None
    except (OSError, TypeError, ValueError, http.client.HTTPException):
        raise GenerationError('Impossible de joindre le service IA ou délai dépassé.') from None
    try:
        if len(body) > MAX_SERVICE_RESPONSE_BYTES:
            raise ValueError('Réponse trop volumineuse.')
        return validate_material(parse_strict_json(body.decode('utf-8')), kind)
    except (ValueError, RecursionError):
        raise GenerationError('Le service IA a renvoyé un support invalide.') from None


def _owned_generation(generation_id):
    record = get_generation(current_app.config['DATABASE'], g.user['id'], generation_id)
    if record is None:
        abort(404)
    return record


def _public_material(material):
    if material['kind'] != 'quiz':
        return material
    questions = [{'question': item['question'], 'options': item['options']} for item in material['questions']]
    return {**material, 'questions': questions}


@bp.route('/studio', methods=['GET', 'POST'])
@login_required
def index():
    config = current_app.config
    database = config['DATABASE']
    user_id = g.user['id']
    error = None
    status = 200
    kind, query, scope = 'summary', '', 'all'
    if request.method == 'POST':
        kind = request.form.get('kind', '')
        query = request.form.get('query', '')
        scope = request.form.get('scope', 'all')
        try:
            if kind not in FORMATS or scope not in SCOPES:
                raise ValueError('Choisissez un format et un périmètre de recherche proposés.')
            query = _checked_text(query, MAX_QUERY_LENGTH, 'Saisissez une requête valide de 1 à 1 000 caractères.')
            documents = list_documents(database, user_id) if scope != 'courses' else []
            if scope != 'personal':
                documents.extend({'id': 'course:' + course['id'], 'title': course['title'], 'content': course['content']}
                                 for course in COURSES)
            sources = search_documents(documents, query)
            if not sources:
                raise ValueError('Aucun extrait pertinent trouvé. Reformulez la requête ou choisissez d’autres sources.')
            if config['AI_SERVICE_URL']:
                support = _service_material(kind, query, sources, config)
            else:
                support = generate_material(kind, query, sources, config)
        except ValueError as exception:
            error, status = str(exception), 400
        except GenerationError as exception:
            error, status = str(exception), 502
        else:
            identifier = save_generation(database, user_id, query, support, sources)
            return redirect(url_for('studio.material', generation_id=identifier))
    return render_template('studio.html', formats=FORMATS, scopes=SCOPES, kind=kind, query=query[:MAX_QUERY_LENGTH],
                           scope=scope, error=error, history=list_generations(database, user_id)), status


@bp.route('/documents', methods=['GET', 'POST'])
@login_required
def documents():
    database = current_app.config['DATABASE']
    user_id = g.user['id']
    error = None
    title, content = '', ''
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        try:
            title = _checked_text(title, MAX_TITLE_LENGTH, 'Saisissez un titre valide de 1 à 500 caractères.')
            text = _import_text(content, request.files.get('file'))
            add_document(database, user_id, title, text, limit=MAX_DOCUMENTS)
        except ValueError as exception:
            error = str(exception)
        else:
            return redirect(url_for('studio.documents'))
    return render_template('documents.html', documents=list_documents(database, user_id), max_documents=MAX_DOCUMENTS,
                           title=title[:MAX_TITLE_LENGTH], content=content[:MAX_DOCUMENT_LENGTH], error=error), 400 if error else 200


@bp.post('/documents/<document_id>/supprimer')
@login_required
def delete_document(document_id):
    if not remove_document(current_app.config['DATABASE'], g.user['id'], document_id):
        abort(404)
    return redirect(url_for('studio.documents'))


@bp.get('/productions/<generation_id>')
@login_required
def material(generation_id):
    record = _owned_generation(generation_id)
    record['material'] = _public_material(record['material'])
    return render_template('material.html', production=record, format_name=FORMATS[record['kind']])


@bp.get('/productions/<generation_id>/export.json')
@login_required
def download(generation_id):
    record = _owned_generation(generation_id)
    response = jsonify(id=record['id'], query=record['query'], created_at=record['created_at'],
                       material=_public_material(record['material']), sources=record['sources'])
    response.headers.set('Content-Disposition', 'attachment', filename='production-' + record['id'] + '.json')
    return response


@bp.route('/productions/<generation_id>/quiz', methods=['GET', 'POST'])
@login_required
def quiz(generation_id):
    record = _owned_generation(generation_id)
    if record['kind'] != 'quiz':
        abort(404)
    support = record['material']
    error = None
    if request.method == 'POST':
        answers = []
        for index in range(len(support['questions'])):
            values = request.form.getlist(f'q{index}')
            answers.append(values[0] if len(values) == 1 else '')
        try:
            result = grade_quiz(support['questions'], answers)
        except ValueError as exception:
            error = str(exception)
        else:
            attempt_id = save_attempt(current_app.config['DATABASE'], g.user['id'], None, result, answers,
                                      generation_id=generation_id)
            return redirect(url_for('learning.result', attempt_id=attempt_id))
    return render_template('quiz.html', title=support['title'], questions=_public_material(support)['questions'],
                           error=error, generated=True), 400 if error else 200
