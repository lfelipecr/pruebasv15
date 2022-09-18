from odoo import api, fields, models

from .. import e_billing
class MoveLine(models.Model):
    _inherit = "account.move.line"

    discount_note = fields.Char(string='Naturaleza Desc.')
    total_tax = fields.Float(string='Total impuesto')
    info_json = fields.Text(string=u'Información')

    def _get_tax_exoneration(self, line):
        exo = line.move_id.partner_has_exoneration
        partner_exoneration_ids = self.move_id.partner_exoneration_ids
        tax_sale_id = self.env['account.tax'].sudo()
        if line.tax_ids and partner_exoneration_ids and line.product_id:
            exoneration_lines = self.env['res.partner.exonerated'].sudo().browse(partner_exoneration_ids.ids)
            for tax in line.tax_ids:
                if exo and exoneration_lines:
                    decimals_e, exoneration = e_billing.generate_xml._get_exoneration(exoneration_lines, line.product_id, 2, tax.tax_code)  # Decimales de exoneración
                    if exoneration:
                        tax_sale_id += exoneration.tax_sale_id

        return tax_sale_id

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(MoveLine, self)._onchange_product_id()
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue

            tax_sale_id = self._get_tax_exoneration(line)
            if tax_sale_id:
                line.tax_ids += tax_sale_id

    @api.onchange('product_uom_id')
    def _onchange_uom_id(self):
        super(MoveLine, self)._onchange_uom_id()
        if self.display_type in ('line_section', 'line_note'):
            return

        tax_sale_id = self._get_tax_exoneration(self)
        if tax_sale_id:
            self.tax_ids += tax_sale_id