odoo.define('l10n_cr_epos.ClientDetailsEdit', function(require) {

    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const Registries = require('point_of_sale.Registries');
    const session = require('web.session');

    const ClientDetailsEditCR = ClientDetailsEdit => class extends ClientDetailsEdit {
        constructor() {
            super(...arguments);
            this.intFields = ['identification_id', 'country_id', 'state_id','county_id','district_id','neighborhood_id','property_product_pricelist'];
            this.changes = {};
         }
        captureChange(event) {
            this.changes[event.target.name] = event.target.value;

            if(event.target.name=='vat'){
                var vat = $('input[name="vat"]').val();
                $.ajax({
                    url: 'https://api.hacienda.go.cr/fe/ae?identificacion='+vat,
                    success: function(respuesta) {
                        console.log(respuesta);
                        alert("Búsqueda exitosa!");
                        $('input[name="name"]').val(respuesta.nombre);
                        //this.changes["name"] = respuesta.nombre;
                    },
                    error: function() {
                        $('input[name="name"]').val("")
                        alert("No se ha podido obtener la información");
                        console.log("No se ha podido obtener la información");
                    }
                });
            }

            if(event.target.name=='country_id'){
                 var states = this.env.pos.states;
                 var states_html = ""
                 for(var i=0; i < states.length; i++){
                    if(states[i].country_id[0] == parseInt(event.target.value)){
                        states_html+= "<option value="+states[i].id +" >"+ states[i].name +"</option>";
                    }
                 }
                 $('select[name="state_id"]').empty();
                 $('select[name="state_id"]').html(states_html);
            }

            if(event.target.name=='state_id'){
                 var counties = this.env.pos.list_county;
                 var counties_html = ""
                 for(var i=0; i < counties.length; i++){
                    if(counties[i].state_id[0] == parseInt(event.target.value)){
                        counties_html+= "<option value="+counties[i].id +" >"+ counties[i].name +"</option>";
                    }
                 }
                 $('select[name="county_id"]').empty();
                 $('select[name="county_id"]').html(counties_html);
            }

            if(event.target.name=='county_id'){
                 var districts = this.env.pos.list_district;
                 var districts_html = ""
                 for(var i=0; i < districts.length; i++){
                    if(districts[i].county_id[0] == parseInt(event.target.value)){
                        districts_html+= "<option value="+districts[i].id +" >"+ districts[i].name +"</option>";
                    }
                 }
                 $('select[name="district_id"]').empty();
                 $('select[name="district_id"]').html(districts_html);
            }

             if(event.target.name=='district_id'){
                 var neighborhoods = this.env.pos.list_neighborhood;
                 var neighborhoods_html = ""
                 for(var i=0; i < neighborhoods.length; i++){
                    if(neighborhoods[i].district_id[0] == parseInt(event.target.value)){
                        neighborhoods_html+= "<option value="+neighborhoods[i].id +" >"+ neighborhoods[i].name +"</option>";
                    }
                 }
                 $('select[name="neighborhood_id"]').empty();
                 $('select[name="neighborhood_id"]').html(neighborhoods_html);
             }



        }
         saveChanges() {
            //El campo "NAME" al ser automático, necesita que se asigne nuevamente para ser guardado
            this.changes['name'] = $('input[name="name"]').val();

            let processedChanges = {};
            for (let [key, value] of Object.entries(this.changes)) {
                if (this.intFields.includes(key)) {
                    processedChanges[key] = parseInt(value) || false;
                } else {
                    processedChanges[key] = value;
                }
            }
             if ((!this.props.partner.name && !processedChanges.name) || processedChanges.name === '' ){
                return this.showPopup('ErrorPopup', {
                  title: _('El nombre del cliente es requerido!.'),
                });
            }
            processedChanges.id = this.props.partner.id || false;
            this.trigger('save-changes', { processedChanges });
        }

    };

    Registries.Component.extend(ClientDetailsEdit, ClientDetailsEditCR);

    return ClientDetailsEdit;
});
