{
    'name': 'RNET Journal Reference Modification',
    'version': '1.0',
    'depends': ['account', 'hr_expense'],
    'author': 'RNET',
    'summary': 'Modifikasi pembentukan jurnal',
    'description': """
        Modifikasi pembentukan jurnal:
        - Tambah field Ref 2 & 3 di jurnal entries.
        - Modifikasi pembentukan jurnal Invoice dan Bill.
        - Modifikasi pembentukan jurnal Expense.
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
