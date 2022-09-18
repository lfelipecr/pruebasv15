# -*- coding: utf-8 -*-
# from odoo import http


# class L10nCrEpos(http.Controller):
#     @http.route('/l10n_cr_epos/l10n_cr_epos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_cr_epos/l10n_cr_epos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_cr_epos.listing', {
#             'root': '/l10n_cr_epos/l10n_cr_epos',
#             'objects': http.request.env['l10n_cr_epos.l10n_cr_epos'].search([]),
#         })

#     @http.route('/l10n_cr_epos/l10n_cr_epos/objects/<model("l10n_cr_epos.l10n_cr_epos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_cr_epos.object', {
#             'object': obj
#         })
