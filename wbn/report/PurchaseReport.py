from odoo import models, api, fields

import logging
_logger = logging.getLogger(__name__)


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    name = fields.Char('PO#')
    unit_quantity = fields.Float('Qty Ordered', readonly=True, oldname='quantity')
    po_total_record = fields.Float('PO Count')
    qty_received = fields.Float('Qty Received')
    qty_invoiced = fields.Float('Qty Billed')
    price_subtotal = fields.Float('Amount Untaxed')
    price_tax = fields.Float('Amount Taxed')
    price_total = fields.Float('Amount Total', readonly=True)

    @api.model_cr
    def init(self):
        return
