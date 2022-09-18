# -*- coding: utf-8 -*-

from odoo import _, fields, models, api
from odoo.exceptions import ValidationError
import requests
from datetime import datetime, date, timedelta
from .. import apii
class ResPartnerExonerated(models.Model):
    _name = "res.partner.exonerated"
    _description = 'Adicionales para Cliente con exoneración'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    #_rec_name = 'numero_documento'

    partner_id = fields.Many2one('res.partner', string='Cliente')
    vat = fields.Char('Identificación')
    numero_documento = fields.Char(string='Número de documento')
    porcentaje_exoneracion = fields.Integer('Porcentaje de exoneración')
    cabys_ids = fields.Many2many('cabys', string='Cabys')
    tipo_documento = fields.Many2one('autorization.document', string='Tipo de documento')
    fecha_emision = fields.Datetime('Fecha emisión')
    fecha_vencimiento = fields.Datetime('Fecha vencimiento')
    institucion = fields.Char(string='Institución')
    date_issue = fields.Char()
    date_expiration = fields.Char()

    tax_sale_id = fields.Many2one('account.tax', string='Impuesto Exoneración')


    def search_exoneration(self):
        res = {}
        if not self.partner_id:
            raise ValidationError(_("Seleccione primero un cliente."))
        if self.numero_documento:
            data = apii.customer_exonerated.find_data(self)
            if 'numero_documento' in data:
                self.sudo().write(data)
                res['warning'] = {'title': _('Bien!'), 'message': _('Datos encontrados!')}
                return res

    @api.onchange('porcentaje_exoneracion')
    def _onchange_porcentaje_exoneracion(self):
        for record in self:
            if record.porcentaje_exoneracion:
                tax = self.env['account.tax'].sudo().search([('percentage_exoneration', '=', record.porcentaje_exoneracion),
                                                             ('is_exoneration', '=', True),
                                                             ('type_tax_use', '=', 'sale'),
                                                             ('company_id', '=', self.env.company.id)], limit=1)
                if tax:
                    record.tax_sale_id = tax

    @api.onchange('fecha_emision')
    def _onchange_fecha_emision(self):
        if self.fecha_emision:
            self.date_issue = (self.fecha_emision - timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M:%S')

    @api.onchange('fecha_vencimiento')
    def _onchange_fecha_vencimiento(self):
        if self.fecha_vencimiento:
            self.date_expiration = (self.fecha_vencimiento - timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M:%S')

    def name_get(self):
        res = []
        for record in self:
            name = record.numero_documento or '-'
            if record.partner_id:
                name = name + ' / ' + record.partner_id.name
            res.append((record.id, name))
        return res

    @api.model
    def _search_active(self, partner):
        exists = self.env['res.partner.exonerated']
        if partner:
            exoneration_ids = self.env['res.partner.exonerated'].sudo().search([('partner_id','=',partner.id), ('date_expiration','!=',False)])
            if exoneration_ids:
                for e in exoneration_ids:
                    d1 = (e.fecha_vencimiento - timedelta(hours=5)).date()
                    d2 = datetime.now().date()
                    if d1 >= d2:
                        exists += e
                #exists = exoneration_ids.filtered(lambda e:e.date_expiration >= datetime.now().date())

        return exists


