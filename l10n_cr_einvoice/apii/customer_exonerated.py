# -*- coding: utf-8 -*-

from odoo import _
from odoo.exceptions import ValidationError
import requests
from datetime import datetime, date, timedelta
import pytz

url = 'https://api.hacienda.go.cr/fe/ex?autorizacion='


def find_data(self):
    res = {}
    url_compound = url + self.numero_documento

    try:
        result = requests.get(url_compound)
    except Exception as e:
        raise ValidationError(_("Error: %s " % e))

    try:
        if result.status_code == 200:
            json = result.json()
            identification = json['identificacion']
            numeroDocumento = json['numeroDocumento']
            if self.vat != False and self.vat != identification:
                res['warning'] = {'title': _('Ups'), 'message': _(
                    'El número de identificación encontrado, no conincide con el número de documento del cliente.')}
                return res

            code_type_exoneration = json['tipoDocumento']['codigo']
            type_ex = self.env['autorization.document'].sudo().search([('code', '=', code_type_exoneration)])
            if not type_ex:
                res['warning'] = {'title': _('Ups'), 'message': _(
                    'No se encuentra el tipo de exoneración. Contacte al administrador del sistema!')}
                return res
            institution_name = json['nombreInstitucion']
            fecha_emision = json['fechaEmision']
            fecha_vencimiento = json['fechaVencimiento']
            percentage_exoneration = json['porcentajeExoneracion']
            identificacion = json['identificacion']

            # tax = percentage_exoneration
            tax = self.env['account.tax'].sudo().search([('percentage_exoneration', '=', percentage_exoneration),
                                                         ('is_exoneration', '=', True),
                                                         ('type_tax_use', '=', 'sale'),
                                                         ('company_id', '=', self.env.company.id)], limit=1)
            if not tax:
                tax = self.env['account.tax'].sudo().create({
                    'name': 'Exoneración %s %s' % (percentage_exoneration, '%'),
                    'description': 'Exoneración %s %s' % (percentage_exoneration, '%'),
                    'amount': -1 * percentage_exoneration,
                    'amount_type': 'percent',
                    'percentage_exoneration': int(percentage_exoneration) or 0,
                    'is_exoneration': True,
                    'type_tax_use': 'sale',
                    'company_id': self.env.company.id,
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

            cabys_ids = False
            if json['poseeCabys']:
                cabys_ids = self.env['cabys'].sudo().search([('code', 'in', json['cabys'])]).ids

            fe = datetime.strptime(fecha_emision, '%Y-%m-%dT%H:%M:%S') + timedelta(hours=5)
            fv = datetime.strptime(fecha_vencimiento, '%Y-%m-%dT%H:%M:%S') + timedelta(hours=5)
            data = {
                'partner_id': self.partner_id.id,
                'vat': identificacion,
                'numero_documento': numeroDocumento,
                # 'tax_id': tax.id,
                'porcentaje_exoneracion': percentage_exoneration,
                'cabys_ids': cabys_ids,
                'tipo_documento': type_ex,
                'fecha_emision': fe,
                'fecha_vencimiento': fv,
                'institucion': institution_name,
                'date_issue': fecha_emision,
                'date_expiration': fecha_vencimiento,
                'tax_sale_id': tax.id
            }

            return data


        else:
            res['warning'] = {'title': _('Ups'), 'message': _('Documento de exoneración no encontrado !')}
            return res
    except Exception as e:
        raise ValidationError(_("Advertencia: %s", e))
