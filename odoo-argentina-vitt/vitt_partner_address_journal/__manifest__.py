# -*- coding: utf-8 -*-
{
    'name': "Partner Address in Jornal",
    'summary': """Partner Address Jornal""",
    'description': """Campo adicional de partner en Diarios de Ventas""",
    'author': "Moogah",
    'website': "http://www.Moogah.com",
    'category': 'Uncategorized',
    'version': '10.0.1.0.1',
    'depends': [
        'vitt_arg_einvoice_format',
        'account',
    ],
    'data': [
        'views/view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'application': True,
}
