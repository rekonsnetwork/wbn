from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from .bankbook_excel import BankbookExcel

import logging


_logger = logging.getLogger(__name__)


class BankbookWizard(models.TransientModel):
    _name = 'bankbook.wizard'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    bank_account_id = fields.Many2one('account.journal', string='Bank Account', required=True,
            domain="[('type', '=', 'bank')]")
    target_moves = fields.Selection([('posted', 'All Posted Entries'), ('all', 'All Entries'),],
            string='Target Moves', required=True, default='posted')

    def print(self):
        if self._context.get('report_type') == 'excel':
            excel = BankbookExcel
            excel.print(self, self.get_data())
        else:
            raise ValidationError('Not implemented')

    def get_data(self):
        params = []
        query = "select * from account_move am where am.journal_id in (%s)"
        params.append(self.bank_account_id.id)

        if(self.start_date):
            query = query + " and am.\"date\" >= %s"
            params.append(self.start_date)

        if(self.end_date):
            query = query + " and am.\"date\" <= %s"
            params.append(self.end_date)

        if(self.target_moves == 'posted'):
            query = query + " and am.state = %s"
            params.append('posted')

        _logger.info("=====")
        _logger.info(query)
        _logger.info(params)
        _logger.info("=====")

        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()
