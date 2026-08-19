"""Small, dependency-free validation helpers for JSON API requests."""

from datetime import datetime

from flask import request


class ValidationError(ValueError):
    """A client supplied invalid JSON or a field with an invalid value."""


def get_json_object():
    """Return a JSON object, rejecting missing JSON, arrays, and invalid JSON."""
    if not request.is_json:
        raise ValidationError("Content-Type must be application/json.")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    return data


def reject_unknown_fields(data, allowed_fields):
    unknown = set(data) - set(allowed_fields)
    if unknown:
        raise ValidationError(f"Unknown field(s): {', '.join(sorted(unknown))}.")


def required_string(data, field):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} is required and must be a non-empty string.")
    return value.strip()


def optional_string(data, field, default=None, allow_null=True):
    if field not in data:
        return default
    value = data[field]
    if value is None and allow_null:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string.")
    return value.strip() or None


def boolean(data, field, default=False):
    if field not in data:
        return default
    value = data[field]
    if type(value) is not bool:
        raise ValidationError(f"{field} must be true or false.")
    return value


def integer(data, field, default=None, minimum=None):
    if field not in data:
        return default
    value = data[field]
    if type(value) is not int:
        raise ValidationError(f"{field} must be an integer.")
    if minimum is not None and value < minimum:
        raise ValidationError(f"{field} must be at least {minimum}.")
    return value


def iso_date(data, field, default=None):
    value = optional_string(data, field, default=default)
    if value is None:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(f"{field} must use YYYY-MM-DD format.") from exc
    return value

