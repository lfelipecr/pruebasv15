# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _domain_activity(self):
        if self.env.company.activity_ids:
            return [("id", "in", self.env.company.activity_ids.ids)]

    # def _default_activity_id(self):
    #     company_id = self.company_id
    #     if not company_id:
    #         company_id = self.env.user.company_id
    #     if company_id.activity_default_id:
    #         return company_id.activity_default_id
    #     else:
    #         return False
        # TODO: check usage of next field

    reference_code_id = fields.Many2one(comodel_name="reference.code", readonly=True, copy=False, states={"draft": [("readonly", False)]}, string=u'Tipo nota crédito')
    payment_methods_id = fields.Many2one(comodel_name="payment.method", readonly=True, copy=False,  states={"draft": [("readonly", False)]}, string='Método de pago')
    # TODO: check usage of next field
    invoice_id = fields.Many2one(comodel_name="account.move", copy=False, readonly=True, states={"draft": [("readonly", False)]}, string="Comprobante referencia", )
    invoice_amount_text = fields.Char(compute="_compute_invoice_amount_text", copy=False)  # Monto en texto
    total_services_taxed = fields.Float(copy=False)
    total_services_exempt = fields.Float(copy=False)
    total_products_taxed = fields.Float(copy=False)
    total_products_exempt = fields.Float(copy=False)
    total_taxed = fields.Float(copy=False)
    total_exempt = fields.Float(copy=False)
    total_sale = fields.Float(copy=False)
    total_discount = fields.Float(copy=False)
    total_others = fields.Float(copy=False)
    activity_id = fields.Many2one(comodel_name="economic.activity", readonly=True, states={"draft": [("readonly", False)]}, string='Actividad económica',
                                  domain=_domain_activity)
    type_document_id = fields.Many2one(comodel_name='type.document', store=True, copy=False, string='Tipo comprobante') #TIPO DE DOCUMENTO
    type_document_sale_id = fields.Many2one(comodel_name='type.document', store=True, copy=False, string='Tipo comprobante',
                                            domain=[('in_sale', '=', True), ('active', '=', True)]) #TIPO DE DOCUMENTO EN VENTAS
    type_document_purchase_id = fields.Many2one(comodel_name='type.document', store=True, copy=False, string='Tipo comprobante',
                                                domain=[('in_purchase', '=', True), ('active', '=', True)]) #TIPO DE DOCUMENTO EN COMPRAS

    @api.onchange('type_document_sale_id', 'type_document_purchase_id')
    def _onchange_type_document_sale_purchase(self):
        self._validations_type_documents()
        if self.type_document_sale_id:
            self.type_document_id = self.type_document_sale_id
        elif self.type_document_purchase_id:
            self.type_document_id = self.type_document_purchase_id

        #Asignar actividad por defecto que tiene la compañia.
        self.activity_id = self.company_id.activity_default_id

    def _validations_type_documents(self):
        for record in self:
            if record.move_type in ('out_invoice', 'out_refund') and (record.type_document_sale_id or record.type_document_purchase_id):
                if record.move_type == 'out_invoice' and record.type_document_sale_id:
                    if record.type_document_sale_id.code in ('NC'):
                        raise ValidationError(_("No puede seleccionar el tipo de comprobante NOTA DE CRÉDITO para una factura de venta"))

                elif record.move_type == 'out_refund' and record.type_document_sale_id:
                    if record.type_document_sale_id.code not in ('NC'):
                        raise ValidationError(_("Solo puede seleccionar el tipo de comprobante NOTA DE CRÉDITO para una factura de venta rectificativa"))
                else:
                    record.type_document_id = record.type_document_sale_id

            elif record.move_type in ('in_invoice', 'in_refund'):
                if record.move_type == 'in_invoice' and record.type_document_purchase_id:
                    if record.type_document_purchase_id.code in ('NC'):
                        raise ValidationError(_("No puede seleccionar el tipo de comprobante NOTA DE CRÉDITO para una factura de compra"))
                elif record.move_type == 'in_refund':
                    if record.type_document_purchase_id:
                        if record.type_document_purchase_id.code not in ('NC'):
                            raise ValidationError(_("Solo puede seleccionar el tipo de comprobante NOTA DE CRÉDITO para una factura de compra rectificativa"))
                else:
                    record.type_document_id = record.type_document_purchase_id

            else:
                record.type_document_id = False
