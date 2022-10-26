from odoo import models, fields, api


class SalesReport(models.Model):
    _inherit = 'sale.report'

    deliver_price_subtotal = fields.Float('Delivered Amount')
    deliver_price_tax = fields.Float('Delivered Amount Tax')
    deliver_price_total = fields.Float('Delivered Amount Total')
    sp_scheduled_date = fields.Date('Delivery Schedule Date')
    delivery_status = fields.Char('Delivery Status')
    sp_date_done = fields.Date('Delivery Effective Date')
    order_line_total_record = fields.Integer('# of Lines')
    qty_outstanding = fields.Integer('Qty Outstanding')
    sales_order_total_record = fields.Float('SO Count')
    sp_name = fields.Char('Delivery #')
    weight_delivered = fields.Integer('Gross Weight Delivered')

    nbr = fields.Integer('Done Deliveries', readonly=True)
    name = fields.Char('Customer Reference', readonly=True)

    price_unit = fields.Float('Unit Price Avg.', group_operator='avg')

    invoice_no=fields.Char('Invoice #')

    @api.model_cr
    def init(self):
        return
