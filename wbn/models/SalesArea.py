from odoo import models, fields, api


class SalesArea(models.Model):
    _name = 'sales.area'
    parent = fields.Many2one('sales.area', string='Parent Sales Area')
    code = fields.Char('Sales Area Code', required=True)
    name = fields.Char('Sales Area Name', required=True)
    longitude = fields.Float('Longitude')
    latitude = fields.Float('Latitude')
    map_location_code = fields.Text('Map Location Code')
    note = fields.Text('Note')
