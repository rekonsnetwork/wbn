from odoo import models, fields, api


class Invoice(models.Model):
    _inherit = 'account.invoice'
    delivery_number = fields.Char('Delivery Slip No.', compute='_get_delivery_number')
    manual_delivery_no =  fields.Char('Delivery No.')
    no_faktur = fields.Char('No Faktur Pajak')

    @api.one
    def _get_delivery_number(self):
        model_name = 'sale.order'
        if self.type == 'in_invoice':
            model_name = 'purchase.order'

        order = self.env[model_name].search([('name', '=', self.origin)])
        picking_list = []
        for picking in order.picking_ids:
            picking_list.append(picking.name)
        self.delivery_number = ", ".join(picking_list)