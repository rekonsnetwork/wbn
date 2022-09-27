from odoo import _, api, fields, models


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    @api.multi
    def action_move_create(self):
        move_sheet = super(HrExpense, self).action_move_create()
        for move in move_sheet.values():
            if move:
                for rec in self:
                    move.write({
                        'ref': rec.sheet_id.seq,
                    })
        return move_sheet
