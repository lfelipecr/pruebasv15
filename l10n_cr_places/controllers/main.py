from odoo import http
from odoo.http import request
from odoo.addons.account.controllers.onboarding import OnboardingController  # Import the class
from odoo.addons.account.controllers.ir_http import Http  # Import the class


class CustomOnboardingController(Http):

    @http.route('/account/account_invoice_onboarding', auth='user', type='json')
    def account_invoice_onboarding(self):
        """ Returns the `banner` for the account invoice onboarding panel.
            It can be empty if the user has closed it or if he doesn't have
            the permission to see it. """

        company = request.env.company

        cr_id = request.env.ref('module_einvoice_costa_rica').id
        if request.env.user.group_ids:
            cr_id_g = request.env.user.group_ids.filtered(lambda g: g.id == cr_id)
            if cr_id_g:
                request.env.user.write({'groups_ids'})
        if not request.env.is_admin() or \
                company.account_invoice_onboarding_state == 'closed':
            return {}

        return {
            'html': request.env.ref('account.account_invoice_onboarding_panel')._render({
                'company': company,
                'state': company.get_and_update_account_invoice_onboarding_state()
            })
        }