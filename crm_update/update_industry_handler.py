import frappe

def sync_industry(doc, method=None):
    # recursion koruması
    if frappe.flags.in_sync:
        return

    frappe.flags.in_sync = True

    # hangi taraftan geldiğini belirle
    if doc.doctype == "Industry Type":
        target_doctype = "CRM Industry"
        target_key = doc.industry
    elif doc.doctype == "CRM Industry":
        target_doctype = "Industry Type"
        target_key = doc.industry
    else:
        return

    # DELETE senaryosu
    if method == "after_delete":
        if frappe.db.exists(target_doctype, target_key):
            frappe.delete_doc(target_doctype, target_key, ignore_permissions=True)
        return

    # INSERT / UPDATE
    if frappe.db.exists(target_doctype, target_key):
        target_doc = frappe.get_doc(target_doctype, target_key)
    else:
        target_doc = frappe.new_doc(target_doctype)
        target_doc.industry = target_key  # sadece industry alanını set ediyoruz

    # loop engellemek için flag set et
    target_doc.flags.ignore_links = True
    target_doc.flags.ignore_mandatory = True

    target_doc.save(ignore_permissions=True)