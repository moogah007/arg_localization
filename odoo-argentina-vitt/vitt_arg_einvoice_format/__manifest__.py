# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016  BACG S.A. de C.V.  (http://www.bacgroup.net)
#    All Rights Reserved.
#
##############################################################################
{
    'name': 'VITT ARG EInvoice Format ',
    'description': 'Formato de impresión para Facturas Argentina',
    'summary': 'Este app instala el formato para Impresión de Facturas según requerimientos de Argentina',
    'author': 'BacGroup, Moogah',
    'website': 'http://www.moogah.com',
    'version': '10.0.1.0.8',
    'license': 'Other proprietary',
    'maintainer': 'Moogah',
    'contributors': '',
    'category': 'Localization',
    'depends': [
        'account',
        'l10n_ar_afipws_fe',
        'account_document',
    ],
    'data': ['views/views.xml'],
}
