# -*- coding: utf-8 -*-

{
    'name': 'Account Invoice Automatic Validation',
    'version': '1.0',
    'description': """
    This module adds a boolean field on invoice model allowing them
    to be included in the automatic validation process.
    """,
    'author': 'Moogah',
    'summary': 'Mark invoices for automatic validation process',
    'depends': [
        'account',
        'account_invoice_accountant_access'
    ],
    'data': [
        'data/auto_validation_cron.xml',
        'views/account_invoice_views.xml',
    ],
    'application': False,
}
