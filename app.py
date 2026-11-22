"""Configuration de Flask et pages principales de la plateforme."""

import os
import secrets
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, g, jsonify, redirect, render_template, request, url_for

from auth import init_auth, login_required
from courses import COURSES, LEVELS
from database import connect, get_profile, init_database, save_profile


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get('DATABASE_URL')
        or os.environ.get('DATABASE')
        or str(Path(app.instance_path) / 'adaptlearn.sqlite'),
        SECRET_KEY=os.environ.get('SECRET_KEY', ''),
        APP_ENV=os.environ.get('APP_ENV', 'development'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', 'false').lower() == 'true',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
        CSRF_ENABLED=True,
        AI_MODE=os.environ.get('AI_MODE', 'llm'),
        AI_SERVICE_URL=os.environ.get('AI_SERVICE_URL', ''),
        AI_SERVICE_TOKEN=os.environ.get('AI_SERVICE_TOKEN', ''),
        LLM_BASE_URL=os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1'),
        LLM_API_KEY=os.environ.get('LLM_API_KEY', ''),
        LLM_MODEL=os.environ.get('LLM_MODEL', ''),
        LLM_TIMEOUT=os.environ.get('LLM_TIMEOUT', '45'),
        EMBEDDING_MODEL=os.environ.get(
            'EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        ),
        EMBEDDING_CACHE_DIR=os.environ.get('EMBEDDING_CACHE_DIR')
        or str(Path(app.instance_path) / 'models'),
        RAG_INDEX_DIR=os.environ.get('RAG_INDEX_DIR') or str(Path(app.instance_path) / 'rag'),
        RAG_MIN_SCORE=os.environ.get('RAG_MIN_SCORE', '0.35'),
    )
    if test_config:
        app.config.update(test_config)
    if not app.config['SECRET_KEY']:
        if app.config['APP_ENV'] == 'production':
            raise ValueError('SECRET_KEY est obligatoire en production.')
        # Une clé locale persistante évite de perdre les sessions au redémarrage.
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
        secret_file = Path(app.instance_path) / 'secret.key'
        if not secret_file.exists():
            try:
                descriptor = os.open(secret_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, 'w') as file:
                    file.write(secrets.token_hex(32))
            except FileExistsError:
                pass
        app.config['SECRET_KEY'] = secret_file.read_text().strip()
    if not str(app.config['DATABASE']).startswith(('postgres://', 'postgresql://')):
        Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    init_database(app.config['DATABASE'])
    init_auth(app)

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        if g.get('user'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/health')
    def health():
        try:
            with connect(app.config['DATABASE']) as db:
                db.execute('SELECT 1').fetchone()
            return jsonify(status='ok')
        except Exception:
            return jsonify(status='unavailable'), 503

    @app.get('/')
    def home():
        profile = get_profile(app.config['DATABASE'], g.user['id']) if g.user else None
        return render_template('home.html', profile=profile, course_count=len(COURSES))

    @app.route('/profil', methods=['GET', 'POST'])
    @login_required
    def profile():
        values = get_profile(app.config['DATABASE'], g.user['id']) or {}
        errors = []
        if request.method == 'POST':
            values = {key: request.form.get(key, '').strip() for key in ('name', 'level', 'goal')}
            if not 1 <= len(values['name']) <= 80 or '\x00' in values['name']:
                errors.append('Le prénom doit contenir entre 1 et 80 caractères.')
            if values['level'] not in LEVELS:
                errors.append('Choisissez un niveau proposé dans la liste.')
            if not 1 <= len(values['goal']) <= 500 or '\x00' in values['goal']:
                errors.append('L’objectif doit contenir entre 1 et 500 caractères.')
            if not errors:
                save_profile(app.config['DATABASE'], g.user['id'], **values)
                return redirect(url_for('profile', saved='1'))
        return render_template(
            'profile.html',
            values=values,
            levels=LEVELS,
            errors=errors,
            saved=request.args.get('saved') == '1',
        ), 400 if errors else 200

    @app.get('/cours')
    def courses():
        return render_template('courses.html', courses=COURSES)

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def user_error(error):
        messages = {
            400: 'La demande est invalide. Rechargez la page et vérifiez les champs.',
            404: 'Cette page ou cette ressource est introuvable.',
            413: 'Le fichier est trop volumineux : limitez l’import à 1 Mo.',
        }
        return render_template('error.html', message=messages[error.code]), error.code

    from learning import bp as learning_bp

    app.register_blueprint(learning_bp)
    from studio import bp as studio_bp

    app.register_blueprint(studio_bp)
    return app
