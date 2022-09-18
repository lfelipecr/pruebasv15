{
    "name": "l10n_cr_places",  # TODO
    'summary': """
       Costa Rica - Territorio""",
    'description': """
       Lista de:
       1. Distritos.
       2. Provincias.
       3. Cantones.
       4. Barrios.

   """,
    'author': "Ruben Madrid",
    'company': '',
    'website': "",
    'category': 'Accounting/Accounting',
    'version': '15.0.1.0',
    "depends": ['account','l10n_cr','base'],  # TODO Check
    "data": [  # TODO Check
        # security
        "security/e_billing_security.xml",
        "security/ir.model.access.csv",
        # data
        "data/res.country.county.csv",
        "data/res.country.district.csv",
        "data/res.country.neighborhood.csv",
        "data/res.country.state.csv",
        # reports
        # views
        "views/menu_views.xml",
        "views/res_company.xml",
        "views/res_country_county.xml",
        "views/res_country_district.xml",
        "views/res_country_neighborhood.xml",
        "views/res_partner.xml",
    ],
}
