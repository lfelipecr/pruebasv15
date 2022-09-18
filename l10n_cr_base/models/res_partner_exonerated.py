# -*- coding: utf-8 -*-

from odoo import _, fields, models, api
from odoo.exceptions import ValidationError
import requests
from datetime import datetime, date
from .. import apii
class ResPartnerExonerated(models.Model):
    _name = "res.partner.exonerated"
    _description = 'Adicionales para Cliente con exoneración'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    #_rec_name = 'numero_documento'

    partner_id = fields.Many2one('res.partner', string='Cliente')
    vat = fields.Char('Identificación')
    numero_documento = fields.Char(string='Número de documento')
    porcentaje_exoneracion = fields.Float('Porcentaje de exoneración')
    cabys_ids = fields.Many2many('cabys', string='Cabys')
    tipo_documento = fields.Many2one('autorization.document', string='Tipo de documento')
    fecha_emision = fields.Datetime('Fecha emisión')
    fecha_vencimiento = fields.Datetime('Fecha vencimiento')
    institucion = fields.Char(string='Institución')
    date_issue = fields.Date()
    date_expiration = fields.Date()



    def search_exoneration(self):
        res = {}
        if self.numero_documento:
            data = apii.customer_exonerated.find_data(self)
            if 'numero_documento' in data:
                self.sudo().write(data)
                res['warning'] = {'title': _('Bien!'), 'message': _('Datos encontrados!')}
                return res

    @api.onchange('fecha_emision')
    def _onchange_fecha_emision(self):
        if self.fecha_emision:
            self.date_issue = self.fecha_emision.date()

    @api.onchange('fecha_vencimiento')
    def _onchange_fecha_vencimiento(self):
        if self.fecha_vencimiento:
            self.date_expiration = self.fecha_vencimiento.date()

    def name_get(self):
        res = []
        for record in self:
            name = record.numero_documento
            if record.partner_id:
                name = name + ' / ' + record.partner_id.name
            res.append((record.id, name))
        return res