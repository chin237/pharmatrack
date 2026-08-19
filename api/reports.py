"""Administrative reports; deliberately unavailable to read-only users."""

from flask import jsonify, request

from api import api_v1_bp
from api.auth import _api_error, role_required
from api.validation import ValidationError, get_json_object, optional_string, reject_unknown_fields
from database.queries import get_dashboard_data, get_loss_reports, mark_loss_reported


@api_v1_bp.get('/reports/dashboard')
@role_required('admin')
def dashboard_report():
    return jsonify(get_dashboard_data())


@api_v1_bp.get('/reports/losses')
@role_required('admin')
def loss_reports():
    return jsonify(get_loss_reports())


@api_v1_bp.patch('/reports/losses/<loss_report_id>/reported')
@role_required('admin')
def report_loss(loss_report_id):
    try:
        data = get_json_object()
        reject_unknown_fields(data, {'authority_reference'})
        authority_reference = optional_string(data, 'authority_reference')
    except ValidationError as exc:
        return _api_error(str(exc))
    mark_loss_reported(loss_report_id, authority_reference=authority_reference)
    return jsonify(message='Loss report marked as reported.')
