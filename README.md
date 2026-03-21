# helios-form
A backend form engine built with FastAPI and MongoDB.

Supports creating and updating forms with versioned schemas, so changes never affect previous submissions. Core functionality includes:

- create_form() — define a new form and its initial schema
- update_form() — evolve the schema while preserving history
- validate_submission() — check a submission field-by-field against a schema
- submit() — validate, evaluate computed fields, and save a submission
- all_submissions() — retrieve all submissions for a form, normalized to the latest schema
