# -*- coding: utf-8 -*-


def patch_web7():
    import babel
    import os.path
    import sys

    import openerp.addons.web
    try:
        from openerp.addons.web import http as openerpweb
    except ImportError:
        # OpenERP Web 6.1
        return

    # Self-reference for 6.1 modules which import 'web.common.http'
    openerp.addons.web.common = openerp.addons.web
    sys.modules['openerp.addons.web.common'] = openerp.addons.web

    # Adapt the OpenERP Web 7.0 method for OpenERP 6.1 server
    @openerpweb.jsonrequest
    def translations(self, req, mods, lang):
        res_lang = req.session.model('res.lang')
        ids = res_lang.search([("code", "=", lang)])
        lang_params = None
        if ids:
            lang_params = res_lang.read(ids[0], ["direction", "date_format", "time_format",
                                                 "grouping", "decimal_point", "thousands_sep"])

        separator = '_' if '_' in lang else '@'
        langs = lang.split(separator)
        langs = [separator.join(langs[:x]) for x in range(1, len(langs) + 1)]

        translations_per_module = {}
        for addon_name in mods:
            translations_per_module[addon_name] = transl = {"messages": []}
            addons_path = openerpweb.addons_manifest[addon_name]['addons_path']
            for l in langs:
                f_name = os.path.join(addons_path, addon_name, "i18n", l + ".po")
                try:
                    with open(f_name) as t_file:
                        po = babel.messages.pofile.read_po(t_file)
                except Exception:
                    continue
                for x in po:
                    if x.id and x.string and "openerp-web" in x.auto_comments:
                        transl["messages"].append({'id': x.id, 'string': x.string})
        return {"modules": translations_per_module,
                "lang_parameters": lang_params}
    openerp.addons.web.controllers.main.WebClient.translations = translations

    # For Python loading, the order is --load web_seven,web
    # For the js stuff, the order should be ['web', 'web_seven']
    def module_boot(req, db=None):
        server_wide_modules = openerp.conf.server_wide_modules
        try:
            openerp.conf.server_wide_modules = server_wide_modules[::-1]
            return main_module_boot(req, db=db)
        finally:
            openerp.conf.server_wide_modules = server_wide_modules
    main_module_boot = openerp.addons.web.controllers.main.module_boot
    openerp.addons.web.controllers.main.module_boot = module_boot
