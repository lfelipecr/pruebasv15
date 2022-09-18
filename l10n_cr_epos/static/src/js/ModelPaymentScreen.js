odoo.define('l10n_cr_epos.ModelPaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const PaymentScreenPaymentLines = require('point_of_sale.PaymentScreenPaymentLines');
    const Registries = require('point_of_sale.Registries');
    const session = require('web.session');
    const { useListener } = require('web.custom_hooks');
    var models = require('point_of_sale.models');
    const NumberBuffer = require('point_of_sale.NumberBuffer');

     const PaymentScreenPaymentLinesExtend = PaymentScreenPaymentLines =>
		class extends PaymentScreenPaymentLines {
		    formatLineAmount(paymentline) {
		        if(paymentline.is_other_currency){
		            return this.env.pos.format_currency_no_symbol(paymentline.get_amount_currency_real());
		        }
                else{
                    return this.env.pos.format_currency_no_symbol(paymentline.get_amount());
                }
            }
		}

	Registries.Component.extend(PaymentScreenPaymentLines, PaymentScreenPaymentLinesExtend);

    const PaymentScreenCR= PaymentScreen =>
        class extends PaymentScreen {

            constructor() {
				super(...arguments);
				this.show_to_send_hacienda = this.show_to_send();
				useListener('envio-hacienda', this.to_send_action);
				this.multi_currency = this.show_multi_currency();
			}

			show_multi_currency(){
                var self = this;
                var multi_currency = self.env.pos.config.multi_currency;
                return multi_currency;
            }

            deletePaymentLine(event) {
                super.deletePaymentLine(event);
                let pos_currency = this.env.pos.currency;
                $('.drop-currency').val(pos_currency.id);
                //$('.drop-currency').change();
            }

			show_to_send(){
                var self = this;
                var envio = self.env.pos.config.show_send_hacienda;
                return envio;
            }
			to_send_action() {
                var self = this;
                var order = this.env.pos.get_order();
                var check_sent_hacienda = $("#check_sent_hacienda")[0].checked;
                var to_sent = false;
                if (check_sent_hacienda && self.show_to_send_hacienda){
                    to_sent = true;
                }
                order.set_to_send(to_sent); //Enviar?
                console.log("Enviar a hacienda ? " + to_sent)

			}

            async _postPushOrderResolve(order, order_server_ids) {
                try {
                    if (this.env.pos.f_code_document_type()) {
                        const result = await this.rpc({
                            model: 'pos.order',
                            method: 'search_order',
                            args: [order.uid],
                        });
                        order.set_code_document_type(JSON.parse(result).code_document_type || false);
                        order.set_electronic_sequence(JSON.parse(result).electronic_sequence || false);
                        order.set_number_electronic(JSON.parse(result).number_electronic || false);
                        //Imprime en consola.
                        console.log(JSON.parse(result).code_document_type || false)
                        console.log(JSON.parse(result).electronic_sequence || false)
                        console.log(JSON.parse(result).number_electronic || false)
                    }
                } finally {
                    return super._postPushOrderResolve(...arguments);
                }
            }


            validaciones_einvoice(){
                 //Validaciones en POS para facturación electrónica costa rica.
                 var t = this;
                 var currentOrder = t.currentOrder;
                 var currentOrder_client = currentOrder.changed.client;
                 var company_id = t.env.pos.company;
                 var pos_config = t.env.pos.config;

                 if ((company_id.e_environment != undefined || company_id.e_environment != false) && pos_config.used_invoice == true){
                     //Validación para la compañia
                     if(company_id.phone == undefined || company_id.phone == false){
                        swal('Aviso.','La compañia debe tener un número de teléfono !','info');
                        return false;
                     }
                     if(company_id.state_id == undefined || company_id.state_id == false){
                        swal('Aviso.','La compañia debe tener una provincia !','info');
                        return false;
                     }
                      if(company_id.county_id == undefined || company_id.county_id == false){
                        swal('Aviso.','La compañia debe tener un cantón !','info');
                        return false;
                      }
                      if(company_id.district_id == undefined || company_id.district_id == false){
                        swal('Aviso.','La compañia debe tener un distrito !','info');
                        return false;
                      }
                      if(company_id.neighborhood_id == undefined || company_id.neighborhood_id == false){
                        swal('Aviso.','La compañia debe tener un barrio !','info');
                        return false;
                      }

                     //Validación para la configuración de POS

                     if(pos_config.sucursal == undefined || pos_config.sucursal == false){
                        swal('Aviso.','La configuración del POS debe tener una sucursal !','info');
                        return false;
                     }
                     if(pos_config.terminal == undefined || pos_config.terminal == false){
                        swal('Aviso.','La configuración del POS debe tener un terminal !','info');
                        return false;
                     }
                      if(pos_config.e_sequence_id == undefined || pos_config.e_sequence_id == false){
                        swal('Aviso.','La configuración del POS debe tener una secuencia para facturación !','info');
                        return false;
                     }
                      if(pos_config.lines_sequences == undefined || pos_config.lines_sequences == false){
                         swal('Aviso.','La configuración del POS debe tener una secuencia para facturación por tipo de comprobante !','info');
                        return false;
                     }

                    //Validación para la el cliente
                     if(currentOrder_client && company_id){
                        var currentOrder_client_id = currentOrder_client.id;
                        if (currentOrder_client_id == company_id.id){
                            swal('Sugerencia.','Asegúrese que el cliente seleccionado sea diferente a la compañia !','info');
                            return false;
                        }

                         //Validación para la compañia
                         if(currentOrder_client.phone == undefined || currentOrder_client.phone == false){
                            swal('Aviso.','El cliente debe tener un número de teléfono !','info');
                            return false;
                         }
                         if(currentOrder_client.state_id == undefined || currentOrder_client.state_id == false){
                            swal('Aviso.','El cliente debe tener una provincia !','info');
                            return false;
                         }
                          if(currentOrder_client.county_id == undefined || currentOrder_client.county_id == false){
                            swal('Aviso.','El cliente debe tener un cantón !','info');
                            return false;
                          }
                          if(currentOrder_client.district_id == undefined || currentOrder_client.district_id == false){
                            swal('Aviso.','El cliente debe tener un distrito !','info');
                            return false;
                          }
                          if(currentOrder_client.neighborhood_id == undefined || currentOrder_client.neighborhood_id == false){
                            swal('Aviso.','El cliente debe tener un barrio !','info');
                            return false;
                          }
                          if(currentOrder_client.email == undefined || currentOrder_client.email == false){
                            swal('Aviso.','El cliente debe tener un email !','info');
                            return false;
                          }
                          if(currentOrder_client.identification_id == undefined || currentOrder_client.identification_id == false){
                            swal('Aviso.','El cliente debe tener un tipo de identificación/documento !','info');
                            return false;
                          }
                          if(currentOrder_client.vat == undefined || currentOrder_client.vat == false){
                            swal('Aviso.','El cliente debe tener un número de identificación/documento !','info');
                            return false;
                          }
                     }

                     //Validación para las opciones de pago
                     var paymentlines = currentOrder.paymentlines;
                     if(paymentlines){
                        for(var i=0; i < paymentlines.models.length; i++){
                            var paid = paymentlines.models[i];
                            if (paid){
                                var payment_method = paid.payment_method;
                                if(payment_method){
                                    if(payment_method.account_payment_term_id == undefined || payment_method.account_payment_term_id == false){
                                        swal('Revisar.','Estimado usuario, es necesario que la opción de pago seleccionado tenga configurado un término de pago','info');
                                        return false;
                                    }
                                    if(payment_method.account_payment_term_id == undefined || payment_method.account_payment_term_id == false){
                                        swal('Revisar.','Estimado usuario, es necesario que la opción de pago seleccionado tenga configurado un método de pago','info');
                                        return false;
                                    }
                                }
                            }
                        }
                     }

                     return true; //En caso no haya ningún problema con las validaciones retorna True
                 }else{
                    return true
                 }
            }

            mapped_refund_order(){
                var t = this;
                var currentOrder = t.currentOrder;
                var order_lines = currentOrder.orderlines;
                var resume_lines = order_lines.models;
                var lines_return_ids = [];
                var toRefundLines = t.env.pos.toRefundLines;
                if(resume_lines.length > 0){
                    for(var x=0; x < resume_lines.length; x++){
                        if (resume_lines[x].refunded_orderline_id != undefined ){
                            lines_return_ids.push(resume_lines[x].refunded_orderline_id);
                        }
                    }

                    var orderBackendId = false;
                    if(lines_return_ids.length > 0 && toRefundLines){
                        for(var y=0; y < lines_return_ids.length ; y++){
                            var ide = lines_return_ids[y];
                            if(toRefundLines[ide] != false || toRefundLines != {}){
                                if (toRefundLines[ide].orderline != false){
                                    var line_incl = toRefundLines[ide].orderline;
                                    if(line_incl.orderBackendId != false){
                                        orderBackendId = line_incl.orderBackendId;
                                        break;
                                    }
                                }
                            }
                        }
                    }

                    if(orderBackendId){
                        currentOrder.set_order_id(orderBackendId);
                        currentOrder.set_is_return(true);
                    }else{
                        currentOrder.set_order_id(false);
                        currentOrder.set_is_return(false);
                    }

                }
                else{
                    currentOrder.set_order_id(false);
                    currentOrder.set_is_return(false);
                }

            }

            async validateOrder(isForceValidate) {
                 var t = this;
                 var res = t.validaciones_einvoice();

                 //START: Validar y mapear los datos para revisar si existe una orden origen en una nota de crédito
                 t.mapped_refund_order()
                 //END

                 if(res){
                     swal({
                          title: "Estimado " + t.env.pos.employee.name + ', ¿Seguro que deseas continuar?',
                          text: "No podrás deshacer este paso.. ",
                          icon: "warning",
                          buttons: ["No seguiré", "Continuar!"],
                        }
                     ).then((value) => {
                         if (value) {
                             super.validateOrder(isForceValidate);
                          } else {
                            console.log("No hacer nada...");
                          }
                    });
                 }else{
                    return res;
                 }
            }


            _ChangeCurrency(type,value, paymentLine) {
                let self = this;
                let currencies = this.env.pos.currencies_ids;
                let cur = $('.drop-currency').val();
                let curr_sym;
                let order= this.env.pos.get_order();
                let pos_currency = this.env.pos.currency;
                let last_payment = order.paymentlines.length >= 0 ? order.paymentlines.models[order.paymentlines.length - 1] : false;
                if (paymentLine){
                    last_payment = paymentLine;
                }

                if(last_payment){
                    let currency_selected = this.env.pos.currency;
                    for(var i=0;i<currencies.length;i++){
                         if(cur == currencies[i].id){
                            currency_selected = currencies[i];
                            break;
                         }
                    }

                    if(currency_selected.id != pos_currency.id){
                        $('.id_convertion').show();
                        let currency_in_pos = (self.env.pos.currency.rate/currency_selected.rate).toFixed(6);
                        //$('.currency_symbol').text(currency_selected.symbol);
                        $('.currency_symbol').text(pos_currency.symbol);
                        $('.currency_rate').text(currency_in_pos);
                        $('.currency_name').text(currency_selected.name);
                        curr_sym = currency_selected.symbol;
                        var due = order.get_due();
                        var val = type == 'change' ? last_payment.amount : value;
                        let curr_tot = val * currency_in_pos;
                        $('.currency_cal').text(parseFloat(curr_tot.toFixed(2)));
                        last_payment.set_currency_other_id(currency_selected.id);
                        last_payment.set_is_other_currency(true);
                        //let amount_currency=0.0
                        last_payment.set_amount_currency(0.0);
                        last_payment.set_amount_currency_real(val);
                        last_payment.set_change_rate(currency_in_pos);
                        if (paymentLine==false){
                            last_payment.set_amount(curr_tot);
                        }else{
                            return curr_tot;
                        }


                    }else{
                        $('.id_convertion').hide();
                        $('.currency_symbol').text("");
                        $('.currency_rate').text("");
                        $('.currency_name').text("");
                        last_payment.set_currency_other_id(false);
                        last_payment.set_is_other_currency(false);
                        last_payment.set_amount(last_payment.amount_currency_real);
                        last_payment.set_amount_currency(0.0);
                        last_payment.set_amount_currency_real(0.0);
                        last_payment.set_change_rate(0.0);

                        return -1;

                    }

                }else{
                    $('.id_convertion').hide();
                    $('.currency_symbol').text("");
                    $('.currency_rate').text("");
                    $('.currency_name').text("");
                    let pos_currency = this.env.pos.currency;
                    $('.drop-currency').val(pos_currency.id);
                    swal("Ups !", "Seleccione primero un método de pago", "warning")
                    return false;
                }

            }


             _updateSelectedPaymentline() {
                if (this.paymentLines.every((line) => line.paid)) {
                    this.currentOrder.add_paymentline(this.payment_methods_from_config[0]);
                }
                if (!this.selectedPaymentLine) return; // do nothing if no selected payment line
                // disable changing amount on paymentlines with running or done payments on a payment terminal
                const payment_terminal = this.selectedPaymentLine.payment_method.payment_terminal;
                if (
                    payment_terminal &&
                    !['pending', 'retry'].includes(this.selectedPaymentLine.get_payment_status())
                ) {
                    return;
                }
                if (NumberBuffer.get() === null) {
                    this.deletePaymentLine({ detail: { cid: this.selectedPaymentLine.cid } });
                } else {
                    var value = NumberBuffer.getFloat();
                    var new_value = this._ChangeCurrency('new',value,this.selectedPaymentLine);
                    if(new_value==-1){
                        new_value = value;
                    }else{
                        if(new_value==false){
                            return 0;
                        }else{
                            new_value = new_value
                        }
                    }

                    this.selectedPaymentLine.set_amount(new_value);
                    //this.selectedPaymentLine.set_amount(NumberBuffer.getFloat());
                }
            }



        };

    Registries.Component.extend(PaymentScreen, PaymentScreenCR);

    return PaymentScreen;

});
