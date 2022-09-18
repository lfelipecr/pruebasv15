# -*- coding: utf-8 -*-
{
    'name': "l10n_cr_epos",
    'summary': """
        Facturación electrónica Punto de Venta para Costa Rica""",
    'description': """
        1. Captura de datos según el documento de identidad.
        2. Envío comprobantes a hacienda (Incluido el PUNTO DE VENTA)

    """,
    'author': "Ruben Madrid",
    'company': '',
    'website': "",
    'category': 'Sales/Point of Sale',
    'version': '15.0.1.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'point_of_sale', 'l10n_cr_cabys', 'l10n_cr_base','l10n_cr_einvoice'],
    # always loaded
    'data': [
        # views
        'views/pos_config_views.xml',
        'views/pos_payment_method_views.xml',
        'views/pos_payment_views.xml',
        'views/pos_order_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            #CSS
            'l10n_cr_epos/static/src/css/styles.css',
            #SWAL
            'l10n_cr_epos/static/src/adds/swal.min.js',
            #MODELS POS
            'l10n_cr_epos/static/src/js/ModelFields.js',
            'l10n_cr_epos/static/src/js/ClientDetailsEdit.js',
            'l10n_cr_epos/static/src/js/ModelOrder.js',
            'l10n_cr_epos/static/src/js/ModelPayment.js',
            'l10n_cr_epos/static/src/js/ModelPaymentScreen.js',
        ],
        'web.assets_qweb': [
            'l10n_cr_epos/static/src/xml/ClientDetailsEdit.xml',
            'l10n_cr_epos/static/src/xml/OrderReceipt.xml',
            'l10n_cr_epos/static/src/xml/PaymentScreen.xml',
        ],
    },
}
