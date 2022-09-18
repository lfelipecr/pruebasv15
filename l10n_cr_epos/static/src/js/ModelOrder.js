odoo.define('l10n_cr_epos.ModelOrder', function(require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const session = require('web.session');
    const { useListener } = require('web.custom_hooks');
    var models = require('point_of_sale.models');


    models.PosModel = models.PosModel.extend({
        f_code_document_type: function () {
            return true;
        },
    });

    var PosOrderSuper = models.Order.prototype;
	models.Order = models.Order.extend({
		initialize: function(attr, options) {
			this.to_send = this.to_send || false;
			this.is_return = this.is_return || false;
			this.order_id = this.order_id || false;
			PosOrderSuper.initialize.call(this,attr,options);
		},
		export_for_printing: function () {
            var result = PosOrderSuper.export_for_printing.apply(this, arguments);
            result.code_document_type = this.get_code_document_type();
            result.number_electronic = this.get_number_electronic();
            result.electronic_sequence = this.get_electronic_sequence();
            result.to_send = this.get_to_send();
            result.is_return = this.get_is_return();
            result.order_id = this.get_order_id();
            return result;
        },

		export_as_JSON: function(){
			var loaded = PosOrderSuper.export_as_JSON.apply(this, arguments);
			loaded.to_send = this.to_send || false;
			loaded.is_return = this.is_return || false;
			loaded.order_id = this.order_id || false;
			return loaded;
		},
        set_to_send: function (to_send) {
            this.to_send = to_send;
        },
        get_to_send: function () {
            return this.to_send;
        },
        set_code_document_type: function (code_document_type) {
            this.code_document_type = code_document_type;
        },
        get_code_document_type: function () {
            return this.code_document_type;
        },

        set_number_electronic: function (number_electronic) {
            this.number_electronic = number_electronic;
        },
        get_number_electronic: function () {
            return this.number_electronic;
        },

        set_electronic_sequence: function (electronic_sequence) {
            this.electronic_sequence = electronic_sequence;
        },
        get_electronic_sequence: function () {
            return this.electronic_sequence;
        },

        set_is_return: function (is_return) {
            this.is_return = is_return;
        },
        get_is_return: function () {
            return this.is_return;
        },

        set_order_id: function (order_id) {
            this.order_id = order_id;
        },
        get_order_id: function () {
            return this.order_id;
        },

        //MÉTODO PARA CONSULTAR
        wait_for_push_order: function () {
            var result = PosOrderSuper.wait_for_push_order.apply(this, arguments);
            result = Boolean(result || this.pos.f_code_document_type());
            return result;
        },


	});

});
