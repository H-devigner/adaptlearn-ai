"""Imports privés, recherche documentaire et supports pédagogiques sauvegardés."""

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from ai_client import generate_service_material
from auth import login_required
from courses import COURSES
from database import (
    add_document,
    get_generation,
    list_documents,
    list_generations,
    save_attempt,
    save_generation,
)
from database import (
    delete_document as remove_document,
)
from document_import import MAX_DOCUMENT_LENGTH, import_document_text
from generation import MAX_QUERY_LENGTH, GenerationError, generate_material, valid_text
from pedagogy import grade_quiz
from retrieval import RetrievalError, clear_indexes, search_documents

bp = Blueprint('studio', __name__)
FORMATS = {'summary': 'Résumé', 'flashcards': 'Fiches de révision', 'quiz': 'Quiz'}
SCOPES = {'all': 'Toutes les sources', 'personal': 'Mes documents', 'courses': 'Leçons Python'}
MAX_TITLE_LENGTH = 500
MAX_DOCUMENTS = 30


def _checked_text(text, limit, message):
    if not valid_text(text, limit):
        raise ValueError(message)
    return text.strip()


def _clear_document_indexes(user_id, config):
    failed = False
    for scope in ('all', 'personal'):
        try:
            clear_indexes(f'{user_id}:{scope}', config)
        except RetrievalError:
            failed = True
    if failed:
        flash('Modification enregistrée. Impossible de nettoyer les index de recherche.', 'error')


def _owned_generation(generation_id):
    record = get_generation(current_app.config['DATABASE'], g.user['id'], str(generation_id))
    if record is None:
        abort(404)
    return record


def _public_material(material):
    if material['kind'] != 'quiz':
        return material
    questions = [
        {'question': item['question'], 'options': item['options']} for item in material['questions']
    ]
    return {**material, 'questions': questions}


@bp.route('/studio', methods=['GET', 'POST'])
@login_required
def index():
    config = current_app.config
    database = config['DATABASE']
    user_id = g.user['id']
    uses_ai_service = bool(config.get('AI_SERVICE_URL'))
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
            query = _checked_text(
                query, MAX_QUERY_LENGTH, 'Saisissez une requête valide de 1 à 1 000 caractères.'
            )
            documents = list_documents(database, user_id) if scope != 'courses' else []
            if scope != 'personal':
                documents.extend(
                    {
                        'id': 'course:' + course['id'],
                        'title': course['title'],
                        'content': course['content'],
                    }
                    for course in COURSES
                )
            sources = search_documents(
                documents, query, config=config, namespace=f'{user_id}:{scope}'
            )
            if not sources:
                raise ValueError(
                    'Aucun extrait pertinent trouvé. Reformulez la requête ou choisissez d’autres sources.'
                )
            if uses_ai_service:
                support = generate_service_material(kind, query, sources, config)
            else:
                support = generate_material(kind, query, sources, config)
        except ValueError as exception:
            error, status = str(exception), 400
        except (RetrievalError, GenerationError) as exception:
            error, status = str(exception), 502
        else:
            material = {**support, 'retrieval_method': 'semantic'}
            identifier = save_generation(database, user_id, query, material, sources)
            return redirect(url_for('studio.material', generation_id=identifier))
    return render_template(
        'studio.html',
        formats=FORMATS,
        scopes=SCOPES,
        kind=kind,
        query=query[:MAX_QUERY_LENGTH],
        scope=scope,
        error=error,
        history=list_generations(database, user_id),
        embedding_configured=bool(config.get('EMBEDDING_MODEL')),
        uses_ai_service=uses_ai_service,
        generation_configured=bool(config.get('LLM_MODEL') and config.get('LLM_API_KEY')),
    ), status


@bp.route('/documents', methods=['GET', 'POST'])
@login_required
def documents():
    config = current_app.config
    database = config['DATABASE']
    user_id = g.user['id']
    error = None
    title, content = '', ''
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        try:
            title = _checked_text(
                title, MAX_TITLE_LENGTH, 'Saisissez un titre valide de 1 à 500 caractères.'
            )
            text = import_document_text(content, request.files.get('file'))
            add_document(database, user_id, title, text, limit=MAX_DOCUMENTS)
        except ValueError as exception:
            error = str(exception)
        else:
            _clear_document_indexes(user_id, config)
            return redirect(url_for('studio.documents'))
    return render_template(
        'documents.html',
        documents=list_documents(database, user_id),
        max_documents=MAX_DOCUMENTS,
        title=title[:MAX_TITLE_LENGTH],
        content=content[:MAX_DOCUMENT_LENGTH],
        error=error,
    ), 400 if error else 200


@bp.post('/documents/<uuid:document_id>/supprimer')
@login_required
def delete_document(document_id):
    config = current_app.config
    user_id = g.user['id']
    if not remove_document(config['DATABASE'], user_id, str(document_id)):
        abort(404)
    _clear_document_indexes(user_id, config)
    return redirect(url_for('studio.documents'))


@bp.get('/productions/<uuid:generation_id>')
@login_required
def material(generation_id):
    record = _owned_generation(generation_id)
    record['material'] = _public_material(record['material'])
    return render_template('material.html', production=record, format_name=FORMATS[record['kind']])


@bp.get('/productions/<uuid:generation_id>/export.json')
@login_required
def download(generation_id):
    record = _owned_generation(generation_id)
    response = jsonify(
        id=record['id'],
        query=record['query'],
        created_at=record['created_at'],
        material=_public_material(record['material']),
        sources=record['sources'],
    )
    response.headers.set(
        'Content-Disposition', 'attachment', filename='production-' + record['id'] + '.json'
    )
    return response


@bp.route('/productions/<uuid:generation_id>/quiz', methods=['GET', 'POST'])
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
            attempt_id = save_attempt(
                current_app.config['DATABASE'],
                g.user['id'],
                None,
                result,
                answers,
                generation_id=record['id'],
            )
            return redirect(url_for('learning.result', attempt_id=attempt_id))
    return render_template(
        'quiz.html',
        title=support['title'],
        questions=_public_material(support)['questions'],
        error=error,
        generated=True,
    ), 400 if error else 200
