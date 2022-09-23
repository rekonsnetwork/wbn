from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    ref2 = fields.Char(String='Reference 2')
    ref3 = fields.Char(String='Reference 3')
