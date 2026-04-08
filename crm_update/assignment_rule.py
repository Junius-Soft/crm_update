from __future__ import annotations

import ast
import re
import frappe
from frappe.utils.data import cint, flt


NUMERIC_FIELD_TYPES = {"Float", "Int", "Currency", "Percent", "Decimal"}


def _get_fieldtype(doctype, fieldname):
    if not doctype or not fieldname:
        return None

    try:
        meta = frappe.get_meta(doctype)
        field = meta.get_field(fieldname)
        if field:
            return field.fieldtype
    except Exception:
        pass

    return None


def _normalize_condition_value(value, fieldtype=None):
    if isinstance(value, str):
        # only convert number-like values for numeric fields
        if fieldtype in NUMERIC_FIELD_TYPES:
            try:
                if "." in value:
                    return flt(value)
                return cint(value)
            except (ValueError, TypeError):
                return value
        return value
    return value


def _normalize_assign_condition(condition, doctype=None):
    if isinstance(condition, dict):
        normalized = {}
        for key, value in condition.items():
            if key in {"value", "value1", "value2"}:
                normalized[key] = _normalize_condition_value(value, _get_fieldtype(doctype, key))
            else:
                normalized[key] = _normalize_assign_condition(value, doctype)
        return normalized

    if isinstance(condition, list):
        # Condition list can be:
        # - [fieldname, operator, value]
        # - [fieldname, operator, value, [value2], ...]
        # - nested condition groups: ['and', [...], [...]]
        if len(condition) == 3 and isinstance(condition[0], str) and isinstance(condition[1], str):
            fieldtype = _get_fieldtype(doctype, condition[0])
            return [condition[0], condition[1], _normalize_condition_value(condition[2], fieldtype)]

        if len(condition) >= 4 and isinstance(condition[1], str):
            fieldtype = _get_fieldtype(doctype, condition[0])
            normalized = [condition[0], condition[1], condition[2], _normalize_condition_value(condition[3], fieldtype)]
            normalized.extend(_normalize_assign_condition(item, doctype) for item in condition[4:])
            return normalized

        return [_normalize_assign_condition(item, doctype) for item in condition]

    return condition




def _condition_to_assign_expression(condition):
    """Convert assign_condition_json structure to assign_condition string."""
    if not condition:
        return ""

    if isinstance(condition, str):
        try:
            condition = frappe.parse_json(condition)
        except (ValueError, TypeError):
            return ""

    # Normalize single condition format to list of conditions
    if isinstance(condition, list) and len(condition) == 3 and isinstance(condition[0], str):
        condition = [condition]

    expressions = []

    if isinstance(condition, list):
        for cond in condition:
            if isinstance(cond, list) and len(cond) == 3:
                field, op, value = cond
                if isinstance(value, str):
                    value_repr = f'"{value}"'
                elif isinstance(value, bool):
                    value_repr = "True" if value else "False"
                else:
                    value_repr = str(value)
                expressions.append(f"{field} {op} {value_repr}")

    return " and ".join(expressions)


def _normalize_rule_field(doc, json_field, condition_field):
    field_json = doc.get(json_field)
    if field_json:
        if isinstance(field_json, str):
            field_json = field_json.strip()
            if not field_json:
                field_json = None

        if field_json:
            try:
                field_json = frappe.parse_json(field_json)
            except (ValueError, TypeError):
                field_json = None

    if field_json:
        normalized = _normalize_assign_condition(field_json, doc.document_type)
        doc.set(json_field, frappe.as_json(normalized))
        doc.set(condition_field, _condition_to_assign_expression(normalized))
        return True

    condition = doc.get(condition_field)
    if not condition:
        return False

    if isinstance(condition, str):
        condition = condition.strip()
        if not condition:
            return False

        try:
            condition = frappe.parse_json(condition)
        except (ValueError, TypeError):
            if not (condition and condition[0] in ('[', '{')):
                return False

            # parse fallback for invalid JSON-like python list syntax
            try:
                condition = ast.literal_eval(condition)
            except (ValueError, SyntaxError):
                # fall back on simple fix list items to quoted string when possible
                if condition.startswith('[') and condition.endswith(']'):
                    m = re.match(r'^\s*\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*,', condition)
                    if m:
                        condition = re.sub(r'^\s*\[\s*([a-zA-Z_][a-zA-Z0-9_]*)', r'["\1"', condition)
                        try:
                            condition = ast.literal_eval(condition)
                        except (ValueError, SyntaxError):
                            return False
                    else:
                        return False
                else:
                    return False

    normalized = _normalize_assign_condition(condition, doc.document_type)
    doc.set(json_field, frappe.as_json(normalized))
    doc.set(condition_field, _condition_to_assign_expression(normalized))
    return True


def normalize_assignment_rule_conditions(doc, method=None):
    if doc.doctype != "Assignment Rule":
        return

    changed = _normalize_rule_field(doc, "assign_condition_json", "assign_condition")
    changed |= _normalize_rule_field(doc, "unassign_condition_json", "unassign_condition")

    # If either field is normalized, doc fields are set accordingly
    return changed


def migrate_assignment_rules():
    """Run once after deploy to normalize all existing Assignment Rule records."""
    for r in frappe.get_all("Assignment Rule", fields=["name"]):
        doc = frappe.get_doc("Assignment Rule", r.name)
        if normalize_assignment_rule_conditions(doc):
            doc.save(ignore_permissions=True)

