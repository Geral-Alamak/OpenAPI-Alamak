def get_api_config():
    SCHEMA = {
        'authors': {'id': 'author_id', 'fields': ['name']},
        'books': {'id': 'book_id', 'fields': ['title', 'author_id']},
        'reviews': {'id': 'review_id', 'fields': ['book_id', 'rating', 'review_text']}
    }

    OPENAPI_SPEC = {
      "openapi": "3.0.0",
      "info": {
        "title": "Authors, Books & Reviews API",
        "version": "1.0.0"
      },
      "paths": {
        "/{resource}": {
          "get": {
            "summary": "Get all records",
            "parameters": [{"name": "resource", "in": "path", "required": True, "schema": {"type": "string", "example": "books"}}],
            "responses": {
              "200": {
                "description": "List of records",
                "content": {
                  "application/json": {
                    "example": [
                      {
                        "book_id": 1,
                        "title": "Dune",
                        "author_id": 2,
                        "_links": [
                          {"rel": "self", "method": "GET", "href": "/books/1"},
                          {"rel": "author", "method": "GET", "href": "/authors/2"}
                        ]
                      }
                    ]
                  }
                }
              }
            }
          },
          "post": {
            "summary": "Create a new record",
            "parameters": [{"name": "resource", "in": "path", "required": True, "schema": {"type": "string", "example": "books"}}],
            "requestBody": {
              "content": {
                "application/json": {
                  "example": {
                    "title": "Dune Messiah",
                    "author_id": 2
                  }
                }
              }
            },
            "responses": {
              "201": {
                "description": "Record created",
                "content": {
                  "application/json": {
                    "example": {
                      "book_id": 2,
                      "title": "Dune Messiah",
                      "author_id": 2
                    }
                  }
                }
              }
            }
          }
        },
        "/{resource}/{id}": {
          "get": {
            "summary": "Get a record by ID",
            "parameters": [
              {"name": "resource", "in": "path", "required": True, "schema": {"type": "string", "example": "books"}},
              {"name": "id", "in": "path", "required": True, "schema": {"type": "integer", "example": 1}}
            ],
            "responses": {
              "200": {
                "description": "Single record",
                "content": {
                  "application/json": {
                    "example": {
                      "book_id": 1,
                      "title": "Dune",
                      "author_id": 2,
                      "_links": [
                        {"rel": "self", "method": "GET", "href": "/books/1"},
                        {"rel": "author", "method": "GET", "href": "/authors/2"}
                      ]
                    }
                  }
                }
              }
            }
          },
          "put": {
            "summary": "Update a record",
            "parameters": [
              {"name": "resource", "in": "path", "required": True, "schema": {"type": "string", "example": "books"}},
              {"name": "id", "in": "path", "required": True, "schema": {"type": "integer", "example": 1}}
            ],
            "requestBody": {
              "content": {
                "application/json": {
                  "example": {
                    "title": "Dune (Updated Edition)"
                  }
                }
              }
            },
            "responses": {
              "200": {
                "description": "Record updated",
                "content": {
                  "application/json": {
                    "example": {
                      "book_id": 1,
                      "title": "Dune (Updated Edition)",
                      "author_id": 2
                    }
                  }
                }
              }
            }
          },
          "delete": {
            "summary": "Delete a record",
            "parameters": [
              {"name": "resource", "in": "path", "required": True, "schema": {"type": "string", "example": "books"}},
              {"name": "id", "in": "path", "required": True, "schema": {"type": "integer", "example": 1}}
            ],
            "responses": {
              "200": {
                "description": "Record deleted",
                "content": {
                  "application/json": {
                    "example": {
                      "message": "Successfully deleted book 1"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    SWAGGER_HTML = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>API Documentation</title>
      <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin></script>
      <script>
        window.onload = () => {
          window.ui = SwaggerUIBundle({
            url: '/openapi.json',
            dom_id: '#swagger-ui',
          });
        };
      </script>
    </body>
    </html>
    """
    
    return SCHEMA, OPENAPI_SPEC, SWAGGER_HTML
