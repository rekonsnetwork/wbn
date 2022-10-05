from odoo import _, api, fields, models


class AccountAgedPartnerBalance(models.TransientModel):
    _inherit = 'bi.account.aged.partner.balance'

    balance_value = fields.Selection([
        ('latest_balance', 'Latest Balance'),
        ('per_position_date', 'As Per Position Date')
    ], required=True, default='latest_balance')

    data_level = fields.Selection([
        ('by_partner', 'By Partner'),
        ('by_transaction', 'By Transaction')
    ], required=True, default='by_partner')
