odoo.define('l10n_cr_epos.ModelFields', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('pos.config', ['used_invoice']);
    models.load_fields('pos.payment.method', ['payment_method_id','account_payment_term_id','is_refund']);
    models.load_fields('res.company', ['county_id','district_id','neighborhood_id']);
    models.load_fields('res.partner', ['identification_id','county_id','district_id','neighborhood_id','payment_methods_id']);

    models.load_fields('pos.payment', ['is_other_currency','amount_currency','amount_currency_real', 'currency_other_id','change_rate']);

    models.load_models([{
        model:  'identification.type',
        fields: ['code','name','notes'],
        loaded: function(self, identification){
            self.list_identification = identification;
            for(var i=0;i<identification.length;i++){
                self.list_identification[i] = identification[i];
            }
        },
    }]);

    models.load_models([{
        model:  'res.country.county',
        fields: ['code','name','state_id'],
        loaded: function(self, county){
            self.list_county = county;

        },
    }]);

    models.load_models([{
        model:  'res.country.district',
        fields: ['code','name','county_id'],
        loaded: function(self, district){
            self.list_district = district;

        },
    }]);

    models.load_models([{
        model:  'res.country.neighborhood',
        fields: ['code','name','district_id'],
        loaded: function(self, neighborhood){
            self.list_neighborhood = neighborhood;
        },
    }]);

     models.load_models([{
        model:  'account.payment.term',
        fields: ['name','active','line_ids','company_id'],
        loaded: function(self, payment_term){
            self.list_payment_terms_ids = payment_term;
        },
    }]);

    models.load_models([{
        model:  'payment.method',
        fields: ['active','name','notes'],
        loaded: function(self, payment_methods){
            self.list_payment_methods_ids = payment_methods;
        },
    }]);

     models.load_models({
		model: 'res.currency',
		fields: ['name','symbol','position','rounding','rate'],
        domain: function(self) {
			return [
				['id', 'in', self.config.currency_ids]
			];
		},
		loaded: function(self, currencies_ids){
			self.currencies_ids = currencies_ids;
		},
	});

});
