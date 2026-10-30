{
    "name": "parametrik_crm",
    "summary": "Short (1 phrase/line) summary of the module's purpose",
    "description": """
CRM especially for parametrik
    """,
    "author": "Hari Achmad",
    "website": "https://www.parametris.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/20.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Uncategorized",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["base", "crm"],
    # always loaded
    "data": [
        # 'security/ir.model.access.csv',
        "views/crm_lead_views.xml",
        "views/crm_lead_pipeline_no_create.xml",
        "views/crm_lead_required_field_views.xml",
        "views/crm_lead_view_form_approval.xml",
        "data/crm_lead_required_data.xml",
        "security/security.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
