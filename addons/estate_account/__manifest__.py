{
    'name': 'Real Estate - Accounting',
    'version': '16.0.1.0.0',
    'category': 'Real Estate',
    'summary': 'Automatic invoice generation when a property is sold',
    'depends': ['estate', 'account'],
    'data': [
        'views/estate_property_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}

# Why depends: ['estate', 'account']?
# estate — we're extending it, so it must be installed first
# account — we're creating account.move (invoice) records, so accounting must exist

