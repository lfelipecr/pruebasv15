from odoo import _
from odoo.exceptions import ValidationError, UserError

def _validations_einvoice_posConfig(config):
    company_id = config.company_id
    if company_id.e_environment and config.used_invoice:
        if not config.sucursal:
            raise ValidationError(_('Para facturación electrónica debe tener configurada una sucursal.'))
        if not config.terminal:
            raise ValidationError(_('Para facturación electrónica debe tener configurada un terminal.'))
        if not config.e_sequence_id or not config.lines_sequences:
            raise ValidationError(_('Para facturación electrónica debe tener configurada una secuencia electrónica'))
        if config.payment_method_ids:
            for pay in config.payment_method_ids:
                if not pay.payment_method_id:
                    raise ValidationError(_('Para el método de pago %s configure el método de pago electrónico' % (pay.name)))
                if not pay.account_payment_term_id:
                    raise ValidationError(_('Para el método de pago %s configure el término de pago electrónico' % (pay.name)))


        if not company_id.country_id:
            raise ValidationError(_('Asegúrese que la compañia tenga un país.'))
        if not company_id.state_id:
            raise ValidationError(_('Asegúrese que la compañia tenga un estado.'))
        if not company_id.county_id:
            raise ValidationError(_('Asegúrese que la compañia tenga un cantón.'))
        if not company_id.district_id:
            raise ValidationError(_('Asegúrese que la compañia tenga un distrito.'))
        if not company_id.neighborhood_id:
            raise ValidationError(_('Asegúrese que la compañia tenga un barrio.'))
        if not company_id.phone:
            raise ValidationError(_('Asegúrese que la compañia tenga un teléfono.'))
        if not company_id.email:
            raise ValidationError(_('Asegúrese que la compañia tenga un correo electrónico.'))


def _validations_e_pos(order):
    """Validaciones al momento de publicar un comprobante """
    message = "Orden %s " % (order.name)
    process = True
    if not order.number_electronic:
        message += ' - No tiene número elecrónico'
        process = False

    if order.is_return and order.amount_total > 0:
        message += ' - tiene monto positivo, pero es nota de crédito en POS'
        process = False

    if not order.type_document_id:
        message += ' No tiene un tipo de comprobante.'
        process = False


    orders = order.env['pos.order'].sudo().search([('id', '!=', order.id),
                                                      ('company_id', '=', order.company_id.id),
                                                      ('number_electronic', '=', order.number_electronic),
                                                      ('number_electronic', '!=', False),
                                                      ('state', '!=', 'cancel'),
                                                      ])

    if orders:
        message = " - La clave de comprobante debe ser única. Puede ser que este comprobante ya esté registrado."
        process = False

    return process, message