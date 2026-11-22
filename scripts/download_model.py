"""Précharge le modèle avant de démarrer le serveur ou une démonstration."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from fastembed import TextEmbedding
from retrieval import DEFAULT_EMBEDDING_MODEL, DEFAULT_MODEL_CACHE_DIR


def main():
    load_dotenv()
    model_name = os.environ.get('EMBEDDING_MODEL', DEFAULT_EMBEDDING_MODEL)
    cache_dir = os.environ.get('EMBEDDING_CACHE_DIR', str(DEFAULT_MODEL_CACHE_DIR))
    TextEmbedding(model_name=model_name, cache_dir=cache_dir, threads=2)
    print('Modèle d’embeddings prêt dans', cache_dir)


if __name__ == '__main__':
    main()
