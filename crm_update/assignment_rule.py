from __future__ import annotations

import frappe
from frappe.utils.data import cint, flt


def _normalize_condition_value(value):
    if isinstance(value, str):
        try:
            if "." in value:
                return flt(value)
            return cint(value)
        except (ValueError, TypeError):
            return value
    return value


def _normalize_assign_condition(condition):
    if isinstance(condition, dict):
        normalized = {}
        for key, value in condition.items():
            if key in {"value", "value1", "value2"}:
                normalized[key] = _normalize_condition_value(value)
            else:
                normalized[key] = _normalize_assign_condition(value)
        return normalized

    if isinstance(condition, list):
        if len(condition) >= 4 and isinstance(condition[1], str):
            condition[3] = _normalize_condition_value(condition[3])
        elif len(condition) == 3 and isinstance(condition[0], str):
            condition[2] = _normalize_condition_value(condition[2])
        return [_normalize_assign_condition(item) for item in condition]

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

    normalized = _normalize_assign_condition(assign_condition)
    doc.assign_condition = frappe.as_json(normalized)
