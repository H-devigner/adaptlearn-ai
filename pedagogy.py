"""Correction, parcours et statistiques calculés à partir des tentatives."""

import re
from unicodedata import normalize

MASTERY_PERCENTAGE = 70.0
ANSWER_INDICES = ('0', '1', '2', '3')
GOAL_STOP_WORDS = {
    'apprendre',
    'avec',
    'dans',
    'depuis',
    'des',
    'étudier',
    'les',
    'mon',
    'par',
    'pour',
    'que',
    'sur',
    'tout',
    'une',
}


def _percentage(score, total):
    return score * 100 / total if total else 0.0


def grade_quiz(questions, answers):
    """Corrige chaque réponse dans l’ordre et rejette les indices invalides."""
    if len(answers) != len(questions):
        raise ValueError('Répondez à chaque question du quiz.')

    corrections = []
    for question, selected in zip(questions, answers):
        if isinstance(selected, str) and selected in ANSWER_INDICES:
            selected = int(selected)
        if type(selected) is not int or selected not in range(4):
            raise ValueError('Choisissez une des quatre réponses proposées.')
        corrections.append(
            {
                'question': question['question'],
                'selected': selected,
                'answer': question['answer'],
                'explanation': question['explanation'],
                'correct': selected == question['answer'],
            }
        )

    score = sum(correction['correct'] for correction in corrections)
    total = len(questions)
    return {
        'score': score,
        'total': total,
        'percentage': _percentage(score, total),
        'corrections': corrections,
    }


def _attempt_history(attempts):
    """Renvoie les tentatives et leurs scores, de la plus récente à la plus ancienne."""
    recent_attempts = sorted(attempts, key=lambda attempt: attempt['created_at'], reverse=True)
    return [
        (attempt, _percentage(attempt['score'], attempt['total'])) for attempt in recent_attempts
    ]


def build_path(courses, attempts, level):
    """Choisit la première leçon accessible restant à maîtriser."""
    latest = {}
    for attempt, percentage in _attempt_history(attempts):
        latest.setdefault(attempt['course_id'], percentage)

    mastered = {
        course_id for course_id, percentage in latest.items() if percentage >= MASTERY_PERCENTAGE
    }
    titles = {course['id']: course['title'] for course in courses}
    path = []
    next_found = False
    for course in courses:
        course_id = course['id']
        percentage = latest.get(course_id)
        missing = [
            titles.get(prerequisite, prerequisite)
            for prerequisite in course['prerequisites']
            if prerequisite not in mastered
        ]
        if course_id in mastered:
            status = 'mastered'
            reason = f'Dernier score de {percentage:g} %, seuil de maîtrise atteint.'
        elif missing:
            status = 'locked'
            reason = f'À maîtriser d’abord : {", ".join(missing)}.'
        else:
            if percentage is not None:
                status = 'review'
                reason = (
                    f'Dernier score de {percentage:g} %. '
                    f'Révisez la leçon pour atteindre {MASTERY_PERCENTAGE:g} %.'
                )
            elif not next_found:
                status = 'next'
                reason = 'C’est la prochaine leçon de votre parcours.'
            else:
                status = 'available'
                reason = 'Les prérequis de cette leçon sont maîtrisés.'
            if course['level'] == level:
                reason += ' Elle correspond à votre niveau déclaré.'
            next_found = True
        path.append(
            {'course': course, 'status': status, 'reason': reason, 'percentage': percentage}
        )
    return path


def _keywords(value):
    words = re.findall(r'[^\W\d_]{3,}', value.casefold())
    terms = set()
    for word in words:
        if word not in GOAL_STOP_WORDS:
            letters = ''.join(
                character for character in normalize('NFKD', word) if character.isalpha()
            )
            terms.add(letters.removesuffix('s') if len(letters) > 4 else letters)
    return terms


def recommend_resources(courses, attempts, level, goal):
    """Classe les leçons à revoir puis celles à découvrir, selon le profil."""
    goal_words = _keywords(goal)
    status_priority = {'review': 0, 'next': 1, 'available': 2, 'locked': 3}
    recommendations = []
    for entry in build_path(courses, attempts, level):
        course = entry['course']
        status = entry['status']
        if status == 'mastered':
            continue
        same_level = course['level'] == level
        course_words = _keywords(
            ' '.join([course['title'], course['description'], *course['topics']])
        )
        related = bool(goal_words & course_words)
        if status == 'locked' and not (same_level or related):
            continue
        reason = entry['reason']
        if status == 'locked' and same_level:
            reason += ' Cette leçon correspond à votre niveau déclaré.'
        if related:
            reason += ' Son thème rejoint votre objectif.'
        priority = (status_priority[status], not same_level, not related)
        recommendations.append((priority, {'course': course, 'reason': reason}))

    recommendations.sort(key=lambda item: item[0])
    return [item for _, item in recommendations]


def learning_stats(courses, attempts):
    """Calcule les statistiques des évaluations et une série chronologique."""
    history = _attempt_history(attempts)
    scores_by_course = {}
    for attempt, percentage in history:
        scores_by_course.setdefault(attempt['course_id'], []).append(percentage)

    by_course = []
    mastered_count = 0
    for course in courses:
        scores = scores_by_course.get(course['id'], [])
        last_percentage = scores[0] if scores else None
        if last_percentage is not None and last_percentage >= MASTERY_PERCENTAGE:
            mastered_count += 1
        by_course.append(
            {
                'course_id': course['id'],
                'title': course['title'],
                'attempt_count': len(scores),
                'last_percentage': last_percentage,
                'best_percentage': max(scores, default=None),
            }
        )

    return {
        'attempt_count': len(history),
        'average_percentage': sum(percentage for _, percentage in history) / len(history)
        if history
        else 0.0,
        'mastered_count': mastered_count,
        'completion_percentage': _percentage(mastered_count, len(courses)),
        'by_course': by_course,
        'timeline': [
            {'date': attempt['created_at'], 'percentage': percentage}
            for attempt, percentage in reversed(history)
        ],
    }
