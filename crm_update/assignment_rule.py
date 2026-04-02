from __future__ import annotations

import frappe
from frappe.utils.data import cint, flt

NUMERIC_FIELD_TYPES = {"Int", "Float", "Currency", "Percent", "Rating"}


def _convert_numeric_string(value: str, fieldtype: str):
    if not isinstance(value, str):
        return value

    try:
        if fieldtype in {"Float", "Currency", "Percent"} or "." in value:
            return flt(value)
        return cint(value)
    except (ValueError, TypeError):
        return value


def _normalize_condition_value(value, fieldtype=None):
    if isinstance(value, str) and fieldtype in NUMERIC_FIELD_TYPES:
        return _convert_numeric_string(value, fieldtype)
    return value


def _get_doctype_field(meta, fieldname: str):
    if not fieldname or not meta:
        return None
    return meta.get_field(fieldname)


def _normalize_assign_condition(condition, meta):
    if isinstance(condition, dict):
        normalized = {}
        for key, value in condition.items():
            if key in {"value", "value1", "value2"}:
                fieldname = condition.get("field") or condition.get("fieldname") or condition.get("docfield")
                field = _get_doctype_field(meta, fieldname)
                if field and field.fieldtype in NUMERIC_FIELD_TYPES:
                    normalized[key] = _convert_numeric_string(value, field.fieldtype)
                else:
                    normalized[key] = _normalize_assign_condition(value, meta)
            else:
                normalized[key] = _normalize_assign_condition(value, meta)
        return normalized

    if isinstance(condition, list):
        if len(condition) >= 4 and isinstance(condition[1], str):
            field = _get_doctype_field(meta, condition[1])
            if field and field.fieldtype in NUMERIC_FIELD_TYPES and isinstance(condition[3], str):
                condition[3] = _convert_numeric_string(condition[3], field.fieldtype)
        return [_normalize_assign_condition(item, meta) for item in condition]

    return condition


def normalize_assignment_rule_conditions(doc, method=None):
    if doc.doctype != "Assignment Rule":
        return

    assign_condition = doc.get("assign_condition")
    if not assign_condition:
        return

    if isinstance(assign_condition, str):
        assign_condition = assign_condition.strip()
        if not assign_condition:
            return

        try:
            assign_condition = frappe.parse_json(assign_condition)
        except (ValueError, TypeError):
            if not assign_condition[0] in ("[", "{"):
                return
            try:
                assign_condition = frappe.safe_eval(assign_condition)
            except (ValueError, SyntaxError, TypeError, NameError):
                return

    doctype_name = doc.get("document_type") or doc.get("reference_doctype")
    if not doctype_name:
        return

    try:
        meta = frappe.get_meta(doctype_name)
    except Exception:
        meta = None

    normalized = _normalize_assign_condition(assign_condition, meta)
    doc.assign_condition = frappe.as_json(normalized)
