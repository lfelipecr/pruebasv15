from odoo import fields, models, api


class TypeDocument(models.Model):
    _name = "type.document"
    _description = "Tipo documento"
    _rec_name = 'name'
    _order = 'sequence'

    sequence = fields.Integer()
    active = fields.Boolean(required=False, default=True, string='Activo')
    name = fields.Char('Nombre')
    description = fields.Char(u'Descripción')
    code = fields.Char('Código')
    code_hacienda = fields.Char('Código hacienda')
    in_sale = fields.Boolean('En ventas')
    in_purchase = fields.Boolean('En compras')
