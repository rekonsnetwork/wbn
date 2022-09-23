from odoo import models, fields, api


class BusinessUnit(models.Model):
    _name = 'business.unit'
    code = fields.Char('Business Unit Code', required=True)
    name = fields.Char('Business Unit Name', required=True)
    note = fields.Text('Note')
