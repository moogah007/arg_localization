# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016  BACG S.A. de C.V.  (http://www.bacgroup.net)
#    All Rights Reserved.
#
##############################################################################
{
    'name': 'History Checks Reports V2',
    'description': 'Adds History Checks Reports for Checks V2',
    'summary': 'Este app instala el reporte de Historia de Cheques con soporte para la nueva versión de Cheques',
    'author': "Moogah",
    'website': "http://www.Moogah.com",
    'version': '10.0.2.0.2',
    'license': 'Other proprietary',
    'maintainer': 'Osvaldo Jorge Gentile',
    'contributors': '',
    'category': 'Localization',
    'depends': ['account', 'account_check','vitt_cashin_cashout'],
    'data': [
        'data/issue.checks.states.csv',
        'data/third.checks.states.csv',
        'views/views.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'application': True,
}
