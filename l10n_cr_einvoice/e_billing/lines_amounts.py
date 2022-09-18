from odoo import _
from odoo.exceptions import ValidationError, UserError
import json

#FACTURACIÓN POS

def _pos_get_lines_xml(self, lineas):
    #Todo: DIGITOS
    digits = self.env.ref('l10n_cr_einvoice.fecr_amount_precision').digits

    lines = []
    i = 0

    def compute_monto_total(line):
        currency = line.order_id.currency_id
        price = line.price_unit
        line_discount_price_unit = price * (1 - (0 / 100.0))
        subtotal = line.qty * line_discount_price_unit
        return round(subtotal, digits)

    def compute_tax_total(line, sub_total):
        currency = line.order_id.currency_id
        tax_list = []
        total_impuesto = 0
        for tax in line.tax_ids_after_fiscal_position:
            j_tax = {
                'tax': tax,
                'codigo': tax.tax_code,
                'codigo_tarifa': tax.iva_tax_code,
                'tarifa': round(tax.amount, digits),
                'monto': round(sub_total * (tax.amount / 100), digits),
            }
            total_impuesto += j_tax['monto']
            tax_list.append(j_tax)

        return tax_list, round(total_impuesto, digits)

    for l in lineas:
        monto_total = compute_monto_total(l)
        monto_descuento = round(monto_total * (l.discount / 100), digits)
        sub_total = round(monto_total - monto_descuento, digits)
        impuestos, total_tax = compute_tax_total(l, sub_total)
        if l.product_id:
            codigo = l.product_id.cabys_id.code
            unidad_medida = l.product_id.uom_id.code
        else:
            codigo = False
            unidad_medida = False

        if l.product_id.type == 'service' and l.product_id.uom_id.category_id.name != 'Services':
            raise UserError(_("Para generar el xml es necesario que el producto:  {}  de tipo servicio, tenga una categoría en la unidad de medida "
                              "de tipo servicio").format(l.product_id.name))
        i += 1
        line_data = {
            'line': l,
            'numero_linea': i,
            'codigo': codigo,
            'cantidad': l.qty,
            'unidad_medida': unidad_medida,
            'detalle': l.name[:500],
            'precio_unitario': round(l.price_unit, digits),
            'monto_total': round(monto_total, digits),
            'discount': l.discount,
            'monto_descuento': monto_descuento,
            'naturaleza_descuento': 'Descuento Comercial',
            'sub_total': sub_total,
            'impuestos': impuestos,
            'impuesto_neto': round(total_tax, digits),
            'monto_total_linea': round(sub_total + total_tax, digits)

        }

        lines.append(line_data)

    return lines


def _pos_get_amounts(self, lines):
    """Totales"""
    self.ensure_one()
    # Todo: DIGITOS
    digits = self.env.ref('l10n_cr_einvoice.fecr_amount_precision').digits

    amounts = {
        "service_taxed": 0,
        "service_no_taxed": 0,
        "service_exempt": 0,  # TODO
        "product_taxed": 0,
        "product_no_taxed": 0,
        "product_exempt": 0,  # TODO
        "discount": 0,
        "other_charges": 0,  # TODO
        'total_venta': 0,
        'venta_neta': 0,
        'total_impuesto': 0,
    }

    for line in lines:
        amounts['discount'] += round(line['monto_descuento'], digits)
        line_type = "service" if line['line'].product_id.type == "service" else "product"
        is_tax = "taxed" if line['line'].tax_ids_after_fiscal_position else "no_taxed"
        amounts[line_type + "_" + is_tax] += round(line['monto_total'], digits)  # TODO Exempt
        amounts['total_impuesto'] += round(line['impuesto_neto'], digits)

    amounts['total_gravado'] = round((amounts["service_taxed"] + amounts["product_taxed"]), digits)
    amounts['total_exento'] = round((amounts["service_no_taxed"] + amounts["product_no_taxed"]), digits)
    amounts['total_exonerado'] = round((amounts["service_exempt"] + amounts["product_exempt"]), digits)
    amounts['total_venta'] = round((amounts["service_taxed"] + amounts["service_no_taxed"] + amounts["service_exempt"] + amounts["product_taxed"] + amounts["product_no_taxed"] + amounts["product_exempt"]), digits)
    amounts['venta_neta'] = round(amounts['total_venta'], digits) - round(amounts["discount"], digits)
    amounts['total_comprobante'] = round(amounts['venta_neta'] + amounts['total_impuesto'], digits)

    return amounts



#FACTURACIÓN

def _get_lines_xml(self, lineas):
    #Todo: DIGITOS
    digits = self.env.ref('l10n_cr_einvoice.fecr_amount_precision').digits

    lines = []
    i = 0

    exo = self.partner_has_exoneration
    exoneration_lines = self.partner_exoneration_ids

    def compute_monto_total(line):
        currency = line.move_id.currency_id
        price = line.price_unit
        line_discount_price_unit = price * (1 - (0 / 100.0))
        subtotal = line.quantity * line_discount_price_unit
        return round(subtotal, digits)

    def compute_tax_total(line, sub_total):
        currency = line.move_id.currency_id
        tax_list = []
        total_impuesto = 0
        for tax in line.tax_ids:
            if tax.is_exoneration:
                continue
            has_exoneration = False
            e_tipo_documento = False
            e_numero_documento = False
            e_nombre_institucion = False
            e_fecha_emision = False
            e_procentaje_exoneracion = False
            e_monto_exoneracion = False
            j_tax = {
                'tax': tax,
                'codigo': tax.tax_code,
                'codigo_tarifa': tax.iva_tax_code,
                'tarifa': round(tax.amount,digits),
                'monto': round(sub_total * (tax.amount/100), digits),
            }
            total_monto_exoneracion = 0.0
            if exo and exoneration_lines:
                has_exoneration = True
                decimals_e, exoneration = _get_exoneration(exoneration_lines, line.product_id, digits, tax.tax_code) #Decimales de exoneración
                e_tipo_documento = exoneration.tipo_documento.code
                e_numero_documento = exoneration.numero_documento
                e_nombre_institucion = exoneration.institucion
                e_fecha_emision = exoneration.date_issue
                e_procentaje_exoneracion = exoneration.porcentaje_exoneracion
                e_monto_exoneracion = round(sub_total * (exoneration.porcentaje_exoneracion / 100), digits)
                total_monto_exoneracion += e_monto_exoneracion

            j_tax.update({
                'has_exoneration': has_exoneration,
                'exoneration': {
                    'tipo_documento': e_tipo_documento,
                    'numero_documento': e_numero_documento,
                    'nombre_institucion': e_nombre_institucion,
                    'fecha_emision': e_fecha_emision,
                    'procentaje_exoneracion': int(e_procentaje_exoneracion),
                    'monto_exoneracion': e_monto_exoneracion,
                }
            })


            total_impuesto += (j_tax['monto'] - total_monto_exoneracion)
            tax_list.append(j_tax)

        return tax_list, round(total_impuesto,digits)

    for l in lineas:
        if l.display_type in ('line_section', 'line_note'):
            continue
        monto_total = compute_monto_total(l)
        monto_descuento = round(monto_total * (l.discount/100), digits)
        sub_total = round(monto_total - monto_descuento,digits)
        impuestos, total_tax = compute_tax_total(l, sub_total)
        if not l.product_id and l.move_id.move_type in ('in_invoice', 'in_refund') and l.info_json:
            js_dict = json.loads(l.info_json)
            codigo = js_dict['codigo']
            unidad_medida = js_dict['unidad_medida']
        elif l.product_id:
            codigo = l.product_id.cabys_id.code
            unidad_medida = l.product_id.uom_id.code
        else:
            codigo = False
            unidad_medida = False

        if l.product_id.type == 'service' and l.product_id.uom_id.category_id.name != 'Services':
            raise UserError(_("Para generar el xml es necesario que el producto:  {}  de tipo servicio, tenga una categoría en la unidad de medida "
                              "de tipo servicio").format(l.product_id.name))

        line_data = {
            'line': l,
            'numero_linea': i + 1,
            'codigo': codigo,
            'cantidad': l.quantity,
            'unidad_medida': unidad_medida,
            'detalle': l.name[:500],
            'precio_unitario': round(l.price_unit, digits),
            'monto_total': round(monto_total, digits),
            'discount': l.discount,
            'monto_descuento': monto_descuento,
            'naturaleza_descuento': l.discount_note or 'Descuento Comercial',
            'sub_total': sub_total,
            'impuestos': impuestos,
            'impuesto_neto': round(total_tax,digits),
            'monto_total_linea': round(sub_total + total_tax, digits)

        }

        lines.append(line_data)

    return lines


def _get_amounts(self, lines):
    """Totales"""
    self.ensure_one()
    # Todo: DIGITOS
    digits = self.env.ref('l10n_cr_einvoice.fecr_amount_precision').digits

    amounts = {
        "service_taxed": 0,
        "service_no_taxed": 0,
        "service_exempt": 0,  # TODO
        "product_taxed": 0,
        "product_no_taxed": 0,
        "product_exempt": 0,  # TODO
        "discount": 0,
        "other_charges": 0,  # TODO
        'total_venta': 0,
        'venta_neta': 0,
        'total_impuesto': 0,
    }
    exo = self.partner_has_exoneration
    exoneration_lines = self.partner_exoneration_ids


    for line in lines:
        amounts['discount'] += round(line['monto_descuento'], digits)
        line_type = "service" if line['line'].product_id.type == "service" else "product"
        is_tax = "taxed" if line['line'].tax_ids else "no_taxed"
        if exo and exoneration_lines:
            #amount = round(self.exoneration_cal() * round(line['monto_total'], digits), digits)
            decimals, exoneration = _get_exoneration(exoneration_lines, line['line'].product_id, digits, False)
            amount = round(decimals * round(line['monto_total'], digits), digits)
            amounts[line_type + "_" + is_tax] += round(amount,digits)
            amounts[line_type + "_exempt"] += round(line['monto_total'] - amount, digits)
        else:
            amounts[line_type + "_" + is_tax] += round(line['monto_total'], digits)  # TODO Exempt

        amounts['total_impuesto'] += round(line['impuesto_neto'], digits)
    total_venta_neta = self.amount_untaxed
    total_impuesto = self.amount_tax
    total_comprobante = self.amount_total

    amounts['total_gravado'] = round((amounts["service_taxed"] + amounts["product_taxed"]),digits)
    amounts['total_exento'] = round((amounts["service_no_taxed"] + amounts["product_no_taxed"]),digits)
    amounts['total_exonerado'] = round((amounts["service_exempt"] + amounts["product_exempt"]),digits)
    amounts['total_venta'] = round((amounts["service_taxed"] + amounts["service_no_taxed"] + amounts["service_exempt"] + amounts["product_taxed"] + amounts["product_no_taxed"] + amounts["product_exempt"]), digits)
    amounts['venta_neta'] = round(amounts['total_venta'], digits) - round(amounts["discount"], digits)
    amounts['total_comprobante'] = round(amounts['venta_neta'] + amounts['total_impuesto'], digits)

    return amounts


def _get_exoneration(exoneration_lines, product_id, digits, tax_code):
    product_cabys_id = product_id.cabys_id
    if not product_cabys_id:
        raise ValidationError(_("El producto %s no tiene un cabys configurado." % (product_id.name)))

    exoneration = False
    for e in exoneration_lines:
        cabys = e.cabys_ids.filtered(lambda c:c.id == product_cabys_id.id)
        if cabys:
            exoneration = e
            break
    decimals = 0.0
    #amount = 0.0
    if exoneration:
        #FORMULA
        # 1 - (PORCENTAJE EXONERACION(INT) / PORCENTAJE DE IMPUESTO(INT)) => 1 - (10/13)
        if tax_code:
            tax_ids = product_cabys_id.taxes_ids.filtered(lambda t: t.type_tax_use == 'sale' and t.tax_code == tax_code)
        else:
            tax_ids = product_cabys_id.taxes_ids.filtered(lambda t:t.type_tax_use == 'sale' and t.tax_code != '')
        if tax_ids:
            tax_id = tax_ids[0]
            percentage = exoneration.porcentaje_exoneracion / tax_id.amount
            decimals = round(1 - percentage, digits)
            #amount = line['monto_total'] * decimals

    return decimals, exoneration
