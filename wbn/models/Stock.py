from odoo import models, _, fields, api
from odoo.exceptions import UserError
from werkzeug import urls
from odoo.addons.http_routing.models.ir_http import slug

import logging

_logger = logging.getLogger(__name__)


class Transfer(models.Model):
    _inherit = ['stock.picking']
    gut_initial_demand = fields.Integer('Initial Demand', compute='_get_initial_demand')
    gut_qty_done = fields.Integer('Qty Done', compute='_get_qty_done')
    gut_transfer_status = fields.Char('Transfer Status', compute='_get_transfer_status')

    @api.one
    def _get_initial_demand(self):
        total = 0
        for line in self.move_ids_without_package:
            total = total + line.product_uom_qty
        self.gut_initial_demand = total

    @api.one
    def _get_qty_done(self):
        total = 0
        for line in self.move_ids_without_package:
            total = total + line.quantity_done
        self.gut_qty_done = total

    @api.one
    @api.depends('gut_initial_demand', 'gut_qty_done')
    def _get_transfer_status(self):
        self.gut_transfer_status = 'Open'
        if self.gut_initial_demand == self.gut_qty_done:
            self.gut_transfer_status = 'Closed'

    @api.one
    @api.depends('move_lines.date_expected')
    def _compute_scheduled_date(self):
        super(Transfer, self)._compute_scheduled_date()
        # Kalau statusnya "Waiting" (seperti backorder) maka scheduled date-nya di-set sekarang:
        if self.state == 'confirmed':
            self.scheduled_date = fields.Datetime.now()

    @api.multi
    def preview_picking(self):
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    @api.multi
    def get_portal_url(self, report_type=None, download=None):
        self.ensure_one()
        base_url = '/' if self.env.context.get('relative_url') else \
            self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url = urls.url_join(base_url, "picking/preview/" + str(self.id))

        url = base_url + '?access_token=12345678-1234-1234-1234-12345678%s%s' % (
            '&report_type=%s' % report_type if report_type else '',
            '&download=true' if download else '',
        )
        return url
