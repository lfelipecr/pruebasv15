# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError,ValidationError
class EinvoiceSequence(models.Model):
    _name = "einvoice.sequence"
    _description = "Secuencias para facturación electrónica"
    _order = 'id desc'
    _rec_name = 'name'

    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(string='Activo',default=False)
    name = fields.Char(string='Nombre',compute='_compute_name', store=True)
    sucursal = fields.Char('Sucursal', default=1)
    terminal = fields.Char('Terminal', default=1, store=True)

    line_ids = fields.One2many('einvoice.sequence.lines','e_inv_sequence_id')

    @api.depends('company_id','sucursal','terminal')
    def _compute_name(self):
        if self.company_id and self.sucursal and self.terminal:
            if not self.company_id.vat:
                raise UserError(_("Asegúrese de que la compañia tenga un número de identificación"))
            self.name = self.company_id.vat + '/' + self.sucursal + '/' + self.terminal

    @api.constrains('active', 'company_id')
    def _constraint_active_company(self):
        records = self.env['einvoice.sequence'].sudo().search([('active', '=', True),
                                                               ('company_id', '=', self.company_id.id),
                                                               ('terminal', '=', self.terminal),
                                                               ('sucursal', '=', self.sucursal)])
        if records:
            for rec in records:
                if rec.id != self.id:
                    raise UserError(_("Ya existe un registro para la compañía %s  - Terminal %s - Sucursal %s" % (self.company_id.name, self.terminal, self.sucursal)))

    def create_sequences(self, type_documents=False):
        """
            <field name="name">Secuencia de Factura Electrónica</field>
            <field name="code">sequece.FE</field>
            <field name="prefix"/>
            <field name="implementation">no_gap</field>
            <field name="padding">10</field>
        :return:
        """
        model_sequence = self.env['ir.sequence'].sudo()
        if not type_documents:
            type_documents = self.env['type.document'].sudo().search([('active', '=', True)])

        if not self.company_id.vat:
            raise UserError(_("Asegúrese de que la compañia tenga un número de identificación"))

        lines = []
        for td in type_documents:

            td_exists = self.line_ids.filtered(lambda l: l.type_document_id.id == td.id)
            if not td_exists:
                name = self.company_id.vat + '/' + self.sucursal + '/' + self.terminal + '/' + td.name
                code = self.company_id.vat + '.' + self.sucursal + '.' + self.terminal + '.' + td.code

                data = {
                    "name": name,
                    "code": code,
                    "implementation": "standard",
                    "padding": 10,
                    "use_date_range": False,
                    "company_id": self.company_id.id,
                }

                seq_line = model_sequence.search([('code','=',code)])
                if not seq_line:
                    seq_line = model_sequence.create(data)
                    lines.append((0,0,{
                        'e_inv_sequence_id': self.id,
                        'type_document_id': td.id,
                        'e_sequence_id': seq_line.id,
                    }))


        self.write({'line_ids': lines})


class EinvoiceSequenceLines(models.Model):
    _name = "einvoice.sequence.lines"
    _description = "Secuencias para facturación electrónica líneas"
    _order = 'id desc'
    _rec_name = 'type_document_id'

    e_inv_sequence_id = fields.Many2one('einvoice.sequence')
    company_id = fields.Many2one('res.company',related='e_inv_sequence_id.company_id', store=True)
    type_document_id = fields.Many2one('type.document','Tipo documento')
    e_sequence_id = fields.Many2one('ir.sequence','Secuencia')
    in_pos = fields.Boolean(string='En pos')