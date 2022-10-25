import imp


from odoo import _, api, fields, models


class AccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    filter_refund = fields.Selection([('refund', 'Create a draft credit note'),
                                      ('cancel', 'Cancel: create credit note and reconcile'),
                                      ('modify', 'Modify: create credit note, reconcile and create a new draft invoice')],
                                     default='modify', string='Credit Method', required=True,
                                     help='Choose how you want to credit this invoice. You cannot Modify and Cancel if the invoice is already reconciled')
