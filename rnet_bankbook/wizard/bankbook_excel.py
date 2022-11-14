from odoo import _, api, fields, models
import datetime
import xlsxwriter
import base64
import io
import logging

_logger = logging.getLogger(__name__)

class BankbookExcel(models.TransientModel):
    _name = 'bankbook.excel'

    def print(self, report_data, data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        title_format = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True, 'font_size': 16})

        parameter_format = workbook.add_format({'bold': True,  'align': 'left'})
        parameter_format_value = workbook.add_format({'align': 'left'})
        parameter_format_date = workbook.add_format({'num_format': 'dd-mmm-yyyy', 'align': 'left'})          

        summary_format = workbook.add_format({'bold': True,})
        header_format = workbook.add_format({'bold': True,  'align': 'center','bg_color':'#D9D9D9','border': 1})
        

        detail_short_date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy', 'align': 'center','border': 1})  
        detail_long_date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy HH:mm:ss', 'align': 'center','border': 1})
        detail_float_format = workbook.add_format({'num_format': '#,##0.00','border': 1})     
        detail_int_format = workbook.add_format({'num_format': '#,##0','border': 1})  
        detail_general_format = workbook.add_format({'border': 1})    

        summary_float_format = workbook.add_format({'num_format': '#,##0.00','border': 1})     

        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        report_title='Bank Book'
        worksheet.merge_range('A1:C1', report_title, title_format)   

        worksheet.write(1, 0, 'Bank Account', parameter_format)
        worksheet.write(1, 1,  data['form']['bank_account_desc'], parameter_format_value)       
        worksheet.write(2, 0, 'Start Date', parameter_format)
        worksheet.write(2, 1,  data['form']['start_date'], parameter_format_date)
        worksheet.write(3, 0, 'End Date', parameter_format)
        worksheet.write(3, 1,  data['form']['end_date'], parameter_format_date)  
        worksheet.write(4, 0, 'Target Moves', parameter_format)
        worksheet.write(4, 1, data['form']['target_move_text'],parameter_format_value)


        row_num = 6
        col_num = 0
        column_names = list(report_data[0].keys())

        # for col_name in column_names:
        #    _logger.info(col_name)  

        worksheet.write(row_num, 0, "Journal Date", header_format)
        worksheet.write(row_num, 1, "Partner", header_format)
        worksheet.write(row_num, 2, "Label", header_format)
        worksheet.write(row_num, 3, "Debit", header_format)
        worksheet.write(row_num, 4, "Credit", header_format)
        worksheet.write(row_num, 5, "Balance", header_format)
        worksheet.write(row_num, 6, "State", header_format)
        
        row_num += 1

        for dict in report_data:
            
            for col_name in column_names:
                col_num = -1
                if (col_name=="Journal Date"):
                    col_num=0
                if (col_name=="Partner"):
                    col_num=1
                if (col_name=="Label"):
                    col_num=2
                if (col_name=="Debit"):
                    col_num=3
                if (col_name=="Credit"):
                    col_num=4
                if (col_name=="Balance"):
                    col_num=5
                if (col_name=="State"):
                    col_num=6

                if (col_num>=0) & (dict["State"]!='SYS_SUMMARY'):
                    cell_value = dict[col_name]

                    cell_format = detail_general_format
                    if isinstance(cell_value, (datetime.datetime)):
                        cell_format = detail_long_date_format
                    elif isinstance(cell_value, (datetime.date)):
                        cell_format = detail_short_date_format
                    elif isinstance(cell_value, (int)):
                        cell_format = detail_int_format
                    elif isinstance(cell_value, (float)):
                        cell_format = detail_float_format

                    worksheet.write(row_num, col_num, cell_value, cell_format)
                    worksheet.set_column(col_num, col_num, self._estimate_col_length(cell_value))

            if (dict["State"]=='SYS_SUMMARY'):
                row_num += 1
                worksheet.write(row_num, 4, "BEGINING BALANCE", summary_format)    
                worksheet.write(row_num, 5, dict["Begining Balance"], summary_float_format) 

                row_num += 1
                worksheet.write(row_num, 4, "TOTAL DEBIT", summary_format)   
                worksheet.write(row_num, 5, dict["Debit"], summary_float_format) 

                row_num += 1
                worksheet.write(row_num, 4, "TOTAL CREDIT", summary_format)   
                worksheet.write(row_num, 5, dict["Credit"], summary_float_format) 

                row_num += 1
                worksheet.write(row_num, 4, "ENDING BALANCE", summary_format) 
                worksheet.write(row_num, 5, dict["Balance"], summary_float_format) 

            row_num += 1

        workbook.close()

        export_id = self.env['excel.wizard'].create({
            'excel_file': base64.encodestring(output.getvalue()),
            'file_name': 'Bankbook Report '+data['form']['bank_account_text']+'.xls'
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
