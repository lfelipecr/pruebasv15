# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, date_utils, email_split, email_re, html_escape, is_html_empty
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
import base64
import json
import logging
_logger = logging.getLogger(__name__)

from .. import e_billing

class AccountMove(models.Model):
    _name = "account.move"
    _inherit = "account.move"

    @api.model
    def _get_default_journal(self):
        return super(AccountMove, self)._get_default_journal()

    journal_id = fields.Many2one('account.journal', string='Diario', required=True, readonly=True,states={'draft': [('readonly', False)]},
                                 check_company=True, domain="[('id', 'in', suitable_journal_ids)]", copy=False, default=_get_default_journal)
    exchange_rate = fields.Float(compute="_compute_exchange_rate", store=True, string="Tipo cambio")

    active = fields.Boolean(default=True, tracking=True)

    @api.depends("invoice_date", "company_id","currency_id")
    def _compute_exchange_rate(self):
        for record in self:
            if not record.invoice_date:
                record.invoice_date = date.today()
            crc_currency = self.env.ref("base.CRC")
            usd_currency = self.env.ref("base.USD")
            company_currency_id = record.company_currency_id
            invoice_currency_id = record.currency_id
            if company_currency_id != invoice_currency_id:
                record.exchange_rate = invoice_currency_id._convert(1, company_currency_id, record.company_id, record.invoice_date)
            else:
                record.exchange_rate = usd_currency._convert(1, crc_currency, record.company_id, record.invoice_date)


    #****************************************** Todo: FACTURACIÓN ELECTRÓNICA *************************************************
    type_document_received_id = fields.Many2one('type.document',copy=False, string='Documento recibido')
    electronic_sequence = fields.Char(readonly=True,copy=False,string='Consecutivo',tracking=True)
    number_electronic = fields.Char(copy=False,index=True,readonly=True, string=u'N°Electrónico/Clave',tracking=True) #Clave
    consecutive_number_receiver = fields.Char(copy=False,readonly=True,index=True,string='Consecutivo recibido', tracking=True)
    date_issuance = fields.Char(copy=False,readonly=True, string=u'Fecha envío')
    state_send_customer = fields.Selection(selection=e_billing.utils.STATE_INVOICE_CUSTOMER,string='Estado en hacienda', copy=False, readonly=True, tracking=True)#ESTADO usado para clientes
    state_send_supplier = fields.Selection(selection=e_billing.utils.STATE_INVOICE_SUPPLIER,string='Estado en hacienda', copy=False, readonly=True, tracking=True)#ESTADO  usado para proveedores
    state_selector_partner = fields.Selection(e_billing.utils.STATE_SELECTOR_PARTNER, string='Aceptar comprobante')#PROVEEDOR SELECCIONA ACEPTACIÓN
    xml_invoice = fields.Binary(copy=False, tracking=True,string=u'XML Envío') #XML DE CLIENTES Y PROVEEDORES AL ENVIAR
    xml_invoice_name = fields.Char(copy=False,  tracking=True,string=u'XML Envío') #NOMBRE XML DE CLIENTES Y PROVEEDORES AL ENVIAR
    xml_invoice_supplier_approval = fields.Binary(copy=False,string='XML Recepcionado') #XML RECIBIDOS DE PROVEEDORES
    xml_invoice_supplier_approval_name = fields.Char(copy=False,string='XML Recepcionado') #NOMBRE XML RECIBIDOS DE PROVEEDORES
    xml_response = fields.Binary(copy=False, tracking=True, string='XML Respuesta' )
    xml_response_name = fields.Char(copy=False, tracking=True, string='XML Respuesta' )
    amount_tax_electronic_invoice = fields.Monetary(readonly=True, string='Total impuesto e-factura', copy=False, tracking=True) #TOTAL IMPUESTO ELECTRÓNICO
    amount_tax_return_electronic_invoice = fields.Monetary(readonly=True, string='Impuesto devuelto e-factura ', copy=False, tracking=True) #TOTAL IMPUESTO ELECTRÓNICO
    amount_total_electronic_invoice = fields.Monetary(readonly=True, string='Total comprobante e-factura', copy=False, tracking=True) #TOTAL MONTO ELECTRÓNICO
    to_send = fields.Boolean('Enviar a Hacienda', copy=False)
    from_mail = fields.Boolean(string='Desde Email', copy=False,tracking=True, help='Proviene desde email')
    message_hacienda = fields.Text(string=u'Mensaje', copy=False, tracking=True)
    invoice_id = fields.Many2one("account.move",copy=False,readonly=True,states={"draft": [("readonly", False)]},string="Comprobante origen")
    sequence_eline_id = fields.Many2one('einvoice.sequence.lines',string='Secuencia utilizada', copy=False)

    partner_has_exoneration = fields.Boolean(string='Tiene exoneración')
    partner_exoneration_id = fields.Many2one('res.partner.exonerated', string='Exoneración')
    partner_exoneration_ids = fields.Many2many('res.partner.exonerated', string='Exoneraciones')
    partner_exoneration_info = fields.Text(string='Información')

    due_date = fields.Date(compute='compute_due_date')

    # ************************************* Todo: PROCESO DE FACTURACIÓN ELECTRÓNICA ********************
    def _post(self, soft=True):
        """Sobreescritura de método _POS() """
        response = super(AccountMove, self)._post(soft=True)
        self._create_xml_4_3() #Creación de xml al validar el comprobante
        return response

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        # Esto permite que el método de pago del cliente vaya en el comprobante.
        partner_has_exoneration = False
        partner_exoneration_ids = False
        partner_exoneration_id = False
        partner_exoneration_info = False
        if self.partner_id:
            if self.partner_id.payment_methods_id:
                self.payment_methods_id = self.partner_id.payment_methods_id

            if self.partner_id.has_exoneration:
                partner_has_exoneration = self.partner_id.has_exoneration
                partner_exoneration_ids = self.env['res.partner.exonerated'].sudo()._search_active(self.partner_id)

                if partner_exoneration_ids:
                    partner_exoneration_ids = partner_exoneration_ids
                    partner_exoneration_id = partner_exoneration_ids[0]
                    msg = 'Hay %s exoneracion(es) relacionada(s), la última con fecha de vencimiento : %s' % (len(partner_exoneration_ids),
                                                                                                          partner_exoneration_ids[0].date_expiration)
                    partner_exoneration_info= msg

        self.partner_has_exoneration = partner_has_exoneration
        self.partner_exoneration_ids = partner_exoneration_ids
        self.partner_exoneration_id = partner_exoneration_id
        self.partner_exoneration_info = partner_exoneration_info

        return res

    @api.depends('invoice_payment_term_id', 'invoice_date')
    def compute_due_date(self):
        for record in self:
            due_date = date.today()
            if record.invoice_date:
                invoice_date = record.invoice_date
            if not record.invoice_date:
                invoice_date = date.today()

            due_date = invoice_date

            if record.invoice_payment_term_id:
                days = record.invoice_payment_term_id.line_ids[0].days
                due_date = invoice_date + timedelta(days=days)

            record.due_date = due_date
            record.sudo().write({'invoice_date_due': due_date})
            a = 1

    def _create_xml(self):
        """Crear xml de envío normal"""
        self.date_issuance = e_billing.utils.get_time_cr()
        if not self.invoice_origin:
            self.invoice_origin = self.invoice_id.display_name
        xml_raw = e_billing.generate_xml.gen(self)
        xml_signed = e_billing.utils.sign_xml(cert=self.company_id.signature, pin=self.company_id.e_pin, xml=xml_raw)
        self.xml_invoice_name = "{}_{}.xml".format(self.type_document_id.code, self.number_electronic)
        self.xml_invoice = base64.encodebytes(xml_signed)
        _logger.debug("E-Factura firmada y creada : {}".format(self.xml_invoice_name))


    def _create_xml_receptor(self):
        """Crear xml de de envío como mensaje de receptor"""
        xml = e_billing.generate_xml.mensaje_receptor(
            electronic_number=self.number_electronic,
            issuer_vat=self.partner_id.vat,
            emition_date=self.date_issuance,
            message_type=self.state_selector_partner,
            message=e_billing.utils.STATE_SELECTOR_PARTNER_MESSAGE[self.state_selector_partner],
            receiver_vat=self.company_id.vat,
            receiver_sequence=self.electronic_sequence,
            amount_tax=self.amount_tax_electronic_invoice,
            amount_total=self.amount_total_electronic_invoice,
            activity_code=self.activity_id.code,
            tax_status="01",  # TODO check
        )
        xml_signed = e_billing.utils.sign_xml(
            cert=self.company_id.signature,
            pin=self.company_id.e_pin,
            xml=xml,
        )
        self.xml_invoice_name = "{}_{}.xml".format(self.type_document_id.code, self.number_electronic)
        self.xml_invoice = base64.encodebytes(xml_signed)
        _logger.debug("E-Factura firmada y creada : {}".format(self.xml_invoice_name))

    def _create_xml_4_3(self):
        """Creación de XML """
        for inv in self:
            if inv.to_send:# => El comprobante se creará siempre y cuando tenga esta opción activa
                try:
                    e_billing.utils._validations_e_invoice(inv)  # Validaciones antes de publicar la factura
                    # Ir a método para crear la secuencia.
                    next_seq = inv._create_e_sequence()
                    if inv.from_mail and inv.type_document_id and inv.move_type in ('in_invoice', 'in_refund'):
                        inv._create_xml_receptor()
                    else:
                        inv._create_xml()
                    e_billing.utils._update_sequence(inv, next_seq)
                except Exception as e:
                    raise ValidationError(_("Advertencia: %s", e))
            else:
                _logger.info("Comprobante %s no se enviará a hacienda." % (inv.name))

    def _create_e_sequence(self):
        """Creación de Secuencias """
        next_seq = False
        for inv in self:
            _logger.info("Generando secuencias eletrónicas para comprobante con ID: %s " % (inv.id))
            def _get_sequence(invoice):
                """ Extraemos la secuencia acorde al tipo de documeto y compañia. """
                if invoice.company_id:
                    e_line = self.env['einvoice.sequence.lines'].sudo().search([('company_id', '=', invoice.company_id.id),
                                                                                ('type_document_id', '=', invoice.type_document_id.id),
                                                                                ('e_inv_sequence_id.active', '=', True)
                                                                                ])

                    if e_line:
                        if not e_line.e_inv_sequence_id.active:
                            raise ValidationError(_("La secuencia para %s no está activa. Revise las secuencias de esta compañía por favor "
                                                    % (e_line.e_inv_sequence_id.name)))

                    #Retornando secuencia.
                    return e_line

            sequence_eline = _get_sequence(inv)
            #Si no hay secuencia electrónica, entonces lo creamos y asignamos.
            if inv.electronic_sequence:
                inv.consecutive_number_receiver = inv.electronic_sequence
            elif not inv.electronic_sequence:
                #next_number = sequence_eline.e_sequence_id.next_by_id()
                # Hay que tomar en cuenta que esto se hace por precaución, más no es la mejor opción, es solo
                #para casos en los que al crear el xml tenga un fallo por motivo no contemplado en el desarrollo.
                #next_number = sequence_eline.e_sequence_id.number_next_actual
                next_number = e_billing.utils._new_number_sequence(sequence_eline.e_sequence_id)

                inv.electronic_sequence = e_billing.utils.compute_full_sequence(branch=sequence_eline.e_inv_sequence_id.sucursal,
                                                                                terminal=sequence_eline.e_inv_sequence_id.terminal,
                                                                                doc_type_code=inv.type_document_id.code_hacienda,
                                                                                sequence=next_number)
                inv.name = e_billing.utils._create_e_name(inv.type_document_id.code, next_number)
                inv.payment_reference = inv.name
                inv.sequence_eline_id = sequence_eline #Secuencia usada
                #inv.state_send_customer = False
                #inv.state_send_supplier = False
                _logger.info("Creando Secuencia electrónica: %s " % (inv.electronic_sequence))
                _logger.info("Nombre a mostrar del comprobante: %s " % (inv.name))

                next_seq = True

            #Número electrónico
            if not (inv.move_type in ('in_invoice', 'in_refund') and inv.from_mail and inv.state_send_supplier) and not inv.number_electronic:
                inv.number_electronic = e_billing.utils.get_number_electronic(issuer=inv.company_id,full_sequence=inv.electronic_sequence)
                _logger.info("Creando Número electrónico: %s " % (inv.number_electronic))

            #Este campo me permite saber si actualizo la secuencia o no
            return next_seq

    def _send_xml(self):
        """Envio de xml a hacienda"""
        response_json = e_billing.api.send_xml(
            client_id=self.company_id.e_environment,
            token=e_billing.auth._get_token_by_company(self.company_id),
            xml=base64.b64decode(self.xml_invoice),
            date=self.date_issuance,
            electronic_number=self.number_electronic,
            issuer=self.company_id,
            receiver=self.partner_id,
        )
        return response_json

    def _send_xml_receptor(self):
        """Envio de xml de mensaje de aceptación a hacienda"""
        token = e_billing.auth._get_token_by_company(self.company_id)
        response_json = e_billing.api.send_message(
            inv=self,
            date_cr=e_billing.utils.get_time_cr(),
            xml=base64.b64decode(self.xml_invoice),
            token=token,
            client_id=self.company_id.e_environment,
        )
        return response_json, token

    def _retry(self,token, message_body):
        """Reintentar envío de mensaje de aceptación"""
        response_json = e_billing.api.query_document(
            clave="{}-{}".format(self.number_electronic, self.electronic_sequence),
            token=token,
            client_id=self.company_id.e_environment,
        )
        status = response_json.get("status")
        if status == 200:
            self.state_send_supplier = response_json.get("ind-estado")
            self.xml_response = response_json.get("respuesta-xml")
            self.xml_response_name = "ACH_{}-{}.xml".format(self.number_electronic,self.electronic_sequence)

            message_body += (
                "<p><b>Mensaje de Hacienda al procesar el documento: </b>"
                "<br/><b>Documento:</b> {}"
                "<br/><b>Consecutivo:</b> {}"
                "<br/><b>Mensaje:</b> {}"
                "</p>".format(
                    self.number_electronic,
                    self.electronic_sequence,
                    self.state_send_supplier
                    #e_billing.utils.STATE_SELECTOR_PARTNER_MESSAGE[self.state_selector_partner],
                )
            )
            self.message_post(body=message_body, subtype_xmlid="mail.mt_note", message_type='comment')

        elif status == 400:
            self.state_send_supplier = "ne"
            if self.number_electronic and self.electronic_sequence:
                _logger.error("Aceptación de documentos: {}-{} no se encuentra en ISR.".format(self.number_electronic, self.electronic_sequence))
        else:
            _logger.error("Error inesperado en el archivo de aceptación de envío - Aborto")

    def action_send_hacienda(self):
        """TODO: Enviar comprobante a hacienda"""
        for inv in self:
            #Valiar si algún elemento del xml contiene False o false, esto es importante para evitar errores de hacienda
            e_billing.utils._evalue_xml_false(inv.xml_invoice)

            if inv.xml_invoice_supplier_approval and inv.from_mail and inv.state_selector_partner:
                #Envio de comprobantes obtenido mediante el correo
                if e_billing.utils._has_error(inv):
                    continue
                if inv.state_send_customer == "procesando":
                    inv.action_check_hacienda()
                    continue

                response_json, token = inv._send_xml_receptor()
                status = response_json.get("status")
                if 200 <= status <= 299:
                    self.state_send_supplier = "procesando"
                    message_body = _("<p><b>Envío del mensaje del receptor</b></p>")
                    if self.state_send_supplier in ('rechazado', 'error'):
                        message_body += (
                            "<p><b>Cambio consecutivo de mensaje de receptor</b><br/>"
                            "<b>Consecutivo anterior:</b> {} <br/>"
                            "<b>Estado previo:</b> {} </p>".format(self.consecutive_number_receiver, self.state_send_supplier)
                        )
                    # Reintento en el envío de mensaje de aceptación
                    self._retry(token, message_body)
                else:
                    self.state_send_supplier = "error"
                    message_body = (
                        "<p><b>Clave: </b> {}"
                        "<br/><b>Mensaje:</b> {}"
                        "</p>".format(self.number_electronic, response_json.get("text")))
                    self.message_post(body=message_body, subtype_xmlid="mail.mt_note", message_type='comment')
                    _logger.error("Factura Email: {}  Error al enviar el mensaje de aceptación: {}".format(self.number_electronic, response_json.get("text")))


            else:
                # Envio de comprobantes normales (no obtenidos mediante el correo)
                response_json = inv._send_xml()
                response_status = response_json.get("status")
                response_text = response_json.get("text")
                if 200 <= response_status <= 299:
                    if inv.type_document_id.in_purchase and inv.move_type in ('in_invoice', 'in_refund'):
                        inv.state_send_supplier = 'procesando'
                    else:
                        inv.state_send_customer = 'procesando'
                    inv.sudo().message_post(body=response_text, subtype_xmlid="mail.mt_note", message_type='comment')
                    continue
                else:
                    #Mostrar mensaje en el comentario
                    if self.move_type in ['out_invouce','out_refund']:
                        inv.state_send_customer = 'error'
                    elif self.move_type in ['in_invouce','in_refund']:
                        inv.state_send_supplier = 'error'
                    message_body = (
                        "<p><b>Código Estado: </b> {}"                      
                        "<br/><b>Mensaje:</b> {}"
                        "</p>".format(response_status,response_text))
                    self.message_post(body=message_body, subtype_xmlid="mail.mt_note", message_type='comment')


    def action_check_hacienda(self):
        """TODO: Consultar envío de comprobante"""
        for inv in self:
            if inv.to_send:
                if inv.xml_invoice_supplier_approval and inv.from_mail:
                    #Consulta para comprobantes recepcionados por medio del email
                    response_json = e_billing.api.query_document(
                        clave="{}-{}".format(inv.number_electronic, inv.electronic_sequence),
                        token=e_billing.auth._get_token_by_company(inv.company_id),
                        client_id=inv.company_id.e_environment,
                    )
                else:
                    #Consulta para comprobantes enviados (No contempla los que vienen por email)
                    response_json = e_billing.api.query_document(
                        clave=inv.number_electronic,
                        token=e_billing.auth._get_token_by_company(inv.company_id),
                        client_id=inv.company_id.e_environment,
                    )

                status = response_json.get("status") #Codigo de estado
                state = response_json.get("ind-estado") #Estado
                if status == 400:
                    message_body = (
                        "<p><b>Código Estado: </b> {}"
                        "<br/><b>Mensaje:</b> {}"
                        "</p>".format(status, state))
                    inv.message_post(body=message_body, subtype_xmlid="mail.mt_note", message_type='comment')
                else:
                    if inv.move_type in ('out_invoice', 'out_refund'): #Para comprobantes de clientes
                        inv.state_send_customer = state
                        inv.date_issuance = e_billing.utils.get_time_cr()

                    elif inv.move_type in ('in_invoice', 'in_refund'): #Para comprobantes de proveedores
                        inv.state_send_supplier = state

                    inv.xml_response_name = "RPTA_{}.xml".format(inv.number_electronic)
                    inv.xml_response = response_json.get("respuesta-xml")

                    if inv.state_send_customer == 'aceptado' and inv.company_id.send_mail_to_customer:
                        inv._send_mail_customer()


    # ************************************* Todo: ACCIÓN PLANIFICADA : CRON  ********************
    @api.model
    def check_einvoices(self, type):
        """Revisión de comprobantes cada 5 minutos para verificar sus estados en hacienda"""
        MAX_LIMIT = 10
        domain = []
        if type == 'customer':
            domain = [("move_type", "in", ["out_invoice", "out_refund"]),
                      ('state_send_customer', 'in', ['recibido', 'procesando', 'ne', 'error'])]
        elif type == 'supplier':
            domain = [("move_type", "in", ["in_invoice", "in_refund"]),('state_send_supplier', 'in', ['procesando', 'ne', 'error'])]
        domain.append(('type_document_id', '!=', False))
        domain.append(('state', 'in', ["posted", "paid"]))
        domain.append(('to_send', '=', True))

        invoices = self.env["account.move"].sudo().search(domain)
        if invoices:
            for inv in invoices[:MAX_LIMIT]:
                #Consultamos el estado de los comprobantes
                inv.action_check_hacienda()

                #Este caso es solo para los comprobantes de clientes y cuando tenga el check de envío automático activo
                if inv.state_send_customer == 'aceptado' and inv.company_id.send_mail_to_customer:
                    inv._send_mail_customer()

    def _send_mail_customer(self):
        """Envío de mail al cliente luego de que hacienda acepte el comprobante"""
        email_template = self.env.ref("account.email_template_edi_invoice", False)

        if not email_template:
            _logger.info("No existe template para envío de email")

        if self.partner_id and self.partner_id.email:
            ir_attachment = self.env['ir.attachment'].sudo()
            if self.partner_id and self.partner_id.email:
                email_template.attachment_ids = False
                if self.xml_invoice:
                    attachment_invoice = ir_attachment.search([('res_model', '=', 'account.move'), ('res_id', '=', self.id),
                                                               ('res_field', '=', 'xml_invoice'), ('mimetype', '=', 'text/plain')], limit=1)
                    if not attachment_invoice:
                        attachment_invoice = ir_attachment.create({
                            'datas': self.xml_invoice,
                            'name': self.xml_invoice_name,
                            'mimetype': 'text/plain',
                            'res_model': 'account.move',
                            'res_id': self.id,
                            'res_field': 'xml_invoice'
                        })

                    email_template.attachment_ids += attachment_invoice

                if self.xml_response:
                    attachment_response = ir_attachment.search([('res_model', '=', 'account.move'), ('res_id', '=', self.id),
                                                                ('res_field', '=', 'xml_response'), ('mimetype', '=', 'text/plain')], limit=1)
                    if not attachment_response:
                        attachment_response = self.env['ir.attachment'].create({
                            'datas': self.xml_response,
                            'name': self.xml_response_name,
                            'mimetype': 'text/plain',
                            'res_model': 'account.move',
                            'res_id': self.id,
                            'res_field': 'xml_response'
                        })

                    email_template.attachment_ids += attachment_response
                    email_template.with_context(type="binary", default_type="binary").send_mail(self.id, raise_exception=False, force_send=True)

                if email_template.attachment_ids:
                    for att in email_template.attachment_ids:
                        email_template.sudo().write({'attachment_ids': [(3, att.id)]})

                    #email_template.attachment_ids = [(5)]
                    #self.write({"is_move_sent": True})
        else:
            _logger.info("El comprobante {} no tiene cliente o el cliente no tiene un email".format(self.name))

    def action_invoice_sent(self):
        """ ADJUNTAR LOS ARCHIVOS PARA ENVÍO AL CLIENTE
        """
        self.ensure_one()
        template = self.env.ref(self._get_mail_template(), raise_if_not_found=False)
        lang = False
        if template:
            ir_attachment = self.env['ir.attachment'].sudo()
            if self.partner_id and self.partner_id.email:
                template.attachment_ids = False
                if self.xml_invoice:
                    attachment_invoice = ir_attachment.search([('res_model', '=', 'account.move'), ('res_id', '=', self.id),
                                                               ('res_field', '=', 'xml_invoice'), ('mimetype', '=', 'text/plain')], limit=1)
                    if not attachment_invoice:
                        attachment_invoice = ir_attachment.create({
                            'datas': self.xml_invoice,
                            'name': self.xml_invoice_name,
                            'mimetype': 'text/plain',
                            'res_model': 'account.move',
                            'res_id': self.id,
                            'res_field': 'xml_invoice'
                        })

                    template.attachment_ids += attachment_invoice

                if self.xml_response:
                    attachment_response = ir_attachment.search([('res_model', '=', 'account.move'), ('res_id', '=', self.id),
                                                                ('res_field', '=', 'xml_response'), ('mimetype', '=', 'text/plain')], limit=1)
                    if not attachment_response:
                        attachment_response = self.env['ir.attachment'].create({
                            'datas': self.xml_response,
                            'name': self.xml_response_name,
                            'mimetype': 'text/plain',
                            'res_model': 'account.move',
                            'res_id': self.id,
                            'res_field': 'xml_response'
                        })

                    template.attachment_ids += attachment_response

                    # attachment_pdf = ir_attachment.search([('res_model', '=', 'account.move'), ('res_id', '=', self.id),
                    #                                      ('res_field', '=', False),('mimetype','=','application/pdf')], limit=1)
                    # if attachment_pdf:
                    #     template.attachment_ids += attachment_pdf

            lang = template._render_lang(self.ids)[self.id]
        if not lang:
            lang = get_lang(self.env).code
        compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)

        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            # For the sake of consistency we need a default_res_model if
            # default_res_id is set. Not renaming default_model as it can
            # create many side-effects.
            default_res_model='account.move',
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            model_description=self.with_context(lang=lang).type_name,
            force_email=True,
            wizard_opened=True
        )
        return {
            'name': _('Send Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    # ************************************* Todo: MÉTODOS ********************

    @api.onchange('to_send')
    def _onchange_to_send(self):
        env_journal = self.env['account.journal'].sudo()
        if self.to_send:
            if self.move_type in ('out_invoice','out_refund'):
                #journal = env_journal.search([('e_invoice_check', '=', True), ('type', '=', 'sale'), ('company_id', '=', self.company_id.id)])
                self.journal_id = self.company_id.journal_sale_id
            elif self.move_type in ('in_invoice','in_refund'):
                #journal = env_journal.search([('e_invoice_check', '=', True), ('type', '=', 'purchase'), ('company_id', '=', self.company_id.id)])
                self.journal_id = self.company_id.purchase_sale_id
        elif not self.to_send and self.journal_id:
            j_object = self._get_default_journal()
            self.journal_id = j_object


    @api.onchange('state_selector_partner')
    def _onchange_state_selector_partner(self):
        if self.state_selector_partner:
            code_hacienda = e_billing.utils.STATE_SELECTOR_PARTNER_RELATION_DOCUMENT_TYPE[self.state_selector_partner]
            type_document_type_id = self.env['type.document'].sudo().search([('code_hacienda','=',code_hacienda)]) #Puede ser de compra o venta
            self.type_document_purchase_id = type_document_type_id
        else:
            if self.move_type in ['out_invoice','out_refund']:
                self.type_document_sale_id = False
            elif self.move_type in ['in_invoice','in_refund']:
                self.type_document_purchase_id = False

    @api.model
    def default_get(self, fields):
        vals = super(AccountMove, self).default_get(fields)
        if 'default_move_type' in self.env.context or 'move_type' in vals:
            move_type = self.env.context.get('default_move_type')
            if not move_type:
                move_type = vals['move_type']
            if move_type in ['out_invoice','out_refund','in_invoice','in_refund'] and self.env.company.send_hacienda == 'automatic'\
                    and self.env.company.e_environment in ['api-stag','api-prod']:
                vals['to_send'] = True

            if 'journal_id' in vals:
                journal = self.env['account.journal'].sudo().browse(vals['journal_id'])
                if not journal.to_send:
                    vals['to_send'] = False
        return vals

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            self.to_send = self.journal_id.to_send
        return super(AccountMove, self)._onchange_journal()

    # ************************************* Todo: CARGA DE FACTURAS POR EMAIL  ********************
    def upload_xml_supplier(self):
        values = {"name": "/"}  # we have to give the name otherwise it will be set to the mail's subject
        # TODO CÓDIGO AGREGADO

        #invoice_import_ids = e_billing.utils._import_params_sup_invoice(self)
        invoice_import_ids = self.env['account.move.supplier.import'].sudo().search([('company_id', '=', self.company_id.id),
                                                                                     ('active','=',True)], limit=1)
        if invoice_import_ids:
            values['journal_id'] = invoice_import_ids.journal_id.id
            logging.info("-------- Parseando xml a factura --------")
            if self.xml_invoice_supplier_approval:
                if self.xml_invoice_supplier_approval_name[-3:] == "xml":
                    vals = e_billing.supplier_email.parse_xml.upload_xml_to_invoice(self, self.xml_invoice_supplier_approval, invoice_import_ids)
                    values.update(vals)
                    self.write(values)
                    self.env['ir.attachment'].sudo().create({
                        'name': self.xml_invoice_supplier_approval_name,
                        'datas': base64.b64encode(self.xml_invoice_supplier_approval),
                        'res_model': 'account.move',
                        'res_id': self.id,
                    })
                else:
                    raise ValidationError(_("Debe ser un archivo con extensión .xml "))


    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Heredamos el método y luego creamos un método de creación para facturas de proveedor desde mail"""
        invoice_import_ids = e_billing.utils._import_params_sup_invoice(self.company_id)
        if not invoice_import_ids:
            _logger.info("No hay configuración para importación en ninguna compañia")
            res = super(AccountMove, self).message_new(msg_dict, custom_values)
        else:
            #
            # # Crear facturas de proveedor.
            # if not msg_dict.get("attachments") or len(msg_dict.get("attachments")) == 0:
            #     return False

            _logger.info("ID de importación %s - compañia %s" % (invoice_import_ids.id, invoice_import_ids.company_id.name))
            res = self.message_new_sup_einvoice(msg_dict, custom_values, invoice_import_ids)
        return res


    def message_new_sup_einvoice(self, msg_dict, custom_values, invoice_import_ids):
        # TODO CÓDIGO AGREGADO
        if invoice_import_ids:
            custom_values = {"move_type": "in_invoice"}
        else:
            # Add custom behavior when receiving a new invoice through the mail's gateway.
            if (custom_values or {}).get('move_type', 'entry') not in ('out_invoice', 'in_invoice'):
                return super().message_new(msg_dict, custom_values=custom_values)

        def is_internal_partner(partner):
            # Helper to know if the partner is an internal one.
            return partner.user_ids and all(user.has_group('base.group_user') for user in partner.user_ids)

        extra_domain = False
        if custom_values.get('company_id'):
            extra_domain = ['|', ('company_id', '=', custom_values['company_id']), ('company_id', '=', False)]
        # Search for partners in copy.
        cc_mail_addresses = email_split(msg_dict.get('cc', ''))
        followers = [partner for partner in self._mail_find_partner_from_emails(cc_mail_addresses, extra_domain) if partner]
        logging.info("-------- Seguidores --------")

        # Search for partner that sent the mail.
        from_mail_addresses = email_split(msg_dict.get('from', ''))
        senders = partners = [partner for partner in self._mail_find_partner_from_emails(from_mail_addresses, extra_domain) if partner]
        logging.info("-------- Remitentes --------")

        # Search for partners using the user.
        if not senders:
            senders = partners = list(self._mail_search_on_user(from_mail_addresses))

        if partners:
            # Check we are not in the case when an internal user forwarded the mail manually.
            if is_internal_partner(partners[0]):
                # Search for partners in the mail's body.
                body_mail_addresses = set(email_re.findall(msg_dict.get('body')))
                partners = [partner for partner in self._mail_find_partner_from_emails(body_mail_addresses, extra_domain) if not is_internal_partner(partner)]
        logging.info("-------- partners --------")

        # Little hack: Inject the mail's subject in the body.
        if msg_dict.get('subject') and msg_dict.get('body'):
            msg_dict['body'] = '<div><div><h3>%s</h3></div>%s</div>' % (msg_dict['subject'], msg_dict['body'])

        # Create the invoice.
        values = {
            'name': '/',  # we have to give the name otherwise it will be set to the mail's subject
            'invoice_source_email': from_mail_addresses[0],
            'partner_id': partners and partners[0].id or False,
        }
        move = False
        #Proceso de parseo de xml
        if invoice_import_ids:
            custom_values['move_type'] = 'in_invoice'
            if 'journal_id' not in custom_values:
                if not invoice_import_ids.journal_id:
                    raise UserError(_("Para importar las facturas de proveedor debe definir un diario en la configuración"))
                custom_values['journal_id'] = invoice_import_ids.journal_id.id
            attachments = msg_dict.get("attachments")
            logging.info("-------- Parseando xml a factura --------")
            vals = e_billing.supplier_email.parse_xml.parseXml(self=self, attachments=attachments,invoice_import_ids=invoice_import_ids)
            if not vals:
                logging.info("No es un xml por lo tanto no se leerá")
            else:
                values.update(vals)
                logging.info("-------- Creando factura --------")
                move = self.env['account.move'].sudo().create(vals)
                if move:
                    logging.info("-------- Factura creada con ID: {} ".format(move.id))
                else:
                    logging.error("------- Factura NO creada")

        else:
            move_ctx = self.with_context(default_move_type=custom_values['move_type'], default_journal_id=custom_values['journal_id'])
            logging.info("-------- valores y contexto --------")
            logging.info("-------- valores y contexto --------")
            move = super(AccountMove, move_ctx).message_new(msg_dict, custom_values=values)
            move.sudo()._compute_name()  # because the name is given, we need to recompute in case it is the first invoice of the journal
        if move:
            # Assign followers.
            all_followers_ids = set(partner.id for partner in followers + senders + partners if is_internal_partner(partner))
            move.message_subscribe(list(all_followers_ids))
        return move

    def button_cancel_invoice(self):
        self.ensure_one()
        self.button_cancel()

    @api.model
    def generate_xml(self):
        for record in self:
            if not record.xml_invoice:
                record._create_xml_4_3()