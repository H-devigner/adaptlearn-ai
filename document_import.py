"""Lecture et validation des documents personnels importés."""

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError
from werkzeug.exceptions import RequestEntityTooLarge

from generation import valid_text

MAX_IMPORT_BYTES = 1024 * 1024
MAX_DOCUMENT_LENGTH = 50_000


def _pdf_text(payload):
    if not payload.startswith(b'%PDF-'):
        raise ValueError('Ce fichier ne contient pas de PDF lisible.')
    pages = []
    total = 0
    try:
        reader = PdfReader(BytesIO(payload), strict=True)
        encrypted = reader.is_encrypted
        if not encrypted:
            for page in reader.pages:
                content = (page.extract_text() or '').strip()
                if content:
                    total += len(content) + bool(pages)
                    if total > MAX_DOCUMENT_LENGTH:
                        break
                    pages.append(content)
    except (
        PyPdfError,
        OSError,
        ValueError,
        RecursionError,
        TypeError,
        KeyError,
        IndexError,
        OverflowError,
    ):
        raise ValueError('Ce fichier ne contient pas de PDF lisible.') from None
    if encrypted:
        raise ValueError('Retirez le mot de passe du PDF avant de l’importer.')
    if total > MAX_DOCUMENT_LENGTH:
        raise ValueError('Le texte du document dépasse 50 000 caractères.')
    if not pages:
        raise ValueError(
            'Ce PDF ne contient pas de texte extractible. Utilisez un PDF textuel ou collez le texte.'
        )
    return '\n'.join(pages)


def import_document_text(content, upload):
    """Lit un texte collé ou un fichier et applique les limites d’import."""
    if upload and upload.filename:
        if content.strip():
            raise ValueError(
                'Collez du texte ou choisissez un fichier. Utilisez une seule méthode à la fois.'
            )
        payload = upload.stream.read(MAX_IMPORT_BYTES + 1)
        if len(payload) > MAX_IMPORT_BYTES:
            raise RequestEntityTooLarge()
        extension = Path(upload.filename).suffix.lower()
        if extension == '.pdf':
            content = _pdf_text(payload)
        elif extension in ('.txt', '.md'):
            try:
                content = payload.decode('utf-8-sig')
            except UnicodeDecodeError:
                raise ValueError('Le fichier texte doit être encodé en UTF-8.') from None
        else:
            raise ValueError('Importez un fichier .txt, .md ou .pdf.')
    if not valid_text(content, MAX_DOCUMENT_LENGTH):
        raise ValueError('Fournissez 1 à 50 000 caractères de texte valide, sans caractère nul.')
    return content.strip()
