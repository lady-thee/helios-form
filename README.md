
# Helios Form Engine

A backend form engine built with FastAPI and MongoDB. Supports creating and updating forms with versioned schemas, so changes never affect previous submissions.

---

## Features

- Create forms with typed, validated schemas
- Schema versioning — every update creates a new immutable version
- Field-by-field submission validation with structured error responses
- Conditional field visibility — show fields based on other field values
- Computed fields — evaluate expressions like `qty * price` at submission time
- Normalized submission retrieval across all schema versions
- Automatic changelog when a schema is updated

---

## Requirements

- Python 3.11+
- MongoDB 6.0+

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/lady-thee/helios-form.git
cd helios-form
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv

# Mac/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Create a `.env` file in the root directory**

```
MONGODB_URL=mongodb://localhost:27017
DB_NAME=helios_form_engine
```

**5. Make sure MongoDB is running**

```bash
mongosh
```

If you get a `>` prompt, MongoDB is up. Type `exit` to leave.

---

## Running the Server

```bash
uvicorn app.main:app
```

The server will start at `http://localhost:8000`.

Interactive API docs are available at `http://localhost:8000/docs`.

---

## API Endpoints

### Create a Form
```
POST /api/forms
```

Creates a new form and stores the schema as version 1.

**Request body:**
```json
{
  "name": "Customer Feedback",
  "description": "A form for collecting customer feedback",
  "form_schema": {
    "fields": [
      {
        "name": "full_name",
        "type": "text",
        "required": true,
        "min_length": 2,
        "max_length": 100
      },
      {
        "name": "rating",
        "type": "number",
        "required": true,
        "min_value": 1,
        "max_value": 5
      },
      {
        "name": "service_type",
        "type": "dropdown",
        "required": true,
        "options": ["support", "sales", "billing"]
      },
      {
        "name": "complaint_details",
        "type": "text",
        "required": true,
        "visible_when": {
          "field": "service_type",
          "equals": "support"
        }
      }
    ]
  }
}
```

**Response:**
```json
{
  "message": "Form created successfully",
  "form": {
    "id": "64f1a2b3c4d5e6f7a8b9c0d1",
    "name": "Customer Feedback",
    "description": "A form for collecting customer feedback",
    "version_number": 1,
    "version_id": "64f1a2b3c4d5e6f7a8b9c0d2",
    "created_at": "2025-01-01T09:00:00Z"
  }
}
```

---

### Update a Form
```
PUT /api/forms/{form_id}
```

Creates a new schema version. All fields are optional — only send what you want to change. Previous versions and their submissions are never affected.

**Request body:**
```json
{
  "name": "Customer Feedback v2",
  "form_schema": {
    "fields": [
      {
        "name": "full_name",
        "type": "text",
        "required": true,
        "min_length": 2,
        "max_length": 100
      },
      {
        "name": "phone_number",
        "type": "text",
        "required": true,
        "min_length": 11,
        "max_length": 11
      }
    ]
  }
}
```

**Response:**
```json
{
  "id": "64f1a2b3c4d5e6f7a8b9c0d1",
  "name": "Customer Feedback v2",
  "description": "A form for collecting customer feedback",
  "version_number": 2,
  "version_id": "64f1a2b3c4d5e6f7a8b9c0d3",
  "changelog": {
    "added": ["phone_number"],
    "removed": ["rating", "service_type", "complaint_details"],
    "modified": []
  }
}
```

---

### Submit a Form
```
POST /api/forms/{form_id}/submit
```

Validates the submission against the latest schema version and saves it. Computed fields are evaluated automatically.

**Request body:**
```json
{
  "data": {
    "full_name": "Amara Okafor",
    "phone_number": "08012345678"
  }
}
```

**Response:**
```json
{
  "id": "64f1a2b3c4d5e6f7a8b9c0d4",
  "form_id": "64f1a2b3c4d5e6f7a8b9c0d1",
  "version_id": "64f1a2b3c4d5e6f7a8b9c0d3",
  "data": {
    "full_name": "Amara Okafor",
    "phone_number": "08012345678"
  },
  "submitted_at": "2025-03-15T10:22:00Z"
}
```

**Validation error response:**
```json
{
  "detail": {
    "full_name": "this field is required",
    "phone_number": "must be at most 11 characters"
  }
}
```

---

### Get All Submissions
```
GET /api/forms/{form_id}/submissions
```

Returns all submissions for a form, normalized to the latest schema. Submissions from older versions will have `null` for fields that did not exist at the time of submission.

**Response:**
```json
[
  {
    "id": "64f1a2b3c4d5e6f7a8b9c0d4",
    "form_id": "64f1a2b3c4d5e6f7a8b9c0d1",
    "version_id": "64f1a2b3c4d5e6f7a8b9c0d2",
    "data": {
      "full_name": "Emeka Nwosu",
      "phone_number": null
    },
    "submitted_at": "2025-01-15T08:00:00Z"
  },
  {
    "id": "64f1a2b3c4d5e6f7a8b9c0d5",
    "form_id": "64f1a2b3c4d5e6f7a8b9c0d1",
    "version_id": "64f1a2b3c4d5e6f7a8b9c0d3",
    "data": {
      "full_name": "Amara Okafor",
      "phone_number": "08012345678"
    },
    "submitted_at": "2025-03-15T10:22:00Z"
  }
]
```

---

## Supported Field Types

| Type | Description |
|---|---|
| `text` | Plain text input. Supports `min_length` and `max_length`. |
| `number` | Numeric input. Supports `min_value` and `max_value`. |
| `email` | Email address. Validated against standard email format. |
| `dropdown` | Select from a list. Requires `options` array. |
| `checkbox` | Boolean true/false field. |
| `table` | List of row objects. |
| `computed` | Evaluated automatically from an `expression` referencing other fields. e.g. `qty * price`. |

---

## Conditional Visibility

Fields can be shown or hidden based on the value of another field using `visible_when`:

```json
{
  "name": "complaint_details",
  "type": "text",
  "required": true,
  "visible_when": {
    "field": "service_type",
    "equals": "support"
  }
}
```

Hidden fields are skipped entirely during validation — even if marked required.

---

## Schema Versioning

Every call to `PUT /api/forms/{form_id}` with a new `form_schema` creates an immutable `FormVersion` snapshot. Submissions are permanently linked to the version they were validated against. This means:

- Old submissions are never invalidated by schema changes
- All submissions can always be re-validated against their original schema
- `GET /submissions` normalizes all submissions to the latest schema shape, filling `null` for fields that did not exist in older versions

---

## Project Structure

```
helios-form/
├── app/
│   ├── main.py          # FastAPI app and startup
│   ├── database.py      # MongoDB connection and Beanie init
│   ├── models.py        # Beanie document models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── services.py      # Core business logic
│   ├── validators.py    # Schema and submission validators
│   └── routes.py        # API route definitions
├── .env                 # Environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## Tech Stack

- **FastAPI** — API framework
- **Beanie** — MongoDB ODM
- **PyMongo (async)** — MongoDB async driver
- **Pydantic** — Data validation
- **Uvicorn** — ASGI server