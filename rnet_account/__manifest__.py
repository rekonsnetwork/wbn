{
    'name': 'RNET Account',
    'version': '1.0',
    'depends': ['account'],
    'author': 'RNET',
    'summary': 'Modifikasi modul accounting',
    'description': """
        Modifikasi modul accounting:
        - Tambah field Ref 2 & 3 di jurnal entries.
    """,
    'data': [
        'views/account_view.xml',
    ],
    'demo': [],
    'category': 'Invoicing Management',
    "installable": True,
    "auto_install": False,
    "application": True,
}
