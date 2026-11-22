"""Stockage du profil unique de démonstration, sans serveur SQL externe."""
import sqlite3
from contextlib import closing


def init_database(path):
    with closing(sqlite3.connect(path)) as connection:
        connection.execute('''CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT NOT NULL,
            level TEXT NOT NULL,
            goal TEXT NOT NULL
        )''')
        connection.commit()


def get_profile(path):
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute('SELECT * FROM profile WHERE id = 1').fetchone()
        return dict(row) if row else None


def save_profile(path, name, level, goal):
    # Les paramètres SQL gardent les saisies séparées de la requête.
    with closing(sqlite3.connect(path)) as connection:
        connection.execute('''INSERT INTO profile (id, name, level, goal)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name, level = excluded.level, goal = excluded.goal
        ''', (name, level, goal))
        connection.commit()
