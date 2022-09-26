from odoo import _, api, fields, models


class HrExpenseSheetRegisterPaymentWizard (models.TransientModel):
    _inherit = 'hr.expense.sheet.register.payment.wizard'

    @api.multi
    def expense_post_payment(self):
        res = super(HrExpenseSheetRegisterPaymentWizard,
                    self).expense_post_payment()

        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        expense_sheet = self.env['hr.expense.sheet'].browse(active_ids)
        move = expense_sheet.account_move_id

        move.write({
            'ref': None,
            'ref2': expense_sheet.seq,
        })
        return res
