from odoo import _, api, fields, models
import datetime
# Sejak v13 Odoo telah beralih ke xlsxwriter dan tidak lagi menggunakan xlwt
import xlsxwriter
import base64
import io
import logging
from collections import OrderedDict

_logger = logging.getLogger(__name__)


class AgedPartnerReportDetail(models.TransientModel):
    _name = 'rnet.aged_partner_report_detail'
    _description = 'Report Aged Partner Balance Detail'

    columns = OrderedDict([('company', 'Company'),
                           ('internal_type', 'Internal Type'),
                           ('partner_code', 'Partner Code'),
                           ('partner', 'Partner'),
                           ('date', 'Date'),
                           ('date_maturity', 'Date Maturity'),
                           ('age', 'Age'),
                           ('age_category', 'Age Category'),
                           ('journal_name', 'Journal Name'),
                           ('debit', 'Debit'),
                           ('credit', 'Credit'),
                           ('balance', 'Balance'),
                           ('full_reconcile_id', 'Full Reconcile Id'),
                           ('full_reconcile', 'Full Reconcile'),
                           ('reconciled', 'Reconciled'),
                           ('account_code', 'Account Code'),
                           ('account_name', 'Account Name'),
                           ('currency', 'Currency'),
                           ('journal_no', 'Journal No.'),
                           ('journal_date', 'Journal Date'),
                           ('ref', 'Ref'),
                           ('ref2', 'Ref 2'),
                           ('ref3', 'Ref 3'),
                           ('journal_state', 'Journal State'),
                           ('reverse_date', 'Reverse Date'),
                           ('reverse_entry_id', 'Reverse Entry Id'),
                           ('invoice_no', 'Invoice No'),
                           ('invoice_type', 'Invoice Type'),
                           ('invoice_origin', 'Invoice Origin'),
                           ('invoice_reference', 'Invoice Reference'),
                           ('invoice_manual_delivery_no',
                            'Invoice Manual Delivery No'),
                           ('invoice_date', 'Invoice Date'),
                           ('invoice_date_due', 'Invoice Date Due'),
                           ('payment_no', 'Payment No'),
                           ('payment_type', 'Payment Type'),
                           ('payment_state', 'Payment State'),
                           ('journal_create_date', 'Journal Create Date'),
                           ])

    def to_excel(self, data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        # cell formatters
        title_format = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True, 'font_size': 16})

        parameter_format = workbook.add_format({'bold': True,  'align': 'left'})
        parameter_format_value = workbook.add_format({'align': 'left'})
        parameter_format_date = workbook.add_format({'num_format': 'dd-mmm-yyyy', 'align': 'left'})  

        header_format = workbook.add_format({'bold': True,  'align': 'center','bg_color':'#D9D9D9','border': 1})

        detail_short_date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy', 'align': 'center','border': 1})  
        detail_long_date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy HH:mm:ss', 'align': 'center','border': 1})
        detail_float_format = workbook.add_format({'num_format': '#,##0.00','border': 1})
        detail_general_format = workbook.add_format({'border': 1})

        total_float_format = workbook.add_format({'num_format': '#,##0.00','border': 1,'bg_color':'#D9D9D9','bold': True})   

        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        internal_types = self._get_internal_types(data)  
        target_move = data['form']['target_move']

        # print title

        report_title='Aged Partner Report Detail'
        if data['form']['data_level']=="detailhistory":
            report_title='Aged Partner Report Detail History'

        worksheet.merge_range(
            'A1:C1', report_title, title_format)
        worksheet.set_row(0, 30)
        worksheet.write(1, 0, 'Position Date', parameter_format)
        worksheet.write(1, 1,  data['form']['date_from'], parameter_format_date)
        worksheet.write(2, 0, 'Type', parameter_format)
        worksheet.write(2, 1, ", ".join(internal_types))
        worksheet.write(3, 0, 'Period Length (days)', parameter_format)
        worksheet.write(3, 1, data['form']['period_length'],parameter_format_value)
        worksheet.write(4, 0, 'Target Moves', parameter_format)
        worksheet.write(4, 1, data['form']['target_move_text'])

        # print header
        row = 6
        col = 0
        for key in self.columns:
            worksheet.write(row, col, self.columns[key], header_format)
            col += 1

        report_data = self._get_report_data(data)

        # print report
        row = 7

        total={}    
        total["debit"]=0
        total["credit"]=0
        total["balance"]=0


        for dict in report_data:
            col = 0
            for key in self.columns:
                value = dict[key]
                if isinstance(value, (datetime.datetime)):
                    worksheet.write(row, col, value, detail_long_date_format)
                elif isinstance(value, (datetime.date)):
                    worksheet.write(row, col, value, detail_short_date_format)
                elif isinstance(value, (float)):
                    worksheet.write(row, col, value, detail_float_format)
                else:
                    worksheet.write(row, col, value, detail_general_format)
                worksheet.set_column(
                    col, col, self._estimate_col_length(value))

                if key=="debit":
                    total[key]+= value    
                if key=="credit":
                    total[key]+= value                        
                if key=="balance":
                    total[key]+= value  
                   
                col += 1
            row += 1

        worksheet.write(row, 9, total["debit"], total_float_format)
        worksheet.write(row, 10, total["credit"], total_float_format)
        worksheet.write(row, 11, total["balance"], total_float_format)


        workbook.close()

        exportfilename='Aged Partner Balance Detail.xls'
        if data['form']['data_level']=="detailhistory":
           exportfilename='Aged Partner Balance Detail History.xls'         

        export_id = self.env['excel.report'].create({'excel_file': base64.encodestring(
            output.getvalue()), 'file_name': exportfilename})
        res = {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'excel.report',
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

    def _get_internal_types(self, data):
        res = data['form']['result_selection']
        if res == 'customer':
            return ['receivable']
        elif res == 'supplier':
            return ['payable']
        elif res == 'customer_supplier':
            return ['receivable', 'payable']
        else:
            return False

    def _get_report_data(self, data):
        position_date = data['form']['date_from']
        period_length = data['form']['period_length']
        selected_partner_ids = data['form']['selected_partner_ids']
        internal_types = self._get_internal_types(data)
        data_level = data['form']['data_level']
        target_move = data['form']['target_move']    

        query = """
            select
                company,
                internal_type,
                partner_code,
                partner,
                date,
                date_maturity,
                (extract(day
            from
                date_maturity - cast(%s as TIMESTAMP) )) as age,
                case
                    when (extract(day
                from
                    date_maturity - cast(%s as TIMESTAMP) )) < 0 then
                    (floor((extract(day from date_maturity - cast(%s as TIMESTAMP) )) / %s)) * %s
                    else
                    (floor((extract(day from date_maturity - cast(%s as TIMESTAMP) )) / %s) + 1) * %s
                end as age_category,
                journal_name,
                debit,
                credit,
                balance,
                full_reconcile_id,
                full_reconcile,
                --reconcile_date,
                reconciled,
                account_code,
                account_name,
                --jurnal_item_label,
                currency,
                journal_no,
                journal_date,
                "ref",
                ref2,
                ref3,
                journal_state,
                reverse_date,
                reverse_entry_id,
                invoice_no,
                invoice_type,
                invoice_origin,
                invoice_reference,
                invoice_manual_delivery_no,
                invoice_date,
                invoice_date_due,
                payment_no,
                payment_type,
                payment_state,
                journal_create_date
            from
                vw_account_move_line
            where
                date <= cast(%s as TIMESTAMP)
            """
        params = (position_date, position_date, position_date, period_length, period_length,
                  position_date, period_length, period_length, position_date)

        if target_move=="posted":
            query = query + " and journal_state='posted' "                 

        if internal_types:
            types = ','.join("'{0}'".format(t) for t in internal_types)
            query = query + \
                " and internal_type in (" + types + ")"

        if selected_partner_ids:
            ids = [str(int) for int in selected_partner_ids]
            ids = ", ". join(ids)
            query = query + \
                " and partner_id in (" + ids + ")"

        if data_level=="detail":
            query = query + \
            " and full_reconcile_id is null"        


        query = query + """
            order by
                company,
                partner,
                internal_type,              
                full_reconcile_id,
                date,
                journal_create_date
        """

        # _logger.info("==================")
        # _logger.info(query)
        # _logger.info(params)
        # _logger.info("==================")

        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()
