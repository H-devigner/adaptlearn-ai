"""Leçons, évaluations, parcours et tableau de progression."""
from flask import Blueprint, abort, current_app, g, redirect, render_template, request, url_for

from auth import login_required
from courses import COURSES, get_course
from database import get_attempt, get_profile, list_attempts, save_attempt
from pedagogy import build_path, grade_quiz, learning_stats, recommend_resources

bp = Blueprint('learning', __name__)


def learner_context():
    path = current_app.config['DATABASE']
    profile = get_profile(path, g.user['id'])
    # Les quiz générés sont des entraînements distincts du référentiel éditorial.
    attempts = [a for a in list_attempts(path, g.user['id']) if a['course_id']]
    return profile, attempts


@bp.get('/cours/<course_id>')
def lesson(course_id):
    course = get_course(course_id)
    if not course:
        abort(404)
    return render_template('lesson.html', course=course)


@bp.route('/cours/<course_id>/quiz', methods=['GET', 'POST'])
@login_required
def quiz(course_id):
    course = get_course(course_id)
    if not course:
        abort(404)
    error = None
    if request.method == 'POST':
        answers = []
        for index in range(len(course['questions'])):
            values = request.form.getlist(f'q{index}')
            answers.append(values[0] if len(values) == 1 else '')
        try:
            result = grade_quiz(course['questions'], answers)
        except ValueError as exception:
            error = str(exception)
        else:
            attempt_id = save_attempt(current_app.config['DATABASE'], g.user['id'], course_id,
                                      result, answers)
            return redirect(url_for('learning.result', attempt_id=attempt_id))
    # Ne pas inclure le corrigé dans le HTML avant l’envoi.
    questions = [{'question': q['question'], 'options': q['options']} for q in course['questions']]
    return render_template('quiz.html', title=course['title'], questions=questions,
                           error=error, generated=False), 400 if error else 200


@bp.get('/resultats/<uuid:attempt_id>')
@login_required
def result(attempt_id):
    attempt = get_attempt(current_app.config['DATABASE'], g.user['id'], str(attempt_id))
    if not attempt:
        abort(404)
    course = get_course(attempt['course_id']) if attempt['course_id'] else None
    return render_template('result.html', attempt=attempt, course=course)


@bp.get('/parcours')
@login_required
def path():
    profile, attempts = learner_context()
    entries = build_path(COURSES, attempts, profile['level'] if profile else 'Débutant')
    return render_template('path.html', entries=entries, profile=profile)


@bp.get('/ressources')
@login_required
def resources():
    profile, attempts = learner_context()
    recommendations = recommend_resources(COURSES, attempts,
        profile['level'] if profile else 'Débutant', profile['goal'] if profile else '')
    return render_template('resources.html', recommendations=recommendations)


@bp.get('/progression')
@login_required
def progress():
    profile, attempts = learner_context()
    stats = learning_stats(COURSES, attempts)
    all_attempts = list_attempts(current_app.config['DATABASE'], g.user['id'])
    titles = {c['id']: c['title'] for c in COURSES}
    return render_template('progress.html', stats=stats, attempts=all_attempts, titles=titles)
