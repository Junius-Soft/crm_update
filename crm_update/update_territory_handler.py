import frappe

FIELD_MAP = {
    "territory_name": "territory_name",
    "parent_territory": "parent_territory",
    "is_group": "is_group",
    "territory_manager": "territory_manager"
}


def sync_territory(doc, method=None):
    # recursion koruması
    if frappe.flags.in_sync:
        return

    frappe.flags.in_sync = True

    # hangi taraftan geldiğini belirle
    if doc.doctype == "Territory":
        source_doctype = "Territory"
        target_doctype = "CRM Territory"
        source_key = doc.name
        target_key = doc.name

    elif doc.doctype == "CRM Territory":
        source_doctype = "CRM Territory"
        target_doctype = "Territory"
        source_key = doc.territory_name
        target_key = doc.territory_name

    else:
        return

    # DELETE senaryosu (after_delete hook ile çağrılırsa)
    if method == "after_delete":
        if frappe.db.exists(target_doctype, target_key):
            frappe.delete_doc(target_doctype, target_key, ignore_permissions=True)
        return

    # INSERT / UPDATE
    if frappe.db.exists(target_doctype, target_key):
        target_doc = frappe.get_doc(target_doctype, target_key)
    else:
        target_doc = frappe.new_doc(target_doctype)

    # field mapping
    for source_field, target_field in FIELD_MAP.items():
        value = doc.get(source_field)
        if value is not None:
            target_doc.set(target_field, value)

    # name / key mapping (çok önemli)
    if target_doctype == "CRM Territory":
        target_doc.territory_name = doc.name
    else:
        target_doc.territory_name = doc.territory_name

    # loop engellemek için flag set et
    target_doc.flags.ignore_links = True
    target_doc.flags.ignore_mandatory = True

    target_doc.save(ignore_permissions=True)