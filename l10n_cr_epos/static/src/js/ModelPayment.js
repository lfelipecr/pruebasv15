odoo.define('l10n_cr_epos.ModelPayment', function(require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const session = require('web.session');
    const { useListener } = require('web.custom_hooks');
    var models = require('point_of_sale.models');
    var SuperPaymentline = models.Paymentline.prototype;

     models.Paymentline = models.Paymentline.extend({
        initialize: function () {
            SuperPaymentline.initialize.apply(this, arguments);
            this.complete_data = false;
            this.is_other_currency = false;
            this.amount_currency = false;
            this.amount_currency_real = false;
            this.currency_other_id = false;
            this.change_rate = false;
        },

         set_complete_data: function(value){
            this.complete_data = value
         },

         set_is_other_currency: function(value){
            this.is_other_currency = value
         },

         get_is_other_currency: function(is_other_currency){
			return this.is_other_currency;
		 },

         set_amount_currency: function(value){
            this.amount_currency = value
         },

         get_amount_currency: function(amount_currency){
			return this.amount_currency;
		 },

		 set_amount_currency_real: function(value){
            this.amount_currency_real = value
         },

         get_amount_currency_real: function(amount_currency_real){
			return this.amount_currency_real;
		 },

         set_currency_other_id: function(value){
            this.currency_other_id = value
         },

         get_currency_other_id: function(currency_other_id){
			return this.currency_other_id;
		 },

		 set_change_rate: function(value){
            this.change_rate = value
         },

         get_change_rate: function(change_rate){
			return this.change_rate;
		 },

		 export_as_JSON: function() {
		    var self = this;
			var res = SuperPaymentline.export_as_JSON.apply(this, arguments);
			res.is_other_currency =  this.get_is_other_currency();
			res.amount_currency = this.get_amount_currency();
			res.amount_currency_real = this.get_amount_currency_real();
			res.currency_other_id = this.get_currency_other_id();
			res.change_rate = this.get_change_rate();
			return res;
		},


     });

});
