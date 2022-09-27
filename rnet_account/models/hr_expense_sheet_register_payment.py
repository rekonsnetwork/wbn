from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from werkzeug import url_encode


class HrExpenseSheetRegisterPaymentWizard (models.TransientModel):
    _inherit = 'hr.expense.sheet.register.payment.wizard'

    # Override semua method karena perlu akses ke local variable.
    # https://github.com/odoo/odoo/blob/12.0/addons/hr_expense/wizard/hr_expense_sheet_register_payment.py#L93
    @api.multi
    def expense_post_payment(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        expense_sheet = self.env['hr.expense.sheet'].browse(active_ids)

        # Create payment and post it
        payment = self.env['account.payment'].create(self._get_payment_vals())
        payment.post()

        # Log the payment in the chatter
        body = (_("A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense %s has been made.") %
                (payment.amount, payment.currency_id.symbol, url_encode({'model': 'account.payment', 'res_id': payment.id}), payment.name, expense_sheet.name))
        expense_sheet.message_post(body=body)

        # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
        account_move_lines_to_reconcile = self.env['account.move.line']
        for line in payment.move_line_ids + expense_sheet.account_move_id.line_ids:
            if line.account_id.internal_type == 'payable' and not line.reconciled:
                account_move_lines_to_reconcile |= line
        account_move_lines_to_reconcile.reconcile()

        # Mulai edit
        self._update_account_move_refs(payment, expense_sheet)
        # Selesai edit

        return {'type': 'ir.actions.act_window_close'}

    def _update_account_move_refs(self, payment, expense_sheet):
        move = expense_sheet.account_move_id
        move.write({
            'ref': payment.name,
            'ref2': expense_sheet.seq,
        })

        payment_move = self.env['account.move'].search(
            [('name', '=', payment.move_name)])
        if payment_move:
            payment_move.write({
                'ref': payment.name,
                'ref2': expense_sheet.seq,
            })
