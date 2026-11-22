"""Recherche lexicale dans les documents du studio."""

import math
import re
import unicodedata
from collections import Counter


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 180
WORD_PATTERN = re.compile(r'[^\W_]+')
STOP_WORDS = frozenset('''
    a afin ainsi alors apres au aucun aux avec avoir c car ce ceci cela ces cet cette chaque comme
    comment dans de des donc du d elle elles en encore est et etre fait faire il ils j je l la le
    les leur leurs lui m ma mais me meme mes moi mon n ne nos notre nous on ont ou par pas pendant
    plus pour pourquoi qu quand que quel quelle quelles quels qui quoi s sa sans se ses si soi son
    sont sous sur t ta te tes toi ton tous tout toute toutes tu un une vos votre vous y
'''.split())


def tokens(text):
    """Normalise les mots, y compris les pluriels simples terminés par s."""
    normalized = unicodedata.normalize('NFKD', text.casefold())
    normalized = ''.join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.replace('œ', 'oe').replace('æ', 'ae')
    words = (word for word in WORD_PATTERN.findall(normalized) if word not in STOP_WORDS)
    return [word.removesuffix('s') if len(word) > 4 else word for word in words]


def _chunks(content):
    start = 0
    while start < len(content):
        end = min(start + CHUNK_SIZE, len(content))
        if end < len(content):
            for position in range(end, end - CHUNK_OVERLAP, -1):
                if content[position].isspace():
                    end = position
                    break
        yield content[start:end].strip()
        if end == len(content):
            break
        start = end - CHUNK_OVERLAP
        while start < end and not content[start - 1].isspace():
            start += 1
        if start == end:
            start = end - CHUNK_OVERLAP


def _weights(counts, inverse_frequencies):
    return {term: (1 + math.log(count)) * inverse_frequencies[term] for term, count in counts.items()}


def search_documents(documents, query, limit=4):
    """Classe les extraits partageant au moins un terme avec la requête."""
    query_counts = Counter(tokens(query))
    if not query_counts or limit <= 0:
        return []

    excerpts = []
    document_frequencies = Counter()
    for document in documents:
        title_counts = Counter(tokens(document['title']))
        for index, chunk in enumerate(_chunks(document['content'])):
            if chunk:
                passage_counts = Counter(tokens(chunk))
                counts = passage_counts + title_counts
                matches_query = not query_counts.keys().isdisjoint(passage_counts)
                excerpts.append((document, index, chunk, counts, matches_query))
                document_frequencies.update(counts.keys())

    inverse_frequencies = {
        term: 1 + math.log((1 + len(excerpts)) / (1 + document_frequencies[term]))
        for term in document_frequencies.keys() | query_counts.keys()
    }
    query_weights = _weights(query_counts, inverse_frequencies)
    query_norm = math.hypot(*query_weights.values())
    matches = []
    for document, index, chunk, counts, matches_query in excerpts:
        if not matches_query:
            continue
        common_terms = query_weights.keys() & counts.keys()
        weights = _weights(counts, inverse_frequencies)
        dot_product = math.fsum(query_weights[term] * weights[term] for term in common_terms)
        score = min(1.0, dot_product / (query_norm * math.hypot(*weights.values())))
        matches.append({
            'document_id': document['id'],
            'title': document['title'],
            'text': chunk,
            'chunk_index': index,
            'score': score,
        })
    return sorted(matches, key=lambda match: match['score'], reverse=True)[:limit]
