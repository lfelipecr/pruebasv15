from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

classification_type = [
    ('none','Ninguna'),
    ('exempt','Exento'),
    ('no_hold','No Sujeta'),
    ('exonerated','Exonerada')
]

class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_code = fields.Char()
    iva_tax_desc = fields.Char(string="Tipo IVA",default="N/A",)
    iva_tax_code = fields.Char(string="Código IVA",default="N/A",)
    #has_exoneration = fields.Boolean(string="Tax Exonerated",)
    is_exoneration = fields.Boolean(string="Es una exoneración")
    percentage_exoneration = fields.Integer()
    #tax_root = fields.Many2one(comodel_name="account.tax",)
    classification_type = fields.Selection(selection=classification_type, string='Clasificación', default='none')

    @api.onchange('classification_type')
    def _onchange_classification_type(self):
        for record in self:
            if record.classification_type:
                if record.classification_type == 'exonerated':
                    record.is_exoneration = True
                else:
                    record.is_exoneration = False
    #
    # @api.onchange("tax_root")
    # def _onchange_tax_root(self):
    #     self.tax_compute_exoneration()

    @api.constrains("percentage_exoneration")
    def _check_percentage_exoneration(self):
        for tax in self:
            if tax.percentage_exoneration > 100:
                raise UserError(_("The percentage cannot be greater than 100"))

    # @api.depends("percentage_exoneration")
    # def tax_compute_exoneration(self):
    #     for tax in self:
    #         if tax.tax_root:
    #             _tax_amount = tax.tax_root.amount / 100
    #             _procentage = tax.percentage_exoneration / 100
    #             tax.amount = (_tax_amount * (1 - _procentage)) * 100

    @api.model
    def create_list(self):
        companies = self.env['res.company'].sudo().search([])
        for company in companies:
            if company.country_id.id != self.env.ref('base.cr').id:
                continue
            for ex in range(1, 14):
                tax = self.env['account.tax'].sudo().search([('percentage_exoneration', '=', ex),
                                                             ('is_exoneration', '=', True),
                                                             ('type_tax_use', '=', 'sale'),
                                                             ('company_id', '=', company.id)], limit=1)
                if tax:
                    _logger.info("Compañia: %s - Exoneración  de %s encontrada" % (company.name, ex))
                    continue

                if not tax:
                    tax = self.env['account.tax'].sudo().create({
                        'name': 'Exoneración %s %s' % (ex, '%'),
                        'description': 'Exoneración %s %s' % (ex, '%'),
                        'amount': -1 * ex,
                        'amount_type': 'percent',
                        'percentage_exoneration': int(ex) or 0,
                        'is_exoneration': True,
                        'type_tax_use': 'sale',
                        'company_id': company.id,
                        'country_id': self.env.ref('base.cr').id,
                        'invoice_repartition_line_ids': [
                            (0, 0, {
                                'factor_percent': 100,
                                'repartition_type': 'base',
                            }),

                            (0, 0, {
                                'factor_percent': 100,
                                'repartition_type': 'tax',
                            }),
                        ],
                        'refund_repartition_line_ids': [
                            (0, 0, {
                                'factor_percent': 100,
                                'repartition_type': 'base',
                            }),

                            (0, 0, {
                                'factor_percent': 100,
                                'repartition_type': 'tax',
                            }),
                        ],

                    })
                    if tax:
                        _logger.info("Compañia: %s - Exoneración  de %s CREADA" % (company.name, ex))
                    else:
                        _logger.info("Compañia: %s - Exoneración  de %s NO CREADA" % (company.name, ex))
