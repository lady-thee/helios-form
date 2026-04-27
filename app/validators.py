from app.models import Schema, SchemaField
from typing import Optional
import re


# Validation logic for form schemas
def validate_schema(schema: Schema) -> list[str]:
    errors = []
    field_names = [field.name for field in schema.fields]
    _check_duplicate_fields(schema, errors)
    _check_field_rules(schema, errors, field_names)
    return errors

# Utility function to compute changelog between two schemas during form update
def compute_changelog(old_schema: Schema, new_schema: Schema) -> dict:
    old_fields = {f.name for f in old_schema.fields}
    new_fields = {f.name for f in new_schema.fields}

    return {
        "added":   list(new_fields - old_fields),
        "removed": list(old_fields - new_fields),
        "modified": [
            f.name for f in new_schema.fields
            if f.name in old_fields and
            f != next(o for o in old_schema.fields if o.name == f.name)
        ]
    }

# Validation logic for form submissions
def validate_submission(data: dict, schema: Schema) -> dict:
    errors = {}
    field_map = {field.name: field for field in schema.fields}

    for field in schema.fields:
        value = data.get(field.name)

        # check visibility condition first
        if field.visible_when:
            condition_field = field.visible_when.field
            condition_value = data.get(condition_field)

            # if condition is not met, field is hidden — skip it entirely
            if condition_value != field.visible_when.equals:
                continue

        # check required
        if field.type != "computed":
            field_error = _validate_field(field, value)
            if field_error:
                errors[field.name] = field_error

    return errors

# Evaluates computed fields based on their expressions and the current submission data
def evaluate_computed_fields(data: dict, schema: Schema) -> dict:
    result = data.copy()
    field_map = {field.name: field for field in schema.fields}

    for field in schema.fields:
        if field.type == "computed" and field.expression:
            try:
                # only allow field names as variables in the expression
                context = {k: v for k, v in result.items() if k in field_map}
                result[field.name] = eval(field.expression, {"__builtins__": {}}, context)
            except Exception:
                result[field.name] = None

    return result

# Utility function to normalize submission data by ensuring all fields from the latest schema version are present
def normalize_submission(data: dict, latest_field_names: list[str]) -> dict:
    normalized = {}
    for field_name in latest_field_names:
        normalized[field_name] = data.get(field_name, None)
    return normalized

# Helper functions for field validation
def _validate_field(field: SchemaField, value: any) -> str | None:
    # required check
    if field.required and (value is None or value == ""):
        return "this field is required"

    # if not required and empty, skip remaining checks
    if value is None or value == "":
        return None

    # type specific checks
    if field.type == "text":
        return _validate_text(field, value)

    if field.type == "number":
        return _validate_number(field, value)

    if field.type == "email":
        return _validate_email(value)

    if field.type == "dropdown":
        return _validate_dropdown(field, value)

    if field.type == "checkbox":
        return _validate_checkbox(value)

    if field.type == "table":
        return _validate_table(value)

    return None


def _validate_text(field: SchemaField, value: any) -> str | None:
    if not isinstance(value, str):
        return f"expected text, got {type(value).__name__}"

    if field.min_length is not None and len(value) < field.min_length:
        return f"must be at least {field.min_length} characters"

    if field.max_length is not None and len(value) > field.max_length:
        return f"must be at most {field.max_length} characters"

    return None


def _validate_number(field: SchemaField, value: any) -> str | None:
    if not isinstance(value, (int, float)):
        return f"expected a number, got {type(value).__name__}"

    if field.min_value is not None and value < field.min_value:
        return f"must be at least {field.min_value}"

    if field.max_value is not None and value > field.max_value:
        return f"must be at most {field.max_value}"

    return None


def _validate_email(value: any) -> str | None:
    if not isinstance(value, str):
        return f"expected text, got {type(value).__name__}"

    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(pattern, value):
        return "invalid email address"

    return None


def _validate_dropdown(field: SchemaField, value: any) -> str | None:
    if field.options and value not in field.options:
        return f"must be one of: {', '.join(field.options)}"

    return None


def _validate_checkbox(value: any) -> str | None:
    if not isinstance(value, bool):
        return f"expected true or false, got {type(value).__name__}"

    return None


def _validate_table(value: any) -> str | None:
    if not isinstance(value, list):
        return f"expected a list of rows, got {type(value).__name__}"

    if len(value) == 0:
        return "table must have at least one row"

    for i, row in enumerate(value):
        if not isinstance(row, dict):
            return f"row {i + 1} must be an object"

    return None

    
# Helper functions for specific validation rules
def _check_duplicate_fields(schema: Schema, errors: list[str]):
    seen = set()
    for field in schema.fields:
        if field.name in seen:
            errors.append(f"Duplicate field name: {field.name}")
        else:
            seen.add(field.name)

def _check_field_rules(schema: Schema, errors: list[str], field_names: list[str]):
    for field in schema.fields:
        _check_computed(field, errors, field_names)
        _check_dropdown(field, errors)
        _check_visible_when(field, errors, field_names)
        _check_min_max(field, errors)

def _check_computed(field: SchemaField, errors: list[str], field_names: list[str]):
    if field.type == "computed":
        if not field.expression:
            errors.append(
                f"Computed field '{field.name}' must have an expression"
            )
            return

        referenced = _extract_field_references(field.expression)
        for ref in referenced:
            if ref not in field_names:
                errors.append(
                    f"Computed field '{field.name}' references "
                    f"unknown field '{ref}' in expression '{field.expression}'"
                )

def _check_dropdown(field: SchemaField, errors: list[str]):
    if field.type == "dropdown":
        if not field.options or len(field.options) == 0:
            errors.append(
                f"Dropdown field '{field.name}' must have at least one option"
            )


def _check_visible_when(field: SchemaField, errors: list[str], field_names: list[str]):
    if field.visible_when:
        if field.visible_when.field not in field_names:
            errors.append(
                f"Field '{field.name}' has visible_when referencing "
                f"unknown field '{field.visible_when.field}'"
            )

def _check_min_max(field: SchemaField, errors: list[str]):
    if field.type == "number":
        if field.min_value is not None and field.max_value is not None:
            if field.min_value > field.max_value:
                errors.append(
                    f"Field '{field.name}' has min ({field.min_value}) "
                    f"greater than max ({field.max_value})"
                )

    if field.type == "text":
        if field.min_length is not None and field.max_length is not None:
            if field.min_length > field.max_length:
                errors.append(
                    f"Field '{field.name}' has min_length ({field.min_length}) "
                    f"greater than max_length ({field.max_length})"
                )


def _extract_field_references(expression: str) -> list[str]:
    return re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expression)