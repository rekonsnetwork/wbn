from odoo import _, api, fields, models
import datetime
import xlsxwriter
import base64
import io


class BankbookExcel(models.TransientModel):
    _name = 'bankbook.excel'

    def print(self, report_data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        headerFormat = workbook.add_format({'bold': True,})
        shortDateFormat = workbook.add_format({'num_format': 'dd-mmm-yyyy',})
        longDateFormat = workbook.add_format({'num_format': 'dd-mmm-yyyy HH:mm:ss',})
        floatFormat = workbook.add_format({'num_format': '#,##0.00',})
        intFormat = workbook.add_format({'num_format': '#,##0',})
        generalFormat = workbook.add_format({})

        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        rowNum = 0
        colNum = 0
        columnNames = list(report_data[0].keys())
        columnNames.sort()
        for colName in columnNames:
            worksheet.write(rowNum, colNum, colName, headerFormat)
            colNum += 1

        rowNum = 1
        for dict in report_data:
            colNum = 0
            for colName in columnNames:
                cellValue = dict[colName]
                cellFormat = generalFormat
                if isinstance(cellValue, (datetime.datetime)):
                    cellFormat = longDateFormat
                elif isinstance(cellValue, (datetime.date)):
                    cellFormat = shortDateFormat
                elif isinstance(cellValue, (int)):
                    cellFormat = intFormat
                elif isinstance(cellValue, (float)):
                    cellFormat = floatFormat

                worksheet.write(rowNum, colNum, cellValue, cellFormat)
                worksheet.set_column(colNum, colNum, self._estimate_col_length(cellValue))
                colNum += 1
            rowNum += 1

        workbook.close()

        exportId = self.env['excel.wizard'].create({
            'excel_file': base64.encodestring(output.getvalue()),
            'file_name': 'Bankbook Report.xls'
        })
        output.close()

        res = {
            'view_mode': 'form',
            'res_id': exportId.id,
            'res_model': 'excel.wizard',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res

    def _estimate_col_length(self, value):
        colLength = 20
        isBool = isinstance(value, (bool))
        if not isBool and (value is not None):
            if len(str(value)) < 15:
                return colLength
            colLength = len(str(value))
        return colLength
