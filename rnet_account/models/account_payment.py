from odoo import _, api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_validate_invoice_payment(self):
        res = super(AccountPayment, self).action_validate_invoice_payment()

        for inv in self.invoice_ids:
            move = self.env['account.move'].search([('name', '=', inv.number)])
            if move:
                move.write({
                    'ref': self.name,
                    'ref2': inv.number,
                })
        return res

    # Tiap create payment entry, ref-nya diisi payment name
    # dan ref2-nya diisi invoice / bill number. Jika invoicenya
    # lebih dari satu, dipisahkan oleh koma.
    def _create_payment_entry(self, amount):
        move = super(AccountPayment, self)._create_payment_entry(amount)
        move.ref = self.name

        if self.invoice_ids:
            invoices = ', '.join([inv.number for inv in self.invoice_ids])
            move.ref2 = invoices
        return move
