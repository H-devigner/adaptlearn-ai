"""Vérification explicite avec de vrais embeddings et le LLM configuré dans .env."""

import json
import os
import sys
from pathlib import Path

# Permet : python scripts/verify_rag.py depuis la racine du projet.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from generation import generate_material
from retrieval import search_documents

DOCUMENTS = [
    {
        'id': 'solaire',
        'title': 'Production électrique solaire',
        'content': 'Les panneaux photovoltaïques transforment le rayonnement solaire en courant continu. '
        'Un onduleur transforme le courant continu en courant alternatif utilisable dans une maison. '
        'Une batterie permet de conserver une partie de cette énergie pour plus tard.',
    },
    {
        'id': 'botanique',
        'title': 'Nutrition des végétaux',
        'content': 'Les plantes fabriquent du glucose par photosynthèse. '
        'Elles absorbent du dioxyde de carbone et rejettent de l’oxygène.',
    },
]
QUERY = 'Comment convertir l’électricité des capteurs du soleil pour alimenter un logement ?'


def main():
    load_dotenv()
    config = dict(os.environ)
    sources = search_documents(DOCUMENTS, QUERY, limit=2, config=config, namespace='verification')
    if not sources or sources[0]['document_id'] != 'solaire':
        raise RuntimeError('Le passage attendu n’a pas été retrouvé.')
    print('Recherche sémantique : passage solaire retrouvé.', flush=True)
    materials = {}
    for kind in ('summary', 'flashcards', 'quiz'):
        materials[kind] = generate_material(kind, QUERY, sources, config)
        print(f'Génération réelle {kind} : valide.', flush=True)
    output = Path('instance/rag-verification.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                'query': QUERY,
                'sources': sources,
                'materials': materials,
                'llm_model': config.get('LLM_MODEL'),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    print(f'Résultat consultable : {output}')


if __name__ == '__main__':
    main()
