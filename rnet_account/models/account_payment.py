from odoo import _, api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_validate_invoice_payment(self):
        res = super(AccountPayment, self).action_validate_invoice_payment()

        for inv in self.invoice_ids:
            move = self.env['account.move'].search([('name', '=', inv.number)])
            if move:
                move.write({
                    'ref': None,
                    # TODO: Konfirmasi apa yang dimaksud dengan No. Reg Payment pada task 17.
                    'ref2': inv.number,
                })
        return res
