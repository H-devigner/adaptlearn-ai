"""Client HTTP du service de génération optionnel."""

import http.client
import json
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from generation import GenerationError, parse_strict_json, validate_material

MAX_SERVICE_RESPONSE_BYTES = 128 * 1024


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


urlopen = build_opener(_NoRedirect).open


def generate_service_material(kind, query, sources, config):
    """Demande un support au service IA et vérifie sa réponse."""
    address = config.get('AI_SERVICE_URL')
    token = config.get('AI_SERVICE_TOKEN')
    if not isinstance(token, str) or not token or any(char.isspace() for char in token):
        raise GenerationError('Le jeton du service IA est absent ou invalide.')
    try:
        if not isinstance(address, str) or any(char.isspace() for char in address):
            raise ValueError('URL de service invalide.')
        base = urlsplit(address)
        if (
            base.scheme not in ('http', 'https')
            or not base.hostname
            or base.username is not None
            or base.query
            or base.fragment
        ):
            raise ValueError('URL de service invalide.')
        http_request = Request(
            address.rstrip('/') + '/generate',
            data=json.dumps(
                {'kind': kind, 'query': query, 'sources': sources}, ensure_ascii=False
            ).encode('utf-8'),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            method='POST',
        )
        with urlopen(http_request, timeout=55) as remote:
            body = remote.read(MAX_SERVICE_RESPONSE_BYTES + 1)
    except HTTPError as error:
        error.close()
        if error.code == 400:
            raise ValueError(
                'Le contexte ne permet pas de créer ce support. Reformulez la requête ou choisissez d’autres sources.'
            ) from None
        if error.code == 413:
            raise ValueError(
                'Les extraits dépassent la taille acceptée par le service IA. Choisissez d’autres sources.'
            ) from None
        raise GenerationError('Le service IA a refusé la demande.') from None
    except (OSError, TypeError, ValueError, http.client.HTTPException):
        raise GenerationError('Impossible de joindre le service IA ou délai dépassé.') from None
    try:
        if len(body) > MAX_SERVICE_RESPONSE_BYTES:
            raise ValueError('Réponse trop volumineuse.')
        material = validate_material(parse_strict_json(body.decode('utf-8')), kind)
        if material['mode'] != 'llm':
            raise ValueError('Mode de génération invalide.')
        return material
    except (ValueError, RecursionError):
        raise GenerationError('Le service IA a renvoyé un support invalide.') from None
