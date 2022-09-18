# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, datetime

class PosPayent(models.Model):
    _inherit = 'pos.payment'

    is_other_currency = fields.Boolean('Pago en otra moneda') #add 17-08-2022
    amount_currency = fields.Float(string='Monto divisa') #add 17-08-2022
    amount_currency_real = fields.Float(string='Monto divisa real') #add 17-08-2022
    currency_other_id = fields.Many2one('res.currency', string='Moneda') #add 17-08-2022
    change_rate = fields.Float(string='Tipo de cambio') #add 17-08-2022






