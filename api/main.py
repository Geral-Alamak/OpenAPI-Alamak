import json
import os
import psycopg2
import psycopg2.extras
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

# Schema maps tables to their Primary Keys and allowed input fields
SCHEMA = {
    'authors': {'id': 'author_id', 'fields': ['name']},
    'books': {'id': 'book_id', 'fields': ['title', 'author_id']},
    'reviews': {'id': 'review_id', 'fields': ['book_id', 'rating', 'review_text']}
}

#Swagger
{
  "openapi": "3.0.0",
  "info": {
    "title": "Authors, Books & Reviews API",
    "version": "1.0.0",
    "description": "A RESTful API for managing authors, books, and reviews."
  },
  "paths": {
    "/{resource}": {
      "get": {
        "summary": "Get all records",
        "parameters": [
          {
            "name": "resource",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "enum": ["authors", "books", "reviews"],
              "example": "authors"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "A list of records",
            "content": {
              "application/json": {
                "example": [
                  {"author_id": 1, "name": "Isaac Asimov"},
                  {"author_id": 2, "name": "Frank Herbert"}
                ]
              }
            }
          }
        }
      },
      "post": {
        "summary": "Create a new record",
        "parameters": [
          {
            "name": "resource",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "enum": ["authors", "books", "reviews"],
              "example": "books"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "example": {
                  "title": "Dune",
                  "author_id": 2
                }
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "Record created"
          }
        }
      }
    },
    "/{resource}/{id}": {
      "get": {
        "summary": "Get a record by ID",
        "parameters": [
          {
            "name": "resource",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "example": "reviews"
            }
          },
          {
            "name": "id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "integer",
              "example": 1
            }
          }
        ],
        "responses": {
          "200": {
            "description": "A single record"
          }
        }
      },
      "put": {
        "summary": "Update a record",
        "parameters": [
          {
            "name": "resource",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "example": "authors"
            }
          },
          {
            "name": "id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "integer",
              "example": 1
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "example": {
                  "name": "Isaac Asimov (Updated)"
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Record updated"
          }
        }
      },
      "delete": {
        "summary": "Delete a record",
        "parameters": [
          {
            "name": "resource",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "example": "books"
            }
          },
          {
            "name": "id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "integer",
              "example": 1
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Record deleted"
          }
        }
      }
    }
  }
}

class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

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
            return self._send_json(200, data[0] if data else {"error": "Not found"})
        else:
            query = f"SELECT * FROM {resource}"
            data, err = self._execute(query, fetch=True)
            if err: return self._send_json(500, {"error": err})
            return self._send_json(200, data)

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

