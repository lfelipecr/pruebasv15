# -*- coding: utf-8 -*-
{
    'name': "l10n_cr_einvoice",
    'summary': """
        Facturación electrónica para Costa Rica""",
    'description': """
        1. Conversión de tipo cambio.
        2. Captura de datos según el documento de identidad.
        3. Envío comprobantes a hacienda (Incluido el PUNTO DE VENTA)
        
    """,
    'author': "Ruben Madrid",
    'company': '',
    'website': "",
    'category': 'Accounting/Accounting',
    'version': '15.0.5.0',
    # any module necessary for this one to work correctly
    'depends': ['base','account','l10n_cr_cabys','l10n_cr_base'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        #data
        'data/ir_cron.xml',
        'data/decimal_precision.xml',
        #views
        'views/res_currency_views.xml',
        'views/account_move_views.xml',
        'views/res_partner_exonerated_views.xml',
        'views/res_partner_views.xml',
        #wizard
        'wizard/account_move_reversal_view.xml',

        #report
        'reports/report_invoice.xml',
    ],
    'external_dependencies': {
        "python": [
            "pyOpenSSL",
            "phonenumbers",
            "xades",
            "xmlsig",
        ],
    },
}
