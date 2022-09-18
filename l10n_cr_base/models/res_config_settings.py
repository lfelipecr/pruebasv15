# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _name = 'res.config.settings'
    _inherit = 'res.config.settings'

    activity_ids = fields.Many2many(comodel_name="economic.activity", string="Actividades económicas",
                                    related='company_id.activity_ids',readonly=False)
    activity_default_id = fields.Many2one(comodel_name="economic.activity", string="Actividad económica por defecto",  store=True,
                                          related='company_id.activity_default_id', readonly=False)
    signature = fields.Binary(string="LLave Criptográfica", related='company_id.signature',  readonly=False)
    e_user = fields.Char(string="E-Usuario", related='company_id.e_user',  readonly=False)
    e_password = fields.Char(string="E-Contraseña", related='company_id.e_password',  readonly=False)
    e_environment = fields.Selection(selection=[("api-stag", _("Prueba")), ("api-prod", _("Producción")), ], string="Entorno",
                                       related='company_id.e_environment',  readonly=False)
    e_pin = fields.Char(string="Pin", help="Es el pin correspondiente al certificado.",related='company_id.e_pin',  readonly=False)


    # def _get_journal_e_sale(self):
    #     env_journal = self.env['account.journal'].sudo()
    #     return env_journal.search([('e_invoice_check', '=', True), ('type', '=', 'sale'), ('company_id', '=', self.company_id.id)], limit=1)

    journal_sale_id = fields.Many2one('account.journal', string='Diario e-ventas',related='company_id.journal_sale_id',  readonly=False,
                                      domain=[('type','=','sale')])

    # def _get_journal_e_purchase(self):
    #     env_journal = self.env['account.journal'].sudo()
    #     return env_journal.search([('e_invoice_check', '=', True), ('type', '=', 'purchase'), ('company_id', '=', self.company_id.id)], limit=1)

    purchase_sale_id = fields.Many2one('account.journal', string='Diaro e-compras',related='company_id.purchase_sale_id',  readonly=False,
                                       domain=[('type', '=', 'purchase')])

    send_hacienda = fields.Selection([('automatic', u'Automático'), ('manual', 'Manual')], default='automatic', related='company_id.send_hacienda',
                                     readonly=False)

    send_mail_to_customer = fields.Boolean(related='company_id.send_mail_to_customer', readonly=False) #Enviar mail al cliente cuando se aceptó el comprobante

    bill_supplier_import = fields.Boolean(string=u"Importación facturas electrónicas", related='company_id.bill_supplier_import', readonly=False)



    def create_journal_e_invoice(self):

        company_id = self.company_id
        env_journal = self.env['account.journal'].sudo()
        j_types = ['sale', 'purchase']
        value_fields = {
            'sale': ['E-Comprobantes Cliente','JEC',1000],
            'purchase': ['E-Comprobantes Proveedores','JEP',2000]
        }
        for jt in j_types:
            journal = env_journal.search([('e_invoice_check', '=', True), ('type', '=', jt), ('company_id', '=', company_id.id)])
            if not journal:
                journal = env_journal.create({
                    'name': value_fields[jt][0],
                    'code': value_fields[jt][1],
                    'type': jt,
                    'sequence': value_fields[jt][2],
                    'e_invoice_check': True,
                    'company_id': company_id.id
                })
            if jt == 'sale':
                self.update({'journal_sale_id': journal.id})
            elif jt == 'purchase':
                self.update({'purchase_sale_id': journal.id})



    def open_params_import_ininvoice(self):
        id=None
        config = self.env['account.move.supplier.import'].sudo().search([('company_id','=',self.company_id.id),('active','=',True)])
        if config:
            id = config.id

        return {
            'type': 'ir.actions.act_window',
            'name': u'Configuración',
            'view_mode': 'form',
            'res_model': 'account.move.supplier.import',
            'res_id': id,
            'target': 'current',
            'context': {
                'default_company_id': self.company_id.id,
                'form_view_initial_mode': 'edit',
            }
        }
