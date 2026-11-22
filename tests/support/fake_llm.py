"""Fournisseur factice réservé au test Docker, sans appel à un service payant."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers.get('Content-Length', 0)))
        material = {
            'title': 'Résumé de test',
            'content': 'Une variable associe un nom à une valeur. [1]',
        }
        response = {
            'id': 'test',
            'object': 'chat.completion',
            'created': 0,
            'model': 'fake-ci',
            'choices': [
                {
                    'index': 0,
                    'finish_reason': 'stop',
                    'message': {'role': 'assistant', 'content': json.dumps(material)},
                }
            ],
        }
        payload = json.dumps(response).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 8050), Handler).serve_forever()
