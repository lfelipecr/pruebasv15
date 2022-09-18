# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import hashlib
import json

import odoo
from odoo import api, http, models
from odoo.http import request
from odoo.tools import file_open, image_process, ustr
from odoo.addons.web.controllers.main import HomeStaticTemplateHelpers


class Http(models.AbstractModel):
    _inherit = 'ir.http'


    def session_info(self):
        user = request.env.user
        version_info = odoo.service.common.exp_version()

        session_uid = request.session.uid
        user_context = request.session.get_context() if session_uid else {}
        IrConfigSudo = self.env['ir.config_parameter'].sudo()
        max_file_upload_size = int(IrConfigSudo.get_param(
            'web.max_file_upload_size',
            default=128 * 1024 * 1024,  # 128MiB
        ))
        mods = odoo.conf.server_wide_modules or []
        lang = user_context.get("lang")
        translation_hash = request.env['ir.translation'].sudo().get_web_translations_hash(mods, lang)
        session_info = {
            "uid": session_uid,
            "is_system": user._is_system() if session_uid else False,
            "is_admin": user._is_admin() if session_uid else False,
            "user_context": user_context,
            "db": request.session.db,
            "server_version": version_info.get('server_version'),
            "server_version_info": version_info.get('server_version_info'),
            "support_url": "https://www.odoo.com/buy",
            "name": user.name,
            "username": user.login,
            "partner_display_name": user.partner_id.display_name,
            "company_id": user.company_id.id if session_uid else None,  # YTI TODO: Remove this from the user context
            "partner_id": user.partner_id.id if session_uid and user.partner_id else None,
            "web.base.url": IrConfigSudo.get_param('web.base.url', default=''),
            "active_ids_limit": int(IrConfigSudo.get_param('web.active_ids_limit', default='20000')),
            'profile_session': request.session.profile_session,
            'profile_collectors': request.session.profile_collectors,
            'profile_params': request.session.profile_params,
            "max_file_upload_size": max_file_upload_size,
            "home_action_id": user.action_id.id,
            "cache_hashes": {
                "translations": translation_hash,
            },
            "currencies": self.sudo().get_currencies(),
        }
        if self.env.user.has_group('base.group_user'):
            # the following is only useful in the context of a webclient bootstrapping
            # but is still included in some other calls (e.g. '/web/session/authenticate')
            # to avoid access errors and unnecessary information, it is only included for users
            # with access to the backend ('internal'-type users)
            if request.db:
                mods = list(request.registry._init_modules) + mods
            qweb_checksum = HomeStaticTemplateHelpers.get_qweb_templates_checksum(debug=request.session.debug, bundle="web.assets_qweb")

            a = request
            if 'cids' in a.httprequest.cookies:
                cids = a.httprequest.cookies['cids']
                ids = False
                if cids.find(',') > 0:
                    new_ids = cids.split(',')
                    if type(new_ids) == list:
                        array_ids = []
                        for i in new_ids:
                            array_ids.append(int(i))
                        ids = array_ids
                elif cids.find(',') == -1:
                    ids = int(cids)
                if ids:
                    cr_id = request.env.ref('l10n_cr_places.module_einvoice_costa_rica').id
                    company = request.env['res.company'].sudo().browse(ids)
                    if company:
                        for co in company:
                            if user.groups_id:
                                if co.country_code == 'CR':
                                    user.write({'groups_id': [(4, cr_id)]})
                                else:
                                    user.write({'groups_id': [(3, cr_id)]})
                # company = request.env['res.company'].sudo().browse(int(a.httprequest.cookies['cids']))
                #
                # # company = request.env.company
                # #
                # cr_id = request.env.ref('l10n_cr_places.module_einvoice_costa_rica').id
                # if user.groups_id:
                #     if company.country_code == 'CR':
                #         user.write({'groups_id': [(4, cr_id)]})
                #     else:
                #         user.write({'groups_id': [(3, cr_id)]})

            menus = request.env['ir.ui.menu'].load_menus(request.session.debug)
            ordered_menus = {str(k): v for k, v in menus.items()}
            menu_json_utf8 = json.dumps(ordered_menus, default=ustr, sort_keys=True).encode()
            session_info['cache_hashes'].update({
                "load_menus": hashlib.sha512(menu_json_utf8).hexdigest()[:64], # sha512/256
                "qweb": qweb_checksum,
            })
            session_info.update({
                # current_company should be default_company
                "user_companies": {
                    'current_company': user.company_id.id,
                    'allowed_companies': {
                        comp.id: {
                            'id': comp.id,
                            'name': comp.name,
                        } for comp in user.company_ids
                    },
                },
                "show_effect": True,
                "display_switch_company_menu": user.has_group('base.group_multi_company') and len(user.company_ids) > 1,
            })
            company_id = session_info['company_id']
            session_info['company_currency_id'] = request.env['res.company'].browse(company_id).currency_id.id if company_id else None
            session_info['companies_currency_id'] = {comp.id: comp.currency_id.id for comp in request.env.user.company_ids}
        return session_info
