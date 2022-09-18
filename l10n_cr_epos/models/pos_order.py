# -*- coding: utf-8 -*-
import base64
import json
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

from ... import l10n_cr_einvoice
einv_billing = l10n_cr_einvoice.e_billing
from .. import e_billing

STATE_MAIL = [("not_email", "Sin cuenta de correo"),
              ("sent", "Enviado"),
              ("error", "Error de envío")
              ]

class PosOrder(models.Model):
    _name = 'pos.order'
    _inherit = ['pos.order','mail.thread', 'mail.activity.mixin']

    #FACTURACIÓN ELECTRÓNICA
    code_document_type = fields.Selection([('FE','E-Facturación'),('TE','E-Ticket'),('NC','E-Nota crédito')], string='E-Código')
    type_document_id = fields.Many2one(comodel_name='type.document', store=True, copy=False, string='Tipo comprobante',
                                            domain=[('in_sale', '=', True), ('active', '=', True)])  # TIPO DE DOCUMENTO EN VENTAS
    electronic_sequence = fields.Char(readonly=True, copy=False, string='Consecutivo', tracking=True)
    number_electronic = fields.Char(copy=False, index=True, readonly=True, string=u'N°Electrónico/Clave', tracking=True)  # Clave
    date_issuance = fields.Char(copy=False, readonly=True, string=u'Fecha envío')
    state_send_customer = fields.Selection(selection=einv_billing.utils.STATE_INVOICE_CUSTOMER,string='Estado en hacienda', copy=False, readonly=True, tracking=True)#ESTADO usado para clientes
    xml_invoice = fields.Binary(copy=False, tracking=True, string=u'XML Envío')  # XML DE CLIENTES Y PROVEEDORES AL ENVIAR
    xml_invoice_name = fields.Char(copy=False, tracking=True, string=u'XML Envío')  # NOMBRE XML DE CLIENTES Y PROVEEDORES AL ENVIAR
    xml_response = fields.Binary(copy=False, tracking=True, string='XML Respuesta')
    xml_response_name = fields.Char(copy=False, tracking=True, string='XML Respuesta')
    to_send = fields.Boolean(string='Envio a Hacienda')
    state_email = fields.Selection(STATE_MAIL, string="Estado email", copy=False, tracking=True)
    currency_rate_usd_crc = fields.Float(compute='_compute_currency_rate_usd_crc', store=True) #TIPO DE CAMBIO
    #NOTA DE CRÉDITO
    is_return = fields.Boolean(string='Devolución')
    order_id = fields.Many2one("pos.order", copy=False, readonly=True, states={"draft": [("readonly", False)]}, string="Comprobante origen")
    reference_code_id = fields.Many2one('reference.code', string="Código de referencia", required=False)

    #GUARDAR MONTOS EN OTRA MONEDA
    amount_paid_currency = fields.Float('Monto pagado real', compute='_compute_amount_paid_currency', store=True)
    paid_other_form = fields.Selection([('no', 'No'), ('total', 'Pago total'), ('partial', 'Pago parcial')], string='Pago en otra moneda', default='no')
    other_currency_id = fields.Many2one('res.currency')


    @api.depends('currency_id', 'currency_rate')
    def _compute_currency_rate_usd_crc(self):
        for record in self:
            currency_rate_usd_crc = 1
            if record.company_id.currency_id != record.currency_id:
                currency_rate_usd_crc = record.currency_id._convert(1, record.company_id.currency_id, record.company_id, record.date_order.date() or datetime.now().date())

            record.currency_rate_usd_crc = currency_rate_usd_crc


    @api.model
    def search_order(self, uid):
        order = self.env['pos.order'].search([('pos_reference', 'like', uid)])
        if order:
            value = {
                "number_electronic": order.number_electronic,
                "electronic_sequence": order.electronic_sequence,
                "code_document_type": order.type_document_id.code,
            }
            return json.dumps(value)
        else:
            return False


    def _get_type_documento(self, ui_order, vals):

        if 'is_return' in ui_order:
            if ui_order['is_return']:
                code_document_type = 'NC'
            elif not ui_order.get('partner_id'):
                code_document_type = 'TE'
            else:
                code_document_type = 'FE'
        else:
            if not ui_order.get('partner_id'):
                code_document_type = 'TE'
            else:
                code_document_type = 'FE'

        type_document_id = self.env['type.document'].sudo().search([('code', '=', code_document_type)])

        return code_document_type, type_document_id

    #vals['lines'] => lines == lines[0][2]['refunded_orderline_id']

    @api.model
    def _order_fields(self, ui_order):
        vals = super(PosOrder, self)._order_fields(ui_order)
        session = self.env['pos.session'].sudo().browse(vals.get('session_id'))
        vals['to_send'] = ui_order.get('to_send')

        _logger.info("POS - Enviar a hacienda ? %s " % (vals['to_send']))

        if ui_order.get('to_send') or not session.config_id.show_send_hacienda and session:
            vals['to_send'] = True
            code_document_type, type_document_id = self._get_type_documento(ui_order, vals)
            vals["code_document_type"] = code_document_type
            vals["type_document_id"] = type_document_id.id if type_document_id else False
            vals["electronic_sequence"] = ui_order.get("electronic_sequence")
            vals["number_electronic"] = ui_order.get("number_electronic")
            vals["is_return"] = ui_order.get("is_return")
            if 'order_id' in ui_order:
                if ui_order.get('order_id') != False:
                    vals['order_id'] = int(ui_order['order_id'])
            _logger.info("POS - Código de tipo de documento %s " % (vals['code_document_type']))
        else:
            vals['to_send'] = False

        return vals

    @api.model
    def create(self, values):
        session = self.env['pos.session'].sudo().browse(values['session_id'])
        values = super()._complete_values_from_session(session, values)
        if values["to_send"] or not session.config_id.show_send_hacienda and session:
            electronic_sequence, number_electronic = self._create_e_sequence(values["code_document_type"], session)
            values["electronic_sequence"] = electronic_sequence
            values["number_electronic"] = number_electronic
        else:
            values['to_send'] = False

        return super().create(values)

    def _create_e_sequence(self, code_document_type, session):
        if not session:
            session = self.env['pos.session'].sudo().browse(self.session_id)

        if not code_document_type:
            code_document_type = self.code_document_type

        electronic_sequence = self.electronic_sequence
        if not session.config_id.lines_sequences and self.used_invoice:
            raise UserError(_("El terminal está configurado para facturación. Configure correctamente las secuencias."))

        if not electronic_sequence:
            line_seq = session.config_id.lines_sequences.filtered(lambda s: s.type_document_id.code == code_document_type)
            next_number = line_seq.e_sequence_id.next_by_id()
            electronic_sequence = einv_billing.utils.compute_full_sequence(branch=session.config_id.sucursal,
                                                                           terminal=session.config_id.terminal,
                                                                           doc_type_code=line_seq.type_document_id.code_hacienda,
                                                                           sequence=next_number)

        number_electronic = self.number_electronic
        if not number_electronic:
            number_electronic = einv_billing.utils.get_number_electronic(issuer=self.env.company, full_sequence=electronic_sequence)

        _logger.info('POS - Secuencia electrónica : %s' % (electronic_sequence))
        _logger.info('POS - Número electrónico : %s' % (number_electronic))

        return electronic_sequence, number_electronic

    def _create_xml(self):
        """Crear xml de envío normal"""

        self.date_issuance = einv_billing.utils.get_time_cr()
        xml_raw = einv_billing.generate_xml.gen(self)
        xml_signed = einv_billing.utils.sign_xml(cert=self.company_id.signature, pin=self.company_id.e_pin, xml=xml_raw)
        self.xml_invoice_name = "{}_{}.xml".format(self.type_document_id.code, self.number_electronic)
        self.xml_invoice = base64.encodebytes(xml_signed)
        _logger.debug("E-Factura firmada y creada : {}".format(self.xml_invoice_name))

    def _create_xml_4_3_pos(self):
        """Creación de XML """
        for record in self:
            if record.config_id.used_invoice:
                if record.to_send and record.config_id.used_invoice:  # => El comprobante se creará siempre y cuando tenga esta opción activa
                    try:
                        process, message = e_billing.bridge._validations_e_pos(record)  # Validaciones antes de publicar la factura
                        if process:
                            record._create_xml()
                        else:
                            UserError(_(message))
                    except Exception as e:
                        raise ValidationError(_("Advertencia: %s", e))
                else:
                    _logger.info("Comprobante %s no se enviará a hacienda." % (record.name))
            else:
                _logger.info("El terminal no está configurado para configuración electrónica")

    @api.model
    def generate_xml(self):
        for record in self:
            if not record.xml_invoice:
                record._create_xml_4_3_pos()

    def _send_xml(self):
        """Envio de xml a hacienda"""
        response_json = einv_billing.api.send_xml(
            client_id=self.company_id.e_environment,
            token=einv_billing.auth._get_token_by_company(self.company_id),
            xml=base64.b64decode(self.xml_invoice),
            date=self.date_issuance,
            electronic_number=self.number_electronic,
            issuer=self.company_id,
            receiver=self.partner_id,
        )
        return response_json

    def sent_to_hacienda(self):
        for record in self:
            if record.to_send and record.type_document_id and record.electronic_sequence and record.number_electronic:
                _logger.info("POS - Envio Hacienda de orden N°: %s", record.name)
                if not record.xml_invoice:
                    record.sudo().generate_xml()

                einv_billing.utils._evalue_xml_false(record.xml_invoice)

                response_json = record.sudo()._send_xml()
                response_status = response_json.get("status")
                response_text = response_json.get("text")
                if 200 <= response_status <= 299:
                    record.state_send_customer = 'procesando'
                    continue
                else:
                    message_body = (
                        "<p><b>Código Estado: </b> {}"
                        "<br/><b>Mensaje:</b> {}"
                        "</p>".format(response_status, response_text))
                    record.sudo().message_post(body=message_body, subtype_xmlid="mail.mt_note", message_type='comment')

                _logger.info('POS - Respuesta de hacienda: %s' % (response_text))

    def get_from_hacienda(self):
        for record in self:
            if record.state_send_customer in ('recibido', 'procesando'):
                _logger.info("POS - Consulta Hacienda de orden N°: %s", record.name)
                response_json = einv_billing.api.query_document(
                    clave=record.number_electronic,
                    token=einv_billing.auth._get_token_by_company(record.company_id),
                    client_id=record.company_id.e_environment,
                )
                status = response_json.get("status")  # Codigo de estado
                state = response_json.get("ind-estado")  # Estado
                if status == 400:
                    message_body = (
                        "<p><b>Código Estado: </b> {}"
                        "<br/><b>Mensaje:</b> {}"
                        "</p>".format(status, state))
                    record.message_post(body=message_body, subtype_xmlid="mail.mt_note", message_type='comment')
                else:
                    record.state_send_customer = state
                    record.xml_response_name = "RPTA_{}.xml".format(record.number_electronic)
                    record.xml_response = response_json.get("respuesta-xml")

                    if record.state_send_customer == 'aceptado' and record.company_id.send_mail_to_customer:
                        _logger.info('POS - Envío de email - Orden: %s' % (record.name))
                        pass
                        #record._send_mail_customer()

    def _send_mail_customer(self):
        self.ensure_one()
        if not self.xml_comprobante or not self.xml_respuesta_tributacion:
            raise ValidationError(_("Asegúrese de tener los xml de envío y respuesta de hacienda."))

        if self.partner_id and self.partner_id.email:
            email_values = {}
            email_template = self.env.ref("l10n_cr_pos.email_template_pos_invoice", False)
            if not email_template:
                _logger.info("No existe template para envío de email")

            if self.partner_id and self.partner_id.email:
                ir_attachment = self.env['ir.attachment'].sudo()
                if self.partner_id and self.partner_id.email:
                    email_template.attachment_ids = False
                    if self.xml_invoice:
                        attachment_invoice = ir_attachment.search([('res_model', '=', 'pos.order'), ('res_id', '=', self.id),
                                                                   ('res_field', '=', 'xml_invoice'), ('mimetype', '=', 'text/plain')], limit=1)
                        if not attachment_invoice:
                            attachment_invoice = ir_attachment.create({
                                'datas': self.xml_invoice,
                                'name': self.xml_invoice_name,
                                'mimetype': 'text/plain',
                                'res_model': 'pos.order',
                                'res_id': self.id,
                                'res_field': 'xml_invoice'
                            })

                        email_template.attachment_ids += attachment_invoice

                    if self.xml_response:
                        attachment_response = ir_attachment.search([('res_model', '=', 'pos.order'), ('res_id', '=', self.id),
                                                                    ('res_field', '=', 'xml_response'), ('mimetype', '=', 'text/plain')], limit=1)
                        if not attachment_response:
                            attachment_response = self.env['ir.attachment'].create({
                                'datas': self.xml_response,
                                'name': self.xml_response_name,
                                'mimetype': 'text/plain',
                                'res_model': 'pos.order',
                                'res_id': self.id,
                                'res_field': 'xml_response'
                            })

                        email_template.attachment_ids += attachment_response
                        email_template.with_context(type="binary", default_type="binary").send_mail(self.id, raise_exception=False, force_send=True)

                    if email_template.attachment_ids:
                        for att in email_template.attachment_ids:
                            email_template.sudo().write({'attachment_ids': [(3, att.id)]})

            email_template.sudo().send_mail(self.id, force_send=True, email_values=email_values, notif_layout='mail.mail_notification_light')
            self.state_email = "sent"

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        values = super(PosOrder, self)._payment_fields(order, ui_paymentline)

        def _get_amount_currency(ui_paymentline):
            amount_currency = 0.0
            if ui_paymentline['is_other_currency']:
                amount = ui_paymentline['amount']
                amount_currency = ui_paymentline['amount_currency_real'] * amount / (ui_paymentline['amount_currency_real'] * float(ui_paymentline['change_rate']))
            return amount_currency

        values['is_other_currency'] = ui_paymentline['is_other_currency'] if 'is_other_currency' in ui_paymentline else False
        values['amount_currency'] = _get_amount_currency(ui_paymentline)
        values['amount_currency_real'] = ui_paymentline['amount_currency_real'] if 'amount_currency_real' in ui_paymentline else 0.0
        values['currency_other_id'] = ui_paymentline['currency_other_id'] if 'currency_other_id' in ui_paymentline else False
        values['change_rate'] = ui_paymentline['change_rate'] if 'change_rate' in ui_paymentline else 0.0
        return values


    @api.depends('payment_ids')
    def _compute_amount_paid_currency(self):
        for record in self:
            amount_paid_currency = 0.0
            paid_other_form = 'no'
            currency_other_id = False
            if record.payment_ids:
                if record.is_return:
                    payment_ids = record.payment_ids.filtered(lambda pay: pay.amount < 0)
                else:
                    payment_ids = record.payment_ids.filtered(lambda pay: pay.amount > 0)

                payments_other_currency = record.payment_ids.filtered(lambda p: p.is_other_currency == True)
                if payments_other_currency:
                    for pay in payments_other_currency:
                        amount_paid_currency += pay.amount_currency

                    if len(payments_other_currency) == len(payment_ids):
                        paid_other_form = 'total'
                    else:
                        paid_other_form = 'partial'

                    currency_other_id = payments_other_currency[0].currency_other_id

            record.amount_paid_currency = amount_paid_currency
            record.paid_other_form = paid_other_form
            record.other_currency_id = currency_other_id
