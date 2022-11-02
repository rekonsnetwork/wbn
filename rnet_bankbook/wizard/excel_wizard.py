from odoo import _, api, fields, models


class ExcelWizard(models.TransientModel):
    _name = 'excel.wizard'

    excel_file = fields.Binary('Excel Report')
    file_name = fields.Char('Excel File', size=64)
