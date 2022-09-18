# -*- coding: utf-8 -*-
{
    'name': "l10n_cr_cabys",
    'summary': """
        CABYS""",
    'description': """
        1. Catálogo de bienes y servicios.

    """,
    'author': "Ruben Madrid",
    'company': '',
    'website': "",
    'category': 'Accounting/Accounting',
    'version': '15.0.1.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'l10n_cr_base'],
    # always loaded
    'data': [
        # security
        "security/ir.model.access.csv",
        # data
        "data/functions.xml",
        "data/function_update_tax_ids.xml",
        "data/ir_cron.xml",
        # views
        'views/cabys.xml',
        'views/product_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
