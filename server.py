#!/usr/bin/env python3
"""
Hermes Study Space — Research Log Server

Provides:
  - Static file serving for the study log website
  - POST /api/comment — submit feedback
  - Data auto-reload via cache-busting

Usage:
  python3 server.py [port]
  Default port: 8765
"""

import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
RESEARCH_JSON = os.path.join(DATA_DIR, 'research.json')


class StudySpaceHandler(SimpleHTTPRequestHandler):
    """Custom handler with API endpoints for comments."""

    def do_GET(self):
        parsed = urlparse(self.path)

        # API: get research data
        if parsed.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            try:
                with open(RESEARCH_JSON, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        # API: get comments for a specific day
        if parsed.path.startswith('/api/comments/'):
            day = parsed.path.split('/')[-1]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                with open(RESEARCH_JSON, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                phase = next((p for p in data['phases'] if str(p['day']) == day), None)
                comments = phase['comments'] if phase else []
                self.wfile.write(json.dumps(comments, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        # Default: serve static files from root directory
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == '/api/comment':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')

            try:
                data = json.loads(body)
                day = data.get('day')
                author = data.get('author', '匿名')
                text = data.get('body', '').strip()

                if not text:
                    self._json_response(400, {'error': '内容不能为空'})
                    return

                # Read existing data
                with open(RESEARCH_JSON, 'r', encoding='utf-8') as f:
                    research = json.load(f)

                # Find the phase
                phase = next((p for p in research['phases'] if p['day'] == day), None)
                if not phase:
                    self._json_response(404, {'error': f'Day {day} not found'})
                    return

                # Add comment
                comment = {
                    'author': author,
                    'body': text,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                phase.setdefault('comments', []).append(comment)

                # Write back
                with open(RESEARCH_JSON, 'w', encoding='utf-8') as f:
                    json.dump(research, f, ensure_ascii=False, indent=2)

                self._json_response(200, {'success': True, 'comment': comment})

            except json.JSONDecodeError:
                self._json_response(400, {'error': '无效的 JSON'})
            except Exception as e:
                self._json_response(500, {'error': str(e)})
            return

        self.send_response(404)
        self.end_headers()

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        """Quieter logging."""
        if '/api/' in str(args[0]) or '?t=' not in str(args[0]):
            sys.stderr.write("[%s] %s - %s\n" % (
                self.log_date_time_string(),
                self.client_address[0],
                format % args
            ))


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

    # Change to script directory so static files resolve correctly
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    server = HTTPServer(('0.0.0.0', port), StudySpaceHandler)
    print(f"🌌 Hermes Study Space server running at http://localhost:{port}")
    print(f"📁 Serving files from: {os.getcwd()}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
        server.server_close()
