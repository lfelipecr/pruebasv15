# -*- coding: utf-8 -*-
{
    'name': "l10n_cr_base",
    'summary': """
        Datos iniciales acordes a Costa Rica""",
    'description': """
        1. Métodos de pago.
        2. Impuestos.
        3. Código tipo de producto.
        4. Resolución.
        5. Condición de venta.
        6. Tipo de documento.
    """,
    'author': "Ruben Madrid",
    'company': '',
    'website': "",
    'category': 'Accounting/Accounting',
    'version': '14.0.2.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'uom','l10n_cr','l10n_cr_places'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/e_billing_security.xml',
        #DATA
        'data/type_document_data.xml',
        'data/autorization_document_data.xml',
        'data/account_journal_data.xml',
        'data/payment_method_data.xml',
        'data/code_type_product_data.xml',
        'data/reference_code_data.xml',
        'data/sale_conditions_data.xml',
        'data/economic_activity_data.xml',
        'data/account_tax_data.xml',
        'data/identification_type_data.xml',
        'data/reference_document_data.xml',
        'data/uom_category.xml',
        'data/uom_product_data.xml',

        #VISTAS NUEVAS
        'views/menu_views.xml',
        'views/type_document_views.xml',
        'views/payment_method_views.xml',
        'views/code_type_product_views.xml',
        'views/sale_condition_views.xml',
        'views/einvoice_sequence_views.xml',
        #'views/res_partner_exonerated_views.xml',
        'views/account_move_supplier_import_views.xml',

        ##VISTAS MODIFICADAS
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
        'views/account_tax_views.xml',
        'views/uom_views.xml',
        'views/account_payment_term_views.xml',
        'views/res_partner_views.xml',
        'views/res_places_views.xml',
        'views/account_journal_views.xml',

        'data/functions.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
