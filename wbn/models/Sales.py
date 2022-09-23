from odoo import models, fields, api, exceptions,_

import logging
_logger = logging.getLogger(__name__)


class Sales(models.Model):
    _inherit = 'sale.order'
    gut_qty_total = fields.Integer('Quantity Ordered', compute='_get_qty_total')
    gut_qty_delivered = fields.Integer('Quantity Delivered', compute='_get_qty_delivered')
    gut_qty_outstanding = fields.Integer('Quantity O/S', compute='_get_qty_outstanding')
    gut_qty_invoiced = fields.Integer('Quantity Invoiced', compute='_get_qty_invoiced')
    gut_total_discount = fields.Float('Discount', compute='_get_total_discount')
    gut_delivery_status = fields.Char('Delivery Status', compute='_get_delivery_status')
    gut_remark = fields.Char('Remark')
    gut_note = fields.Text('Note')

    @api.one
    def _get_qty_total(self):
        total = 0
        for line in self.order_line:
            total = total + line.product_uom_qty
        self.gut_qty_total = total

    @api.one
    def _get_qty_delivered(self):
        total = 0
        for line in self.order_line:
            total = total + line.qty_delivered
        self.gut_qty_delivered = total

    @api.one
    def _get_qty_invoiced(self):
        total = 0
        for line in self.order_line:
            total = total + line.qty_invoiced
        self.gut_qty_invoiced = total

    @api.one
    def _get_total_discount(self):
        self.gut_total_discount = self.amount_undiscounted - self.amount_untaxed

    @api.one
    @api.depends('gut_qty_total', 'gut_qty_delivered')
    def _get_delivery_status(self):
        self.gut_delivery_status = 'Open'
        if self.gut_qty_total == self.gut_qty_delivered:
            self.gut_delivery_status = 'Closed'

    @api.one
    @api.depends('gut_qty_total', 'gut_qty_delivered')
    def _get_qty_outstanding(self):
        self.gut_qty_outstanding = self.gut_qty_total - self.gut_qty_delivered

    @api.multi
    def _prepare_invoice(self):
        existing_picking_numbers = set()
        for invoice in self.invoice_ids:
            manual_delivery_numbers = invoice.manual_delivery_no
            if manual_delivery_numbers:
                numbers = manual_delivery_numbers.split(",")
                for n in numbers:
                    existing_picking_numbers.add(n)

        pickings = []
        for picking in self.picking_ids:
            if picking.state == 'done' and (picking.name not in existing_picking_numbers):
                pickings.append(picking.name)

        invoice_vals = super(Sales, self)._prepare_invoice()
        invoice_vals['manual_delivery_no'] = ", ".join(pickings) or None
        return invoice_vals

    @api.onchange('partner_shipping_id')
    def onchange_partner_id_carrier_id(self):
        return
