from odoo import models, api, fields, _

import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class Production(models.Model):
    _inherit = 'mrp.production'

    order_id = fields.Many2one('sale.order', string='Sale Order')
    customer_ref = fields.Char('Customer Ref', compute='_get_customer_ref')
    customer_id = fields.Many2one('res.partner', string='Customer')
    qty_done = fields.Integer('Qty Done', compute='_get_qty_done')
    qty_wip = fields.Integer('Qty WIP', compute='_get_qty_wip')
    qty_posted = fields.Integer('Quantity Posted', compute='_get_posted_quantity')
    qty_unposted = fields.Integer('Quantity Unposted', store=False)

    @api.onchange('order_id')
    def onchange_order_id(self):
        self.customer_id = self.order_id.partner_id

    @api.one
    def _get_qty_done(self):
        for line in self.finished_move_line_ids:
            self.qty_done += line.qty_done

    @api.one
    @api.depends('product_qty', 'qty_done')
    def _get_qty_wip(self):
        self.qty_wip = self.product_qty - self.qty_done

    @api.one
    @api.depends('order_id')
    def _get_customer_ref(self):
        self.customer_ref = self.order_id.client_order_ref

    @api.one
    def _get_posted_quantity(self):
        self.qty_posted = 0
        self.qty_unposted = 0
        for line in self.move_raw_ids:
            if line.state == 'done':
                self.qty_posted = self.qty_posted + line.quantity_done
            else:
                self.qty_unposted = self.qty_unposted + line.quantity_done


class Productivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    shift = fields.Integer('Shift')
    qty_done = fields.Integer('Qty Done')


class Workorder(models.Model):
    _inherit = 'mrp.workorder'

    shift = fields.Selection([(0, 0), (1, 1), (2, 2), (3, 3)], 'Shift', default=1, required=True)
    qty_producing_tmp = fields.Integer('qty_producing_tmp')

    @api.multi
    def record_production(self):
        if self.update_timeline():
            self.create_new_timeline()
        return super(Workorder, self).record_production()

    def create_new_timeline(self):
        timeline_obj = self.env['mrp.workcenter.productivity']
        loss_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'productive')], limit=1)
        timeline = timeline_obj.create({
            'workorder_id': self.id,
            'workcenter_id': self.workcenter_id.id,
            'description': _('Time Tracking: ') + self.env.user.name,
            'loss_id': loss_id.id,
            'date_start': datetime.now(),
            'user_id': self.env.user.id,
            'shift': 0,
            'qty_done': 0
        })
        self.write({'time_ids': timeline})
        return True

    def update_timeline(self):
        continue_work = True

        timeline_obj = self.env['mrp.workcenter.productivity']
        domain = [('workorder_id', 'in', self.ids), ('date_end', '=', False)]
        timeline = timeline_obj.search(domain, limit=1)
        qty_done = self.qty_producing_tmp

        # end of manufacturing
        if qty_done == 0:
            qty_done = self.qty_producing
            continue_work = False
        #

        timeline.write({
            'date_end': datetime.now(),
            'shift': self.shift,
            'qty_done': qty_done
        })
        # hack
        self.qty_producing_tmp = 0
        return continue_work

    @api.onchange('qty_producing')
    def _onchange_qty_producing(self):
        res = super(Workorder, self)._onchange_qty_producing()
        self.qty_producing_tmp = self.qty_producing
        return res
