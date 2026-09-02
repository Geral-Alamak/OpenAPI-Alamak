import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Library API", "version": "1.0.0"},
    "paths": {
        "/authors": {
            "get": {"summary": "Get authors", "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Add author", "responses": {"201": {"description": "Created"}}}
        },
        "/books": {
            "get": {"summary": "Get books", "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Add book", "responses": {"201": {"description": "Created"}}}
        },
        "/reviews": {
            "get": {"summary": "Get reviews", "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Add review", "responses": {"201": {"description": "Created"}}}
        }
    }
}

class RequestHandler(BaseHTTPRequestHandler):
    def get_db(self):
        return psycopg2.connect(DATABASE_URL)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/openapi.json":
            self._send_json(OPENAPI_SPEC)
            return

        conn = self.get_db()
        cur = conn.cursor()

        if path == "/authors":
            cur.execute("SELECT author_id, name FROM authors;")
            rows = cur.fetchall()
            self._send_json([{"author_id": r[0], "name": r[1]} for r in rows])
        elif path == "/books":
            cur.execute("SELECT book_id, title, author_id FROM books;")
            rows = cur.fetchall()
            self._send_json([{"book_id": r[0], "title": r[1], "author_id": r[2]} for r in rows])
        elif path == "/reviews":
            cur.execute("SELECT review_id, rating, comment, book_id FROM reviews;")
            rows = cur.fetchall()
            self._send_json([{"review_id": r[0], "rating": r[1], "comment": r[2], "book_id": r[3]} for r in rows])
        else:
            self._send_json({"error": "Not Found"}, 404)

        cur.close()
        conn.close()

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}

        conn = self.get_db()
        cur = conn.cursor()

        if path == "/authors":
            cur.execute("INSERT INTO authors (name) VALUES (%s) RETURNING author_id;", (body.get("name"),))
            author_id = cur.fetchone()[0]
            conn.commit()
            self._send_json({"author_id": author_id, "name": body.get("name")}, 201)
        elif path == "/books":
            cur.execute(
                "INSERT INTO books (title, author_id) VALUES (%s, %s) RETURNING book_id;",
                (body.get("title"), body.get("author_id"))
            )
            book_id = cur.fetchone()[0]
            conn.commit()
            self._send_json({"book_id": book_id, "title": body.get("title"), "author_id": body.get("author_id")}, 201)
        elif path == "/reviews":
            cur.execute(
                "INSERT INTO reviews (rating, comment, book_id) VALUES (%s, %s, %s) RETURNING review_id;",
                (body.get("rating"), body.get("comment"), body.get("book_id"))
            )
            review_id = cur.fetchone()[0]
            conn.commit()
            self._send_json({"review_id": review_id, "rating": body.get("rating"), "comment": body.get("comment"), "book_id": body.get("book_id")}, 201)
        else:
            self._send_json({"error": "Not Found"}, 404)

        cur.close()
        conn.close()

def run():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), RequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    run()
