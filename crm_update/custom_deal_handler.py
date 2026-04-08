import frappe

def update_customer_crm_lead(doc, method):
    """Ensure crm_deal field is set and set custom_crm_lead and customer_name from Deal"""
    try:
        frappe.log_error(f"Hook called for customer: {doc.name}, crm_deal: {doc.crm_deal}", "CRM Update Hook")
        
        # If crm_deal is not set, we can't do anything
        #if not doc.crm_deal:
        #   frappe.log_error(f"No crm_deal for customer: {doc.name}", "CRM Update Hook")
        #   return
        
        # Get the Deal document
        deal = frappe.get_doc("CRM Deal", doc.crm_deal)
        frappe.log_error(f"Deal found: {deal.name}, Lead Name: {deal.lead_name}", "CRM Update Hook")
        print(f"Deal found: {deal.name}, Lead Name: {deal.deal_name}, company_name: {deal.company_name}")
        
        # Set custom_crm_lead to the deal name
        doc.crm_deal  = deal.name
        
        # Set customer_name to Deal's company name
        if deal.company_name:
            frappe.log_error(f"Setting customer_name to: {deal.company_name}", "CRM Update Hook")
            doc.customer_name = deal.company_name
        else:
            frappe.log_error(f"No company name found for deal: {doc.crm_deal}", "CRM Update Hook")
            
    except Exception as e:
        frappe.log_error(f"Error in update_customer_crm_lead: {str(e)}", "CRM Update Hook Error")