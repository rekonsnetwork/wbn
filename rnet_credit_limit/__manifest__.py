{
    'name': "RNET - Credit Limit",
    'author': "RNET",
    'version': '0.1',

    'depends': ['customer_credit_management'],

    'data': [
        'views/res_config_settings_view.xml',
        'views/stock_picking_view.xml',
        'wizard/sale_credit_limit_warning_view.xml',
        'wizard/delivery_credit_limit_warning_view.xml',
        'wizard/delivery_credit_limit_block_view.xml'
    ],

    "installable": True,
    "auto_install": False,
    "application": True,
}