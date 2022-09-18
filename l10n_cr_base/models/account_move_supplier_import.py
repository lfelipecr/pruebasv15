# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

TYPE_PRODUCT = [('product_create', 'Crear producto en factura.'),
                ('product_no_create', 'No crear producto en factura.'),
                ('product_default', 'Asignar producto por defecto para factura.'),
                ('line_no_create', 'No crear líneas o  detalle en factura.')]

class AccountMoveSupplierConfig(models.Model):
    _name = "account.move.supplier.import"
    _inherit = ["mail.thread"]
    _description = "Configuracion para importar Facturas de Proveedor"
    _order = "sequence"

    sequence = fields.Integer()
    name = fields.Char(string=u"Descripción")
    company_id = fields.Many2one(comodel_name="res.company", string=u"Compañia", ondelete="cascade",default=lambda self: self.env.company)
    partner_id = fields.Many2one(comodel_name="res.partner", store=True, related='company_id.partner_id',string='Contacto relacionado')
    active = fields.Boolean(string="Activo?",default=True)

    server_id = fields.Many2one('fetchmail.server' ,string='Servidor de correo entrada')

    journal_id = fields.Many2one('account.journal',string='Diario proveedor')
    account_id = fields.Many2one(comodel_name="account.account",string="Cuenta de gasto",domain=[("deprecated", "=", False),])
    account_analytic_id = fields.Many2one(comodel_name="account.analytic.account",string=u'Cuenta analítica')
    tax_id = fields.Many2one(comodel_name="account.tax",string="Impuesto",domain=[("type_tax_use", "=", "purchase"),])

    line_type = fields.Selection(TYPE_PRODUCT, string='Se necesita', default='product_create', required=True)
    product_id = fields.Many2one(comodel_name="product.product",string="Producto")
    date_start = fields.Datetime(string='Fecha/Hora')

    supplier_payment_term = fields.Many2one('account.payment.term', string='Plazo de pago', copy=False)
    supplier_payment_method = fields.Many2one('payment.method', string='Método de pago', copy=False)

    _sql_constraints = [
        (
            "company_active_uniq",
            "UNIQUE(company_id, active)",
            "Solo puede haber una configuración activa por empresa.",
        ),
    ]






