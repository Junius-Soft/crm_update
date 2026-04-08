import frappe


# hooks.py'ın beklediği liste (Hata almamak için şart)
CRM_DOCTYPES = ["CRM Lead", "CRM Deal", "CRM Note", "CRM Task", "CRM Organization", "CRM Contact"]

def get_user_sales_users(user):
    # Manager'ın ağaçtaki yerini bul (SQL çıktınızdaki 48-53 aralığı)
    manager_info = frappe.db.get_value("Sales Person", {"custom_user_link": user}, ["lft", "rgt"], as_dict=True)
    if not manager_info:
        return [user]

    # Alt ekibi (kendisi dahil) bul
    subordinates = frappe.get_all(
        "Sales Person",
        filters={"lft": [">=", manager_info.lft], "rgt": ["<=", manager_info.rgt]},
        pluck="custom_user_link"
    )
    return list(set(filter(None, subordinates)))

def get_permission_query_conditions(user, doctype=None):
    if not user:
        user = frappe.session.user

    # Admin veya System Manager her şeyi görsün
    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return ""

    users = get_user_sales_users(user)
    if not users:
        return "1=0"

    user_list_str = ", ".join([frappe.db.escape(u) for u in users])

    # Call Log, Note ve Task için ortak filtreleme mantığı
    target_doctypes = [
        "CRM Note", "FCRM Note", 
        "CRM Task", "FCRM Task", 
        "CRM Call Log", "FCRM Call Log",
        "CRM Organization", "FCRM Organization",
        "CRM Contact", "FCRM Contact"
    ]

    if doctype in target_doctypes:
        # Bu kayıtlar hem sahibi (owner) hem de oluşturan/değiştiren üzerinden filtrelenir
        return f"(`tab{doctype}`.owner IN ({user_list_str}) OR `tab{doctype}`.modified_by IN ({user_list_str}))"
    
    # Lead, Deal vb. için standart owner filtresi
    return f"`tab{doctype}`.owner IN ({user_list_str})"




def crm_filter_query(doctype, filters, user):
    if not user: user = frappe.session.user
    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return

    users = get_user_sales_users(user)
    if not users: return

    # Filtre yapısı liste veya dict olabilir, ikisini de kapsayalım
    if isinstance(filters, list):
        filters.append([doctype, "owner", "in", users])
    elif isinstance(filters, dict):
        filters["owner"] = ["in", users]