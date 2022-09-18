# -*- coding: utf-8 -*-
from functools import partial

from odoo import _, fields, models, api
from odoo.exceptions import ValidationError, UserError
import requests
from datetime import datetime, date
import re
import logging
_logger = logging.getLogger(__name__)


class PartnerElectronic(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    has_exoneration = fields.Boolean(string='Tiene exoneración')
    exoneration_lines = fields.One2many('res.partner.exonerated','partner_id', string=u'Exoneración')
