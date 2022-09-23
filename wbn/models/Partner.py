from odoo import models, api

import logging
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'
    _order = 'name'

    @api.multi
    def name_get(self):
        res = super(Partner, self).name_get()
        if(res):
            t = res[0]
            if not "\n" in t[1]:
                data = []
                for partner in self:
                    display_name = '['
                    display_name += partner.ref or ""
                    display_name += '] '
                    display_name += partner.name or ""
                    data.append((partner.id, display_name))
                return data
        return res

    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name', 'ref')
    def _compute_display_name(self):
        super(Partner, self)._compute_display_name()

    @api.model
    def create(self, vals):
        obj = super(Partner, self).create(vals)
        if not obj.ref:
            number = self.env['ir.sequence'].next_by_code('internal.ref') or ''
            obj.write({'ref': number})
        return obj
