from odoo import models, fields, api


class PurchaseLineReport01(models.Model):
    _name = "vw_po_line_rpt_01"
    _description = "Purchase Line Report"
    _auto = False

    po_no = fields.Char('PO No')
    order_date = fields.Char('Order Date')
    partner_ref = fields.Char('Partner Ref')
    vendor = fields.Char('Vendor')
    po_representative = fields.Char('Purchase Representative')
    line_description = fields.Char('Line Description')
    product_default_code = fields.Char('Product Default Code')
    product_name = fields.Char('Product Name')
    qty_order = fields.Integer('Qty Order')
    qty_received = fields.Integer('Qty Received')
    receipt_status = fields.Char('Receipt Status')
    qty_invoiced = fields.Integer('Qty Invoiced')
    qty_return_refund = fields.Integer('Qty Return Refund')
    qty_return_no_refund = fields.Integer('Qty Return No Refund')
    qty_delivery_manual = fields.Integer('Qty Delivery Manual')
    qty_scrap = fields.Integer('Qty Scrap')
    stock_move_row = fields.Integer('Stock Move Row')
    unit_price = fields.Float('Unit Price')
    sub_total = fields.Float('Subtotal')
    tax = fields.Float('Tax')
    discount = fields.Float('Discount')
    total = fields.Float('Total')
    line_status = fields.Char('Line Status')
    order_status = fields.Char('Order Status')
    order_invoice_status = fields.Char('Order Invoice Status')

    @api.model_cr
    def init(self):
        self._cr.execute(""" select * from vw_po_line_rpt_01 """)
