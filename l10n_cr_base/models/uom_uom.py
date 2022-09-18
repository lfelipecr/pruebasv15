# -*- coding: utf-8 -*-
from odoo import fields, models, api


class UoM(models.Model):
    _inherit = "uom.uom"

    code = fields.Char(string=u'Código')

    @api.model
    def update_unit_measures(self):
        product_uom_cm = self.env.ref('uom.product_uom_cm')
        product_uom_cm.write({'name':'Centímetro', 'code': 'cm'})

        product_uom_day = self.env.ref('uom.product_uom_day')
        product_uom_day.write({'name':'Día(s)', 'code': 'd'})

        product_uom_gram = self.env.ref('uom.product_uom_gram')
        product_uom_gram.write({'name': 'Gramo', 'code': 'g'})

        product_uom_gal = self.env.ref('uom.product_uom_gal')
        product_uom_gal.write({'name': 'Galón', 'code': 'Gal'})

        product_uom_kgm = self.env.ref('uom.product_uom_kgm')
        product_uom_kgm.write({'name': 'Kilogramo', 'code': 'kg'})

        product_uom_litre = self.env.ref('uom.product_uom_litre')
        product_uom_litre.write({'name': 'Litro', 'code': 'L'})

        product_uom_inch = self.env.ref('uom.product_uom_inch')
        product_uom_inch.write({'name': 'Pulgada', 'code': 'ln'})

        product_uom_meter = self.env.ref('uom.product_uom_meter')
        product_uom_meter.write({'name': 'Metro', 'code': 'm'})

        product_uom_oz = self.env.ref('uom.product_uom_oz')
        product_uom_oz.write({'name': 'Onzas', 'code': 'Oz'})

        product_uom_ton = self.env.ref('uom.product_uom_ton')
        product_uom_ton.write({'name': 'Tonelada', 'code': 't'})

        product_uom_unit = self.env.ref('uom.product_uom_unit')
        product_uom_unit.write({'name': 'Unidad', 'code': 'Unid'})

        product_uom_qt = self.env.ref('uom.product_uom_qt')
        product_uom_qt.write({'name': 'Cuarto(s) de Galón', 'code': 'cuarto(s) de galón'})

        product_uom_dozen = self.env.ref('uom.product_uom_dozen')
        product_uom_dozen.write({'name': 'Docena(s)', 'code': 'Docena(s)'})

        product_uom_floz = self.env.ref('uom.product_uom_floz')
        product_uom_floz.write({'name': 'fl oz', 'code': 'fl oz'})

        product_uom_lb = self.env.ref('uom.product_uom_lb')
        product_uom_lb.write({'name': 'Libra(s)', 'code': 'libra(s)'})

        product_uom_mile = self.env.ref('uom.product_uom_mile')
        product_uom_mile.write({'name': 'Milla(s)', 'code': 'milla(s)'})

        product_uom_foot = self.env.ref('uom.product_uom_foot')
        product_uom_foot.write({'name': 'Pie(s)', 'code': 'pie(s)'})





