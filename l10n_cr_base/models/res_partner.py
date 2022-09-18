# -*- coding: utf-8 -*-
from functools import partial

from odoo import _, fields, models, api
from odoo.exceptions import ValidationError, UserError
import requests
from datetime import datetime, date
import re
import logging
_logger = logging.getLogger(__name__)

NIF_API = "https://api.hacienda.go.cr/fe/ae"

class PartnerElectronic(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    commercial_name = fields.Char()
    identification_id = fields.Many2one(comodel_name="identification.type",string="Tipo identificación",)
    payment_methods_id = fields.Many2one(comodel_name="payment.method",string='Método de pago')
    vat = fields.Char(string=u'N°Documento', help="Número de identificación")

    #Exoneración
    #has_exoneration = fields.Boolean(string='Tiene exoneración')
    #exoneration_lines = fields.One2many('res.partner.exonerated','partner_id')


    _sql_constraints = [
        (
            "vat_unique",
            "Check(1=1)",
            _("No pueden existir dos clientes/proveedores con el mismo número de identificación"),
        )
    ]

    @api.constrains('vat')
    def _check_unique_vat(self):
        for partner in self:
            if partner.vat:
                p_find = self.sudo().search([('vat','=',partner.vat),('parent_id','=',False),('vat','=',False)])
                if p_find and not partner.parent_id and p_find != partner:
                    raise ValidationError(_(u'No pueden existir dos clientes/proveedores con el mismo número de identificación'))



    # def open_partner_exonerated(self):
    #     id = None
    #     partner_tax = self.env['res.partner.tax'].sudo().search(['|', ('partner_id', '=', self.id), ('vat', '=', self.vat)])
    #     if partner_tax:
    #         id = partner_tax.id
    #     view = {
    #         'type': 'ir.actions.act_window',
    #         'name': u'Cliente exonerado',
    #         'view_mode': 'form',
    #         'res_model': 'res.partner.tax',
    #         'res_id': id,
    #         'target': 'current',
    #         'context': {
    #             'default_partner_id': self.id,
    #             'default_vat': self.vat,
    #             'form_view_initial_mode': 'edit',
    #         }
    #     }
    #
    #     return view

    @api.onchange("vat", "identification_id")
    def _verify_vat_and_identification_id(self):  # TODO in res.company
        if not (self.identification_id and self.vat) or self.env.company.country_id.code != 'CR':
            return
        self.vat = re.sub(r"[^\d]", "", self.vat)
        lens = {
            "01": (9, 9),
            "02": (10, 10),
            "03": (11, 12),
            "04": (9, 9),
            "05": (20, 20),
        }
        limits = lens[self.identification_id.code]
        if not limits[0] <= len(self.vat) <= limits[1]:
            raise UserError(
                _("VAT must be between {} and {} (inclusive) chars long").format(
                    limits[0],
                    limits[1],
                )
            )

    @api.onchange("vat")
    def _get_name_from_vat(self):
        if not self.vat or self.env.company.country_id.code != 'CR':
            return

        try:
            response = requests.get(NIF_API, params={"identificacion": self.vat})
            if response.status_code == 200:
                response_json = response.json()
                self.name = response_json["nombre"]
                self.identification_id = self.identification_id.search(
                    [("code", "=", response_json["tipoIdentificacion"])], limit=1
                )
                return
            elif response.status_code == 404:
                title = "El documento de identificacióm no fue encontrado"
                message = "El documento de identificación no está en la API"
            elif response.status_code == 400:
                title = "Error de API 400"
                message = "Solicitud incorrecta"
            else:
                title = "Error desconocido"
                message = "Error desconocido en la solicitud de API"
            return {
                "warning": {
                    "title": title,
                    "message": message,
                }
            }
        except Exception as e:
            _logger.info("Error en la conexión")
            pass
        else:
            pass