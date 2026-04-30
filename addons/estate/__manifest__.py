{
    'name': 'Real Estate',
    'version': '16.0.1.0.0',
    'category': 'Real Estate',
    'summary': 'Manage real estate properties, offers, and sales',
    'author': 'Maghan Das',
    'depends': ['base'],           # 'base' is always required — it's Odoo's core
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_type_views.xml',
        'views/estate_property_views.xml',
        'views/estate_menus.xml',
    ],
    'installable': True,
    'application': True,           # Shows as a top-level app in the menu
    'license': 'LGPL-3',
}







