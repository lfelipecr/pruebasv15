# -*- coding: utf-8 -*-
from odoo import fields, models


class AutorizationDocument(models.Model):
    _name = "autorization.document"
    _description = "Documento para autorizacion en exoneración"

    active = fields.Boolean(default=True)
    code = fields.Char()
    name = fields.Char()
