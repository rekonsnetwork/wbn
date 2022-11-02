from odoo import _, api, fields, models
import xlsxwriter
import base64
import io


class BankbookExcel(models.TransientModel):
    _name = 'bankbook.excel'

    def print(self, report_data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        rownum = 0
        colnum = 0
        columnNames = list(report_data[0].keys())
        columnNames.sort()
        for colName in columnNames:
            worksheet.write(rownum, colnum, colName)
            colnum += 1

        rownum = 1
        for dict in report_data:
            colnum = 0
            for colName in columnNames:
                worksheet.write(rownum, colnum, dict[colName])
                colnum += 1
            rownum += 1

        workbook.close()

        export_id = self.env['excel.wizard'].create({
            'excel_file': base64.encodestring(output.getvalue()),
            'file_name': 'Bankbook Report.xls'
        })
        output.close()

        res = {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'excel.wizard',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res
