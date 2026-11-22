"""Point d'entrée : routes web et validation du formulaire apprenant."""
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

from courses import COURSES, LEVELS
from database import get_profile, init_database, save_profile


def create_app(test_config=None):
    app = Flask(__name__)
    app.config['DATABASE'] = str(Path(app.instance_path) / 'adaptlearn.sqlite')
    if test_config:
        app.config.update(test_config)
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    init_database(app.config['DATABASE'])

    @app.get('/')
    def home():
        return render_template('home.html', profile=get_profile(app.config['DATABASE']),
                               course_count=len(COURSES))

    @app.route('/profil', methods=['GET', 'POST'])
    def profile():
        values = get_profile(app.config['DATABASE']) or {}
        errors = []
        if request.method == 'POST':
            values = {key: request.form.get(key, '').strip()
                      for key in ('name', 'level', 'goal')}
            if not 1 <= len(values['name']) <= 80:
                errors.append('Le prénom doit contenir entre 1 et 80 caractères.')
            if values['level'] not in LEVELS:
                errors.append('Choisissez un niveau proposé dans la liste.')
            if not 1 <= len(values['goal']) <= 500:
                errors.append('L’objectif doit contenir entre 1 et 500 caractères.')
            if not errors:
                save_profile(app.config['DATABASE'], **values)
                return redirect(url_for('profile', saved='1'))
        return render_template('profile.html', values=values, levels=LEVELS,
                               errors=errors, saved=request.args.get('saved') == '1'), 400 if errors else 200

    @app.get('/cours')
    def courses():
        return render_template('courses.html', courses=COURSES)

    return app
