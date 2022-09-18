# -*- coding: utf-8 -*-
# from odoo import http


# class L10nCrAccounting(http.Controller):
#     @http.route('/l10n_cr_accounting/l10n_cr_accounting', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_cr_accounting/l10n_cr_accounting/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_cr_accounting.listing', {
#             'root': '/l10n_cr_accounting/l10n_cr_accounting',
#             'objects': http.request.env['l10n_cr_accounting.l10n_cr_accounting'].search([]),
#         })

#     @http.route('/l10n_cr_accounting/l10n_cr_accounting/objects/<model("l10n_cr_accounting.l10n_cr_accounting"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_cr_accounting.object', {
#             'object': obj
#         })
