# -*- coding: utf-8 -*-
from odoo import api, fields, models
from .. import e_billing

TYPES = {
    0 : u'FE-Secuencia de Factura electrónica',
    1 : u'NC-Secuencia de Nota de crédito electrónica',
    2 : u'TE-Secuencia de Tiquete electrónico',
}

class PosConfig(models.Model):
    _inherit = "pos.config"

    #FACTURACIÓN
    used_invoice = fields.Boolean('')
    sucursal = fields.Char(string="Sucursal", required=False, copy=False)
    terminal = fields.Char(string="Terminal", required=False, copy=False)
    e_sequence_id = fields.Many2one('einvoice.sequence', string='Secuencia')
    lines_sequences = fields.One2many('einvoice.sequence.lines', related='e_sequence_id.line_ids', readonly=False, domain="[('in_pos','=', True)]")
    show_send_hacienda = fields.Boolean()

    #SERVICIO ADICIONAL
    show_remove_tax = fields.Boolean()  # Quitar 10% de servicio
    remove_tax_amount = fields.Many2one('account.tax', domain=[('type_tax_use', '=', 'sale')])

    #MULTIDIVISA
    multi_currency = fields.Boolean('Habilitar multidivisa')
    currency_ids = fields.Many2many('res.currency', string="")



    def create_electronic_sequences(self):
        model_sequence = self.env['einvoice.sequence'].sudo()
        seq = model_sequence.search([('company_id','=', self.company_id.id),
                                     ('sucursal','=',self.sucursal),
                                     ('terminal','=',self.terminal),
                                     ('active','=',True)])
        if not seq:
            data = {
                'company_id': self.company_id.id,
                'sucursal': self.sucursal,
                'terminal': self.terminal,
                'active': True,
            }

            seq = model_sequence.create(data)
        FILTER = ['FE', 'TE', 'NC']
        self.e_sequence_id = seq
        type_documents = self.env['type.document'].sudo().search([('active', '=', True), ('code', 'in', FILTER)])
        seq.sudo().create_sequences(type_documents)
        for line in self.lines_sequences:
            if line.type_document_id.code in FILTER:
                line.in_pos = True


    def open_session_cb(self, check_coa=True):
        e_billing.bridge._validations_einvoice_posConfig(self)
        return super(PosConfig, self).open_session_cb(check_coa)
