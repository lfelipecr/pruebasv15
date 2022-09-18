from odoo import _
from odoo.exceptions import ValidationError, UserError
import base64
import pkgutil
import random
from datetime import datetime

import jinja2
#import OpenSSL
from OpenSSL import crypto

import phonenumbers
import pytz
import xades
import xmlsig
from lxml import etree
import re

from . import abstract
from . import context

#Nuevo 2022-04-24
from ..xades.context2 import PolicyId2, XAdESContext2, create_xades_epes_signature
import logging
_logger = logging.getLogger(__name__)
def get_time_cr(as_obj=False):
    """Return current time in Costa Rica in ISO-Format

    Returns:
        str: current time in Costa Rica in ISO-Format
    """
    now_cr = datetime.now(pytz.timezone("America/Costa_Rica"))
    if as_obj:
        return now_cr
    iso_str = now_cr.isoformat()
    return iso_str


def limit(string, max_chars):
    """Truncate a string to the `max_chars` amount ouf chars and append `...` at the end of it if is truncated

    Args:
        string (str): String to limitate
        max_chars (integer): Amount of chars wanted

    Returns:
        str: The original string truncated
    """
    return (string[: max_chars - 3] + "...") if len(string) > max_chars else string


def compute_full_sequence(branch, terminal, doc_type_code, sequence):
    branch = str(branch)
    terminal = str(terminal)
    sequence = str(sequence)

    if not abstract.Sequence.valid(sequence):
        raise ValidationError(_("The sequence must have 10 digits"))

    branch_filled = branch.zfill(3)
    terminal_filled = terminal.zfill(5)

    full_sequence = branch_filled + terminal_filled + doc_type_code + sequence
    return full_sequence


def get_number_electronic(issuer,full_sequence,situation_code=abstract.Voucher.TYPE_TO_CODE["normal"]):
    """Generate Number Electronic

    Args:
        issuer (res.company/res.partner): Issuer
        full_sequence (str): Sequence used to generate Number Electronic (use compute_full_sequence to generate it)
        situation_code (str, optional): Situation code. Defaults to Voucher.TYPE_TO_CODE["normal"].

    Returns:
        [type]: [description]
    """
    if issuer.country_id:
        phone_code = issuer.country_id.phone_code
    #phone_code = phonenumbers.parse(issuer.phone, issuer.country_id and issuer.country_id.code)
    cur_date = get_time_cr(as_obj=True).strftime("%d%m%y")
    random_digits = str(random.randint(1, 99999999)).zfill(8)
    number_electronic = (
        str(phone_code)
        + cur_date
        + str(issuer.vat).zfill(12)
        + full_sequence
        + situation_code
        + random_digits
    )
    return number_electronic


def get_template(path: str) -> jinja2.Template:
    """Get jinja2.Template from local path and trim extra spaces

    Args:
        path (str): Template .jinja path

    Returns:
        jinja2.Template: Template
    """
    template = jinja2.Template(pkgutil.get_data(__name__, "templates/" + path).decode(),trim_blocks=True,lstrip_blocks=True)
    return template


def sign_xml(cert, pin, xml):
    """Sign an XML using XAdES

    Args:
        cert (binary): Certificate
        pin (str): PIN to decrypt cert
        xml (str): XML to be signed

    Returns:
        [str]: XML signed
    """
    signed = False
    policy_id = 'https://www.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2016/v4.2/ResolucionComprobantesElectronicosDGT-R-48-2016_4.2.pdf'
    xml = xml.replace('&', '&amp;')
    root = etree.fromstring(xml)
    root2 = etree.fromstring(xml)
    error = False
    # try:
    #     signature = context.create_xades_epes_signature()
    #     policy = xades.policy.GenericPolicyId(
    #         identifier=policy_id,
    #         name=u"Politica de Firma Factura",
    #         hash_method=xmlsig.constants.TransformSha1,
    #     )
    #     root.append(signature)
    #     ctx = xades.XAdESContext(policy)
    #     certificate = crypto.load_pkcs12(base64.b64decode(cert), pin)
    #     ctx.load_pkcs12(certificate)
    #     ctx.sign(signature)
    # except Exception as exc:
    #     error = True
    #
    # if error:
    try:
        signature = create_xades_epes_signature()
        policy = PolicyId2()
        policy.id = policy_id
        root2.append(signature)
        ctx = XAdESContext2(policy)
        certificate = crypto.load_pkcs12(base64.b64decode(cert), bytes(pin, 'utf-8'))
        ctx.load_pkcs12(certificate)
        ctx.sign(signature)
        root = root2
    except Exception as error:
        raise UserError(error)

    signed = etree.tostring(
        root,
        encoding="UTF-8",
        method="xml",
        xml_declaration=True,
        with_tail=False
    )

    return signed




STATE_INVOICE_SUPPLIER = [
    ("aceptado","Aceptado"),
    ("rechazado", "Rechazado"),
    ("error", "Error"),
    ("na", "No aplica"),
    ("ne", "No encontrado"),
    ("firma_invalida", "Firma inválida"),
    ("procesando", "Procesando")
]


STATE_INVOICE_CUSTOMER = [
        ("aceptado", "Aceptado"),
        ("rechazado", "Rechazado"),
        ("recibido","Recibido"),
        ("firma_invalida","Firma inválida"),
        ("error", "Error"),
        ("procesando","Procesando"),
        ("na", "No aplica"),
        ("ne", "No encontrado"),
]


STATE_SELECTOR_PARTNER = [("1","Aceptado"),("3","Rechazado"),("2","Parcialmente aceptado")]

STATE_SELECTOR_PARTNER_MESSAGE = {
    '1': 'Aceptado',
    '2': 'Rechazado',
    '3': 'Parcialmente aceptado',
}


STATE_SELECTOR_PARTNER_RELATION_DOCUMENT_TYPE = {
    '1': '05',
    '2': '06',
    '3': '07',
}

def _validations_e_invoice(invoice):
    """Validaciones al momento de publicar un comprobnate """

    if invoice.move_type == 'out_refund' and not invoice.reference_code_id:
        raise ValidationError(_("Al ser una nota de crédito, debe validar que tipo es. Complete la campo 'Tipo nota crédito' "))

    if not invoice.partner_id.email and invoice.move_type != 'entry':
        raise ValidationError(_("Valide que el cliente tenga un correo electrónico "))

    if not invoice.type_document_id:
        raise ValidationError(_("Por favor: Seleccione un tipo de comprobante. "))

    if not invoice.payment_methods_id:
        raise ValidationError(_("Por favor: Seleccione un método de pago. "))

    if invoice.type_document_id.code == 'TE':
        raise ValidationError(_("El tipo de documento para Ticket no está configurado para facturas. "))

    if invoice.invoice_date_due and not invoice.invoice_payment_term_id:
        raise ValidationError(_("Por favor: Seleccione algún término de pago ya que este documento será enviado a hacienda. "))

    if invoice.invoice_payment_term_id:
        if not invoice.invoice_payment_term_id.sale_conditions_id:
            raise ValidationError(_("Por favor: Seleccione la Condición de Venta dentro de : %s  " % (invoice.invoice_payment_term_id.name) ))

    invs = invoice.env['account.move'].sudo().search([('id', '!=', invoice.id),
                                                      ('company_id', '=', invoice.company_id.id),
                                                      ('number_electronic', '=', invoice.number_electronic),
                                                      ('number_electronic', '!=', False),
                                                      ('move_type', '=', invoice.move_type),
                                                      ('state_send_supplier', 'in', [False, 'aceptado', 'procesando']),
                                                      ('state', '!=', 'cancel'),
                                                      ('payment_state', '!=', 'reversed'),
                                                      ])

    if invs:
        raise ValidationError(_("La clave de comprobante debe ser única. Puede ser que este comprobante ya esté registrado."))


def _create_e_name(code, number):
    """Creación de nombre en factura electrónica """
    return str(code) + '-' + str(number)

def _has_error(self):
    """Verifique si las facturas tienen errores para ser procesadas"""
    if self.state_send_supplier in ("aceptado", "rechazado", "na"):  # TODO why
        raise UserError(_("La factura ya ha sido confirmada"))
    error_message = None
    if abs(self.amount_total_electronic_invoice - self.amount_total) > 1 and self.move_type in ['in_invoice','in_refund']:  # TODO may be config
        error_message = _("La cantidad total no coincide con la cantidad XML")
    if not self.state_selector_partner and self.move_type in ['in_invoice','in_refund'] and self.to_send:
        error_message = _("Primero debe seleccionar el tipo de respuesta para el archivo cargado.")
    if error_message:
        self.state_send_supplier = "error"
        self.message_post(subject=_("Error"), body=error_message)
    return error_message


def _evalue_xml_false(xml):
    if xml:
        xml_bytes = base64.b64decode(xml)
        xml_string = xml_bytes.decode("utf-8")
        fields_to_search = ['false','False']
        for field in fields_to_search:
            if xml_string.find(field) != -1:
                raise ValidationError("Hay algún elemento con contenido {} en el xml. Descargue el xml y revise que elemento contiene error "
                                      "antes de enviar a Hacienda. ".format(field))


def _update_sequence(invoice=False, value=False):
    if invoice:
        if invoice.sequence_eline_id:
            seq = invoice.sequence_eline_id.e_sequence_id
            #Si hay secuencia, y hay un valor True, y no tuvo una respuesta de hacienda(Porque no fue enviado anteriormente)
            #Entonces procede con el aumento de la secuencia.
            if seq and value and not invoice.xml_response:
                seq.sudo().next_by_id()

            #Limpieza de datos clave
            # invoice.state_send_customer = False
            # invoice.state_send_supplier = False
            # invoice.xml_response = False
            # invoice.xml_response_name = False

def _new_number_sequence(e_sequence_id):
    number = str(e_sequence_id.number_next_actual)
    padding = e_sequence_id.padding
    return number.zfill(padding)


def _import_params_sup_invoice(self):
    companies = self.env['res.company'].sudo().search([])
    config = False
    for company in companies:
        exist = False
        if company.bill_supplier_import:
            config = self.env['account.move.supplier.import'].sudo().search([('company_id', '=', company.id)], limit=1)
            if config:
                if not config.active:
                    _logger.info("No hay ninguna configuración 'ACTIVA' para esta compañía: %s - configuración con ID: %s" % (company.name, config.id))
                else:
                    exist = True
            else:
                _logger.info("No hay ninguna configuración para esta compañía: %s" % (company.name))

        if exist:
            break

    return config

