from odoo import _, api, fields, models
import datetime
import xlsxwriter
import base64
import io


class CashbookExcel(models.TransientModel):
    _name = 'cashbook.excel'

    def print(self, report_data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        header_format = workbook.add_format({'bold': True,})
        short_date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy',})
        long_date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy HH:mm:ss',})
        float_format = workbook.add_format({'num_format': '#,##0.00',})
        int_format = workbook.add_format({'num_format': '#,##0',})
        general_format = workbook.add_format({})

        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        row_num = 0
        col_num = 0
        column_names = list(report_data[0].keys())
        column_names.sort()
        for col_name in column_names:
            worksheet.write(row_num, col_num, col_name, header_format)
            col_num += 1

        row_num = 1
        for dict in report_data:
            col_num = 0
            for col_name in column_names:
                cell_value = dict[col_name]
                cell_format = general_format
                if isinstance(cell_value, (datetime.datetime)):
                    cell_format = long_date_format
                elif isinstance(cell_value, (datetime.date)):
                    cell_format = short_date_format
                elif isinstance(cell_value, (int)):
                    cell_format = int_format
                elif isinstance(cell_value, (float)):
                    cell_format = float_format

                worksheet.write(row_num, col_num, cell_value, cell_format)
                worksheet.set_column(col_num, col_num, self._estimate_col_length(cell_value))
                col_num += 1
            row_num += 1

        workbook.close()

        export_id = self.env['excel.wizard'].create({
            'excel_file': base64.encodestring(output.getvalue()),
            'file_name': 'Cashbook Report.xls'
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

    def _estimate_col_length(self, value):
        col_length = 20
        is_bool = isinstance(value, (bool))
        if not is_bool and (value is not None):
            if len(str(value)) < 15:
                return col_length
            col_length = len(str(value))
        return col_length
