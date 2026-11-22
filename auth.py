"""Comptes locaux, sessions signées et protection des formulaires."""
import hmac
import re
import secrets
from functools import wraps

from flask import Blueprint, abort, current_app, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import create_user, find_user, get_user

bp = Blueprint('auth', __name__)
USERNAME_PATTERN = re.compile(r'[a-z0-9_-]{3,40}')
CSRF_TOKEN_PATTERN = re.compile(r'[0-9a-f]{64}')


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped


def init_auth(app):
    @app.before_request
    def load_user_and_check_csrf():
        g.user = get_user(app.config['DATABASE'], session['user_id']) if session.get('user_id') else None
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        if request.method == 'POST' and app.config['CSRF_ENABLED']:
            supplied = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token', '')
            if not CSRF_TOKEN_PATTERN.fullmatch(supplied) or not hmac.compare_digest(session['csrf_token'], supplied):
                abort(400, description='Formulaire expiré ou invalide. Rechargez la page puis réessayez.')

    app.register_blueprint(bp)


def _start_session(user_id):
    session.clear()
    session.permanent = True
    session['user_id'] = user_id


@bp.route('/inscription', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        if not USERNAME_PATTERN.fullmatch(username):
            error = 'Utilisez 3 à 40 lettres sans accents, chiffres, tirets ou traits de soulignement.'
        elif not 10 <= len(password) <= 128:
            error = 'Le mot de passe doit contenir entre 10 et 128 caractères.'
        elif '\x00' in password:
            error = 'Le mot de passe contient un caractère invalide.'
        else:
            try:
                user = create_user(current_app.config['DATABASE'], username,
                                   generate_password_hash(password))
                _start_session(user['id'])
                return redirect(url_for('profile'))
            except ValueError as exception:
                error = str(exception)
    return render_template('auth.html', register=True, error=error), 400 if error else 200


@bp.route('/connexion', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        user = find_user(current_app.config['DATABASE'], username) if USERNAME_PATTERN.fullmatch(username) else None
        if (not user or len(password) > 128 or '\x00' in password
                or not check_password_hash(user['password_hash'], password)):
            error = 'Identifiants incorrects.'
        else:
            _start_session(user['id'])
            return redirect(url_for('home'))
    return render_template('auth.html', register=False, error=error), 400 if error else 200


@bp.post('/deconnexion')
@login_required
def logout():
    session.clear()
    return redirect(url_for('home'))
