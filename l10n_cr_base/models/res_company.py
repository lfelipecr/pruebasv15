import logging

from odoo import fields, models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = ["res.company", "mail.thread"]

    activity_ids = fields.Many2many(comodel_name="economic.activity", string="Actividades económicas")
    activity_default_id = fields.Many2one(comodel_name="economic.activity", string="Actividad económica por defecto", store=True)
    signature = fields.Binary(string="LLave Criptográfica")
    e_user = fields.Char(string="E-Usuario")
    e_password = fields.Char(string="E-Contraseña")
    e_environment = fields.Selection(selection=[("api-stag", _("Prueba")), ("api-prod", _("Producción")), ], string="Entorno")
    e_pin = fields.Char(string="Pin", help="Es el pin correspondiente al certificado.")

    journal_sale_id = fields.Many2one('account.journal', string='Diario e-ventas')
    purchase_sale_id = fields.Many2one('account.journal', string='Diaro e-compras')

    identification_id = fields.Many2one(comodel_name="identification.type", string="Tipo identificación",)

    send_hacienda = fields.Selection([('automatic', u'Automático'), ('manual', 'Manual')], default='automatic')

    send_mail_to_customer = fields.Boolean()

    bill_supplier_import = fields.Boolean(string=u"Importación facturas electrónicas")


    def first_company(self):
        country_id = self.env.ref('base.cr').id
        company = self.env['res.company'].sudo().search([('chart_template_id', '!=', False),
                                                         ('country_id', '=', country_id)], order='id asc', limit=1)
        return company

    def assign_chart_template_id_cr(self):
        self.ensure_one()

        company = self.first_company()
        if company:
            self.sudo().write({'chart_template_id': company.chart_template_id.id})
            _logger.info("Plan contable con ID %s - Asignado" % company.chart_template_id.id)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Plan contable asignado correctamente a esta compañia ! "),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            raise UserError(_("No existe información de una compañía inicial"))

    def assign_tax_ids_cr(self):
        self.ensure_one()

        company = self.first_company()
        if company:
            tax_ids = self.env['account.tax'].sudo().search([('is_exoneration', '=', False),
                                                             ('active', '=', True),
                                                             ('company_id', '=', company.id)])
            if tax_ids:
                for tax in tax_ids:
                    invoice_repartition_line_ids = tax.mapped('invoice_repartition_line_ids')
                    refund_repartition_line_ids = tax.mapped('refund_repartition_line_ids')

                    tax_list_invoice_lines = []
                    if invoice_repartition_line_ids:
                        for r in invoice_repartition_line_ids:
                            account_id = False
                            if r.account_id:
                                account_id = self.env['account.account'].sudo().search([('code','=', r.account_id.code),('company_id','=', self.ids[0])], limit=1)
                            data = {'factor_percent': r.factor_percent,
                                    'repartition_type': r.repartition_type,
                                    'account_id': account_id.id if account_id else account_id
                                    }
                            tax_list_invoice_lines.append((0, 0, data))

                    tax_list_refund_lines = []
                    if refund_repartition_line_ids:
                        for r2 in refund_repartition_line_ids:
                            account_id = False
                            if r2.account_id:
                                account_id = self.env['account.account'].sudo().search([('code', '=', r2.account_id.code), ('company_id', '=', self.ids[0])], limit=1)
                            data_r = {'factor_percent': r2.factor_percent,
                                      'repartition_type': r2.repartition_type,
                                      'account_id': account_id.id if account_id else account_id
                                      }

                            tax_list_refund_lines.append((0, 0, data_r))


                    new_tax = tax.copy(default={'company_id': self.ids[0],
                                                'name': tax.name,
                                                'invoice_repartition_line_ids': tax_list_invoice_lines,
                                                'refund_repartition_line_ids': tax_list_refund_lines,
                                                })
                    if new_tax:
                        _logger.info("Impuesto auto creado con ID : %s" % new_tax.id)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'success',
                        'message': _("Se crearon los impuestos correctamente ! "),
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }






