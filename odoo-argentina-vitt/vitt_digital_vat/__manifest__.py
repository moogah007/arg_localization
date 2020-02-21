# -*- coding: utf-8 -*-
{
    'name': "Digital VAT",
    'summary': """Digital VAT""",
    'description': """Digital VAT""",
    'author': "Moogah",
    'website': "http://www.Moogah.com",
    'category': 'Uncategorized',
    'version': '10.0.1.0.18',
    'depends': [
        'vitt_sales_reports',
        'account_document',
    ],
    'data': [
        'views/view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'application': True,
}
