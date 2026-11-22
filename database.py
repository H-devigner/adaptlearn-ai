"""Requêtes SQL simples, compatibles SQLite local et PostgreSQL via DATABASE_URL."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import uuid4


def now():
    return datetime.now(UTC).isoformat(timespec='microseconds')


class Connection:
    def __init__(self, raw, postgres):
        self.raw = raw
        self.postgres = postgres

    def execute(self, sql, parameters=()):
        # Seules nos requêtes fixes utilisent « ? » comme paramètre SQL.
        return self.raw.execute(sql.replace('?', '%s') if self.postgres else sql, parameters)


@contextmanager
def connect(path):
    postgres = str(path).startswith(('postgres://', 'postgresql://'))
    if postgres:
        import psycopg
        from psycopg.rows import dict_row

        raw = psycopg.connect(path, row_factory=dict_row, connect_timeout=10)
    else:
        raw = sqlite3.connect(path, timeout=15)
        raw.row_factory = sqlite3.Row
        raw.execute('PRAGMA foreign_keys = ON')
    try:
        yield Connection(raw, postgres)
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()


def init_database(path):
    # Schéma additif : la table « profile » de la version 0.1 est conservée.
    statements = [
        """CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, created_at TEXT NOT NULL)""",
        """CREATE TABLE IF NOT EXISTS learner_profiles (
            user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL, level TEXT NOT NULL, goal TEXT NOT NULL)""",
        """CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL)""",
        """CREATE TABLE IF NOT EXISTS generations (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            query TEXT NOT NULL, kind TEXT NOT NULL, mode TEXT NOT NULL,
            material_json TEXT NOT NULL, sources_json TEXT NOT NULL, created_at TEXT NOT NULL)""",
        """CREATE TABLE IF NOT EXISTS attempts (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            course_id TEXT, generation_id TEXT REFERENCES generations(id),
            score INTEGER NOT NULL, total INTEGER NOT NULL CHECK(total > 0),
            answers_json TEXT NOT NULL, corrections_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            CHECK ((course_id IS NULL) <> (generation_id IS NULL)),
            CHECK (score >= 0 AND score <= total))""",
        'CREATE INDEX IF NOT EXISTS attempts_user_date ON attempts(user_id, created_at)',
        'CREATE INDEX IF NOT EXISTS documents_user ON documents(user_id)',
        'CREATE INDEX IF NOT EXISTS generations_user ON generations(user_id)',
    ]
    with connect(path) as db:
        for sql in statements:
            db.execute(sql)


def create_user(path, username, password_hash):
    user_id = str(uuid4())
    try:
        with connect(path) as db:
            db.execute(
                'INSERT INTO users VALUES (?, ?, ?, ?)',
                (user_id, username.lower(), password_hash, now()),
            )
    except Exception as error:
        # Ne masquer que les violations d’unicité, pas les erreurs de connexion.
        if isinstance(error, sqlite3.IntegrityError) or getattr(error, 'sqlstate', None) == '23505':
            raise ValueError('Ce nom d’utilisateur est déjà utilisé.') from error
        raise
    return get_user(path, user_id)


def get_user(path, user_id):
    with connect(path) as db:
        row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return dict(row) if row else None


def find_user(path, username):
    with connect(path) as db:
        row = db.execute('SELECT * FROM users WHERE username = ?', (username.lower(),)).fetchone()
        return dict(row) if row else None


def get_profile(path, user_id):
    with connect(path) as db:
        row = db.execute('SELECT * FROM learner_profiles WHERE user_id = ?', (user_id,)).fetchone()
        return dict(row) if row else None


def save_profile(path, user_id, name, level, goal):
    with connect(path) as db:
        db.execute(
            """INSERT INTO learner_profiles VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name, level = excluded.level, goal = excluded.goal""",
            (user_id, name, level, goal),
        )


def save_attempt(path, user_id, course_id, result, answers, generation_id=None):
    if (course_id is None) == (generation_id is None):
        raise ValueError('Une tentative doit correspondre à une seule évaluation.')
    score, total = result['score'], result['total']
    if type(score) is not int or type(total) is not int or not (0 <= score <= total and total > 0):
        raise ValueError('Le résultat de l’évaluation est invalide.')

    attempt_id = str(uuid4())
    with connect(path) as db:
        if generation_id is not None:
            quiz = db.execute(
                "SELECT id FROM generations WHERE id = ? AND user_id = ? AND kind = 'quiz'",
                (generation_id, user_id),
            ).fetchone()
            if quiz is None:
                raise ValueError('Ce quiz est introuvable pour ce compte.')
        db.execute(
            """INSERT INTO attempts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                attempt_id,
                user_id,
                course_id,
                generation_id,
                score,
                total,
                json.dumps(answers),
                json.dumps(result['corrections'], ensure_ascii=False),
                now(),
            ),
        )
    return attempt_id


def list_attempts(path, user_id):
    with connect(path) as db:
        rows = db.execute(
            'SELECT * FROM attempts WHERE user_id = ? ORDER BY created_at DESC, id DESC', (user_id,)
        ).fetchall()
        return [dict(row) for row in rows]


def get_attempt(path, user_id, attempt_id):
    with connect(path) as db:
        row = db.execute(
            'SELECT * FROM attempts WHERE id = ? AND user_id = ?', (attempt_id, user_id)
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result['corrections'] = json.loads(result.pop('corrections_json'))
        result['percentage'] = round(100 * result['score'] / result['total'], 1)
        return result


def add_document(path, user_id, title, content, limit=None):
    document_id = str(uuid4())
    with connect(path) as db:
        if limit is not None:
            # Sérialise la vérification de quota et l’insertion concurrente.
            if db.postgres:
                db.execute('SELECT id FROM users WHERE id = ? FOR UPDATE', (user_id,)).fetchone()
            else:
                db.execute('BEGIN IMMEDIATE')
            count = db.execute(
                'SELECT COUNT(*) AS document_count FROM documents WHERE user_id = ?', (user_id,)
            ).fetchone()['document_count']
            if count >= limit:
                raise ValueError(f'La limite de {limit} documents par compte est atteinte.')
        db.execute(
            'INSERT INTO documents VALUES (?, ?, ?, ?, ?)',
            (document_id, user_id, title, content, now()),
        )
    return document_id


def list_documents(path, user_id):
    with connect(path) as db:
        return [
            dict(row)
            for row in db.execute(
                'SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC', (user_id,)
            ).fetchall()
        ]


def delete_document(path, user_id, document_id):
    with connect(path) as db:
        return (
            db.execute(
                'DELETE FROM documents WHERE id = ? AND user_id = ?', (document_id, user_id)
            ).rowcount
            > 0
        )


def save_generation(path, user_id, query, material, sources):
    generation_id = str(uuid4())
    with connect(path) as db:
        db.execute(
            'INSERT INTO generations VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (
                generation_id,
                user_id,
                query,
                material['kind'],
                material['mode'],
                json.dumps(material, ensure_ascii=False),
                json.dumps(sources, ensure_ascii=False),
                now(),
            ),
        )
    return generation_id


def get_generation(path, user_id, generation_id):
    with connect(path) as db:
        row = db.execute(
            'SELECT * FROM generations WHERE id = ? AND user_id = ?', (generation_id, user_id)
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result['material'] = json.loads(result.pop('material_json'))
        result['sources'] = json.loads(result.pop('sources_json'))
        return result


def list_generations(path, user_id):
    with connect(path) as db:
        return [
            dict(row)
            for row in db.execute(
                """SELECT id, query, kind, mode, created_at FROM generations
               WHERE user_id = ? ORDER BY created_at DESC""",
                (user_id,),
            ).fetchall()
        ]
