from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class DeliveryCreditLimitWarning(models.TransientModel):
    _name = "delivery.credit.limit.warning"

    message = fields.Text('Message', required=True)

    @api.one
    def confirm(self):
        current_id = int(self.env.context.get('current_id'))
        rec = self.env['stock.picking'].browse([current_id])
        rec.validate()
