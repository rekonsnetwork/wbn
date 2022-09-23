from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sales_order_validation_cr = fields.Selection([
        ('none', 'None'),
        ('block', 'Block'),
        ('warning', 'Warning')
    ], 'Sales Order Validation', default='block',)

    delivery_order_validation_cr = fields.Selection([
        ('none', 'None'),
        ('block', 'Block'),
        ('warning', 'Warning')
    ], 'Delivery Order Validation', default='block',)

    sales_order_validation_ow = fields.Selection([
        ('none', 'None'),
        ('block', 'Block'),
        ('warning', 'Warning')
    ], 'Sales Order Validation', default='block',)

    maximum_allowed_ap_so = fields.Integer('Maximum Allowed AP Age', default=30)

    delivery_order_validation_ow = fields.Selection([
        ('none', 'None'),
        ('block', 'Block'),
        ('warning', 'Warning')
    ], 'Delivery Order Validation', default='block',)

    maximum_allowed_ap_do = fields.Integer('Maximum Allowed AP Age', default=60)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            sales_order_validation_cr=str(self.env['ir.config_parameter'].sudo().get_param('rnet_credit_limit.sales_order_validation_cr')),
            delivery_order_validation_cr=str(self.env['ir.config_parameter'].sudo().get_param('rnet_credit_limit.delivery_order_validation_cr')),
            sales_order_validation_ow=str(self.env['ir.config_parameter'].sudo().get_param('rnet_credit_limit.sales_order_validation_ow')),
            delivery_order_validation_ow=str(self.env['ir.config_parameter'].sudo().get_param('rnet_credit_limit.delivery_order_validation_ow')),
            maximum_allowed_ap_so=int(self.env['ir.config_parameter'].sudo().get_param('rnet_credit_limit.maximum_allowed_ap_so')),
            maximum_allowed_ap_do=int(self.env['ir.config_parameter'].sudo().get_param('rnet_credit_limit.maximum_allowed_ap_do')),
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        sales_order_validation_cr = self.sales_order_validation_cr or 'block'
        delivery_order_validation_cr = self.delivery_order_validation_cr or 'block'
        sales_order_validation_ow = self.sales_order_validation_ow or 'block'
        delivery_order_validation_ow = self.delivery_order_validation_ow or 'block'
        maximum_allowed_ap_so = self.maximum_allowed_ap_so or 30
        maximum_allowed_ap_do = self.maximum_allowed_ap_do or 60

        param = self.env['ir.config_parameter'].sudo()
        param.set_param('rnet_credit_limit.sales_order_validation_cr', sales_order_validation_cr)
        param.set_param('rnet_credit_limit.delivery_order_validation_cr', delivery_order_validation_cr)
        param.set_param('rnet_credit_limit.sales_order_validation_ow', sales_order_validation_ow)
        param.set_param('rnet_credit_limit.delivery_order_validation_ow', delivery_order_validation_ow)
        param.set_param('rnet_credit_limit.maximum_allowed_ap_so', maximum_allowed_ap_so)
        param.set_param('rnet_credit_limit.maximum_allowed_ap_do', maximum_allowed_ap_do)
