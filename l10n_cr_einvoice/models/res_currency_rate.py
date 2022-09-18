from datetime import datetime
import bs4
import requests

from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)

# TODO Analyze if EUR necessary
CRC_USD_RATE_API = "https://api.hacienda.go.cr/indicadores/tc/dolar"

URL_BCR = 'https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?idioma=1&CodCuadro=%20400'

class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    rate_purchase = fields.Float(digits=0,group_operator="avg", help='The rate of the currency to the currency of rate 1', string='Technical Rate Purchase')

    @api.model
    def update_crc_usd_rate(self):
        res = requests.get(URL_BCR)
        soup = bs4.BeautifulSoup(res.content, 'lxml')
        table = soup.find_all('table')[1]
        tr = table.find_all('tr')[2]
        #venta
        table3 = tr.find_all('table')[3]
        table_content_sale = table3.find_all('tr')[3:]
        td_sale = table_content_sale[len(table_content_sale) - 1].text
        value_sale = td_sale.strip().replace(',', '.')
        rate_sale = float(value_sale)
        #compra
        table2 = tr.find_all('table')[2]
        table_content_purchase = table2.find_all('tr')[3:]
        td_purchase = table_content_purchase[len(table_content_purchase) - 1].text
        value_purchase = td_purchase.strip().replace(',', '.')
        rate_purchase = float(value_purchase)


        now = datetime.now().date()
        crc_currency = self.env.ref("base.CRC")
        usd_currency = self.env.ref("base.USD")
        for company in self.env["res.company"].search([]):
            if company.currency_id != crc_currency:
                continue
            current_rate = self.search([("company_id", "=", company.id), ("currency_id", "=", usd_currency.id), ("name", "=", now), ], limit=1, )
            crc_to_usd_sale = 1 / rate_sale
            crc_to_usd_purchase = 1 / rate_purchase
            if current_rate:
                current_rate.rate = crc_to_usd_sale
            else:
                self.sudo().create({"company_id": company.id, "currency_id": usd_currency.id, "name": now, "rate": crc_to_usd_sale, 'rate_purchase': crc_to_usd_purchase})
        _logger.info("Fecha: %s - Tipo de cambio %s" % (now, rate_sale))
