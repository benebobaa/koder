# Simple REST API

A lightweight Python Flask REST API with basic CRUD operations for managing items.

## Features

- **GET /items** - Retrieve all items
- **GET /items/<id>** - Retrieve a specific item by ID
- **POST /items** - Create a new item
- **PUT /items/<id>** - Update an existing item
- **DELETE /items/<id>** - Delete an item

## Prerequisites

- Python 3.7+
- pip (Python package installer)

## Installation

1. Clone or download this repository
2. Navigate to the project directory
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the API

Start the Flask development server:

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Get All Items

```http
GET /items
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Sample Item",
    "description": "This is a sample item"
  }
]
```

### Get Item by ID

```http
GET /items/{id}
```

**Response:**
```json
{
  "id": 1,
  "name": "Sample Item",
  "description": "This is a sample item"
}
```

### Create New Item

```http
POST /items
Content-Type: application/json

{
  "name": "New Item",
  "description": "Description of new item"
}
```

**Response:**
```json
{
  "id": 2,
  "name": "New Item",
  "description": "Description of new item"
}
```

### Update Item

```http
PUT /items/{id}
Content-Type: application/json

{
  "name": "Updated Item",
  "description": "Updated description"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Updated Item",
  "description": "Updated description"
}
```

### Delete Item

```http
DELETE /items/{id}
```

**Response:**
```json
{
  "message": "Item deleted successfully"
}
```

## Example Usage with curl

### Get all items:
```bash
curl http://localhost:5000/items
```

### Create a new item:
```bash
curl -X POST http://localhost:5000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "Testing the API"}'
```

### Update an item:
```bash
curl -X PUT http://localhost:5000/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "description": "Updated description"}'
```

### Delete an item:
```bash
curl -X DELETE http://localhost:5000/items/1
```

## Development

This is a simple Flask application for demonstration purposes. For production use, consider:

- Adding proper error handling
- Implementing authentication/authorization
- Using a proper database instead of in-memory storage
- Adding input validation
- Implementing rate limiting

## License

MIT License