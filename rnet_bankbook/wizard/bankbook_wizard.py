from odoo import _, api, fields, models


class BankbookWizard(models.TransientModel):
    _name = 'bankbook.wizard'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    bank_account_id = fields.Many2one('account.journal', string='Bank Account', domain="[('type', '=', 'bank')]")
    target_moves = fields.Selection([('posted', 'All Posted Entries'), ('all', 'All Entries'),],
            string='Target Moves', required=True, default='posted')
