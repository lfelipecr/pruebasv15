# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    reference_code_id = fields.Many2one('reference.code',string=u'Tipo nota crédito')
    #country_id = fields.Many2one('res.country', related='company_id.country_id')
    company_country_id = fields.Many2one('res.country', 'Company Country', related='company_id.country_id', readonly=True)
    company_country_code = fields.Char(related='company_country_id.code', readonly=True)

    @api.onchange('reference_code_id')
    def _onchange_reference_code_id(self):
        if self.reference_code_id:
            self.reason = self.reference_code_id.name

    def _prepare_default_reversal(self, move):

        if not self.journal_id:
            raise UserError(_("Seleccione un diario por favor. De preferencia: {}".format(move.journal_id.name)))

        reverse_date = self.date if self.date_mode == 'custom' else move.date

        type_document_sale_id = self.env.ref('l10n_cr_base.document_nota_credito').id if move.move_type == 'out_invoice' else False
        type_document_purchase_id = self.env.ref('l10n_cr_base.document_nota_credito').id if move.move_type == 'in_invoice' else False
        if move.to_send:
            type_document_id = self.env.ref('l10n_cr_base.document_nota_credito').id if move.move_type == 'out_invoice' \
                               else self.env.ref('l10n_cr_base.document_nota_credito').id
        else:
            type_document_id = False

        return {
            'ref': _('Rectificativa de: %(move_name)s, %(reason)s', move_name=move.name, reason=self.reason)
                   if self.reason
                   else _('Rectificativa de: %s', move.name),
            'date': reverse_date,
            'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
            'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
            'invoice_user_id': move.invoice_user_id.id,
            'auto_post': True if reverse_date > fields.Date.context_today(self) else False,
            'reference_code_id': self.reference_code_id.id,
            'invoice_id':  move.id,
            'type_document_sale_id': type_document_sale_id,
            'type_document_purchase_id': type_document_purchase_id,
            'type_document_id': type_document_id,
            'to_send': move.to_send,
            'invoice_payment_term_id': move.invoice_payment_term_id.id,
            'payment_methods_id': move.payment_methods_id.id,
        }
