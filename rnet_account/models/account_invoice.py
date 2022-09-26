from odoo import _, api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        move = self.env['account.move'].search([('name', '=', self.number)])

        if move:
            move.write({
                'ref': self.number
            })
        return res
