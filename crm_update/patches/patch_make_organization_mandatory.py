import frappe

def execute():
    """
    CRM Lead doctype'ındaki 'organization' alanını zorunlu yapar.
    Standart alan için DocField objesi üzerinden reqd=1 olarak set edilir.
    """
    try:
        # DocField objesini al
        df = frappe.get_doc("DocField", {"parent": "CRM Lead", "fieldname": "organization"})
        df.reqd = 1
        df.save()
        print("✅ CRM Lead.organization alanı artık zorunlu (standart field üzerinden).")
    except frappe.DoesNotExistError:
        print("⚠ CRM Lead.organization alanı bulunamadı!")