from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class DeliveryCreditLimitBlock(models.TransientModel):
    _name = "delivery.credit.limit.block"

    @api.one
    def action_exceed_limit(self):
        order_rec = self.env['stock.picking'].browse(self._context['current_id'])
        order_rec.write({'state': "account_review"})
