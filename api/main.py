import json
import os
import psycopg2
import psycopg2.extras
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

from .config import get_api_config
SCHEMA, OPENAPI_SPEC, SWAGGER_HTML = get_api_config()

class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _add_links(self, resource, item):
        if not item:
            return item
        item_id = item[SCHEMA[resource]['id']]
        links = [
            {"rel": "self", "method": "GET", "href": f"/{resource}/{item_id}"}
        ]
        
        # Add relation link for foreign keys
        if resource == 'books' and item.get('author_id'):
            links.append({"rel": "author", "method": "GET", "href": f"/authors/{item['author_id']}"})
        elif resource == 'reviews' and item.get('book_id'):
            links.append({"rel": "book", "method": "GET", "href": f"/books/{item['book_id']}"})

        item['_links'] = links
        return item

    def _parse_path(self):
        parts = urlparse(self.path).path.strip('/').split('/')
        resource = parts[0] if len(parts) > 0 and parts[0] in SCHEMA else None
        item_id = parts[1] if len(parts) > 1 and parts[1].isdigit() else None
        return resource, item_id

    def _get_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length > 0 else {}

    def _execute(self, query, params=(), fetch=False):
        try:
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(query, params)
            
            result = cur.fetchall() if fetch else None
            
            conn.commit()
            cur.close()
            conn.close()
            return result, None
        except Exception as e:
            return None, str(e)

    def do_GET(self):
        # Serve Swagger HTML UI
        if self.path == '/docs':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(SWAGGER_HTML.encode('utf-8'))
            return

        # Serve OpenAPI Spec JSON
        if self.path == '/openapi.json':
            return self._send_json(200, OPENAPI_SPEC)

        # Standard database routes
        resource, item_id = self._parse_path()
        if not resource:
            return self._send_json(404, {"error": "Endpoint not found. Visit /docs for API documentation."})

        if item_id:
            query = f"SELECT * FROM {resource} WHERE {SCHEMA[resource]['id']} = %s"
            data, err = self._execute(query, (item_id,), fetch=True)
            if err: return self._send_json(500, {"error": err})
            if not data: return self._send_json(404, {"error": "Not found"})
            return self._send_json(200, self._add_links(resource, data[0]))
        else:
            query = f"SELECT * FROM {resource}"
            data, err = self._execute(query, fetch=True)
            if err: return self._send_json(500, {"error": err})
            results = [self._add_links(resource, row) for row in data]
            return self._send_json(200, results)

    def do_POST(self):
        resource, item_id = self._parse_path()
        if not resource or item_id:
            return self._send_json(400, {"error": "Invalid POST URL. Use /<resource>"})

        body = self._get_body()
        fields = SCHEMA[resource]['fields']
        
        try:
            values = [body[f] for f in fields]
        except KeyError as e:
            return self._send_json(400, {"error": f"Missing required field: {e}"})

        cols = ', '.join(fields)
        placeholders = ', '.join(['%s'] * len(fields))
        query = f"INSERT INTO {resource} ({cols}) VALUES ({placeholders}) RETURNING *"
        
        data, err = self._execute(query, tuple(values), fetch=True)
        if err: return self._send_json(500, {"error": err})
        return self._send_json(201, data[0])

    def do_PUT(self):
        resource, item_id = self._parse_path()
        if not resource or not item_id:
            return self._send_json(400, {"error": "PUT requires an ID (e.g., /authors/1)"})

        body = self._get_body()
        fields = [f for f in SCHEMA[resource]['fields'] if f in body]
        if not fields:
            return self._send_json(400, {"error": "No valid fields provided to update"})

        set_clause = ', '.join([f"{f} = %s" for f in fields])
        values = [body[f] for f in fields] + [item_id]
        
        query = f"UPDATE {resource} SET {set_clause} WHERE {SCHEMA[resource]['id']} = %s RETURNING *"
        
        data, err = self._execute(query, tuple(values), fetch=True)
        if err: return self._send_json(500, {"error": err})
        if not data: return self._send_json(404, {"error": "Record not found"})
        return self._send_json(200, data[0])

    def do_DELETE(self):
        resource, item_id = self._parse_path()
        if not resource or not item_id:
            return self._send_json(400, {"error": "DELETE requires an ID (e.g., /authors/1)"})

        query = f"DELETE FROM {resource} WHERE {SCHEMA[resource]['id']} = %s RETURNING {SCHEMA[resource]['id']}"
        data, err = self._execute(query, (item_id,), fetch=True)
        
        if err: return self._send_json(500, {"error": err})
        if not data: return self._send_json(404, {"error": "Record not found"})
        return self._send_json(200, {"message": f"Successfully deleted {resource[:-1]} {item_id}"})

