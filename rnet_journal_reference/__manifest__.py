{
    'name': 'RNET Journal Reference',
    'version': '1.0',
    'depends': ['hr_expense', 'bi_financial_excel_reports'],
    'author': 'Rekons Network',
    'website': 'http://www.rekons.net/',
    'summary': 'Modifikasi pembentukan jurnal dan report',
    'description': """
        Modifikasi pembentukan jurnal dan GL:
        - Tambah field Ref 2 & 3 di jurnal entries.
        - Modifikasi pembentukan jurnal Invoice dan Bill.
        - Modifikasi pembentukan jurnal Expense.
        - Tampilkan field Ref 2 & 3 di GL.
    """,
    'data': [
        'views/account_view.xml',
        'reports/report_generalledger.xml'
    ],
    'demo': [],
    'category': 'Accounting',
    "installable": True,
    "auto_install": False,
    "application": True,
}
