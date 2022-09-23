from odoo import models, _, fields, api
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from .credit_limit import CreditLimit

import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('account_review', 'Approve For Delivery'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore.")

    def show_warning_message(self):
        message_id = self.env['delivery.credit.limit.warning'].create({
            'message': "This customer has reached his credit limit, do you want to continue?"
        })

        return {
            'name': 'Warning',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'delivery.credit.limit.warning',
            'res_id': message_id.id,
            'target': 'new',
            'context': {'current_id': self.id}
        }

    def show_block_window(self):
        view_id = self.env.ref('rnet_credit_limit.delivery_credit_limit_block_wizard').id
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery.credit.limit.block',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'name': 'Customer Credit Limit',
            'views': [[view_id, 'form']],
            'context': {'current_id': self.id}
        }

    def get_credit_do_warning_type(self):
        return str(
            self.env['ir.config_parameter'].sudo().get_param(
                'rnet_credit_limit.delivery_order_validation_cr') or 'block'
        )

    def get_overdue_do_warning_type(self):
        return str(
            self.env['ir.config_parameter'].sudo().get_param(
                'rnet_credit_limit.delivery_order_validation_ow') or 'block'
        )

    @api.multi
    def validate(self):
        return super(StockPicking, self).button_validate()

    @api.multi
    def button_validate(self):
        partner = self.partner_id
        credit_do_warning_type = self.get_credit_do_warning_type()
        overdue_do_warning_type = self.get_overdue_do_warning_type()

        if credit_do_warning_type == 'none' and overdue_do_warning_type == 'none':
            return super(StockPicking, self).button_validate()

        inv_rec = self.env['account.invoice'].search([
            ('partner_id', '=', partner.id),
            ('state', 'not in', ['draft', 'cancel'])
        ])

        s = self.env['sale.order'].search([
            ('origin', '=', self.origin),
        ])

        sale_amount = s.search([
            ('partner_id', '=', partner.id),
        ]).mapped('amount_total')

        cr = CreditLimit()
        is_credit_so_reached = cr.is_credit_so_reached(partner, inv_rec, sale_amount)
        if is_credit_so_reached and (credit_do_warning_type == 'warning'):
            # return self.show_warning_message()
            return super(StockPicking, self).button_validate()

        if is_credit_so_reached and (credit_do_warning_type == 'block'):
            return self.show_block_window()

        overdue_days = int(self.env['ir.config_parameter'].sudo().get_param('rnet_credit_limit.maximum_allowed_ap_do'))
        is_so_overdue = cr.is_so_overdue(partner.id, self.env, overdue_days)

        if is_so_overdue and (overdue_do_warning_type == 'warning'):
            # return self.show_warning_message()
            return super(StockPicking, self).button_validate()

        if is_so_overdue and (overdue_do_warning_type == 'block'):
            return self.show_block_window()

        return super(StockPicking, self).button_validate()

    def action_account_approve(self):
        if self.env.user.has_group('stock.group_stock_manager'):
            return super(StockPicking, self).button_validate()
        else:
            raise UserError("Please contact your Administrator for delivery approval")
