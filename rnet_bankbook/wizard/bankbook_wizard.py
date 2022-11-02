from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BankbookWizard(models.TransientModel):
    _name = 'bankbook.wizard'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    bank_account_id = fields.Many2one('account.journal', string='Bank Account', domain="[('type', '=', 'bank')]")
    target_moves = fields.Selection([('posted', 'All Posted Entries'), ('all', 'All Entries'),],
                                    string='Target Moves', required=True, default='posted')

    def print(self):
        report_data = self._get_report_data()
        if not report_data:
            raise ValidationError('Bankbook is empty')

        if self._context.get('report_type') == 'excel':
            return self.env['bankbook.excel'].print(report_data)
        else:
            raise ValidationError('Not implemented')

    def _get_report_data(self):
        params = []
        query = "select * from account_move am"

        if(self.bank_account_id.id):
            query = query + "  where am.journal_id in (%s)"
            params.append(self.bank_account_id.id)
        else:
            query = query + "  where am.journal_id in (select aj.id from account_journal aj where \"type\" = 'bank')"

        if (self.start_date):
            query = query + " and am.\"date\" >= %s"
            params.append(self.start_date)

        if (self.end_date):
            query = query + " and am.\"date\" <= %s"
            params.append(self.end_date)

        if (self.target_moves == 'posted'):
            query = query + " and am.state = %s"
            params.append('posted')

        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()
