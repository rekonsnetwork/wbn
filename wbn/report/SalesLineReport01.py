from odoo import models, fields, api


class SalesLineReport01(models.Model):
    _name = "vw_so_line_rpt_01"
    _description = "Sales Line Report"
    _auto = False

    order_no = fields.Char('Order No')
    order_date = fields.Datetime('Order Date')
    customer_ref = fields.Char('Customer Ref')
    customer = fields.Char('Customer')
    sales_person = fields.Char('Sales Person')
    line_description = fields.Char('Line Description')
    product_default_code = fields.Char('Product Default Code')
    product_name = fields.Char('Product Name')
    qty_order = fields.Integer('Qty Order')
    qty_delivered = fields.Integer('Qty Delivered')
    qty_outstanding = fields.Integer('Qty Outstanding', compute='_compute_qty_outstanding')
    delivery_status = fields.Char('Delivery Status')
    qty_invoiced = fields.Integer('Qty Invoiced')
    qty_return_refund = fields.Integer('Qty Return Refund')
    qty_return_no_refund = fields.Integer('Qty Return No Refund')
    qty_delivery_manual = fields.Char('Qty Delivery Manual')
    qty_scrapt = fields.Char('Qty Scrapt')
    stock_move_row = fields.Integer('Stock Move Row')
    unit_price = fields.Integer('Unit Price')
    sub_total = fields.Integer('Sub Total')
    tax = fields.Float('Tax')
    discount = fields.Integer('Discount')
    total = fields.Integer('Total')
    line_status = fields.Char('Line Status')
    line_invoice_status = fields.Char('Line Invoice Status')
    order_status = fields.Char('Order Status')
    order_invoice_status = fields.Char('Order Invoice Status')

    @api.model_cr
    def init(self):
        self._cr.execute(""" select * from vw_so_line_rpt_01 """)

    @api.depends('qty_order', 'qty_delivered')
    @api.one
    def _compute_qty_outstanding(self):
        self.qty_outstanding = self.qty_order - self.qty_delivered
