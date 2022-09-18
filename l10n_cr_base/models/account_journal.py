# -*- coding: utf-8 -*-

from odoo import api, models, fields

class AccountJournal(models.Model):
    _inherit = "account.journal"

    e_invoice_check = fields.Boolean('Usado en facturación')
    to_send = fields.Boolean('Enviar a hacienda')



