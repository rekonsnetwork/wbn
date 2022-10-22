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
    _name = 'rnet.aged_partner_report_byarap'
    _description = 'Report Aged Partner Balance By AR/AP'
    _logger.info(_description)

    columns = OrderedDict([('company', 'Company'),
                            ('partner_code', 'Partner Code'),
                            ('partner', 'Partner Name'),
                            ('internal_type', 'Internal Type'),
                            ('journal_name', 'Journal'),
                            ('journal_no', 'Journal No'),
                            ('journal_state', 'Jourbal State'),
                            ('invoice_no', 'Invoice No'),
                            ('date', 'Date'),
                            ('date_maturity', 'Due Date'),
                            ('age', 'Age (days)'),
                            ('age_category', 'Age Category'),
                            ('currency', 'Currency'),
                            ('amount', 'Amount'),
                            ('amount_paid', 'Amount Paid'),
                            ('over_due', 'Over Due'),
                            ('age_1', 'age1-age2'),
                            ('age_2', 'age2-age3'),
                            ('age_3', 'age3-age4'),
                            ('age_4', 'age4-age5'),
                            ('age_5', '+age'),
                            ('balance', 'Total'),
                            ('invoice_origin', 'Invoice Origin'),
                            ('invoice_manual_delivery_no', 'DO'),
                           ])

    def to_excel(self, data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        # cell formatters
        short_date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy', 'align': 'center'})
        short_date_format_L = workbook.add_format({'num_format': 'dd-mmm-yyyy', 'align': 'left'})    
        long_date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy HH:mm:ss', 'align': 'center'})
        float_format = workbook.add_format({'num_format': '#,##0.00'})
        title_format = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True, 'font_size': 16})
        parameter_format = workbook.add_format({'bold': True,  'align': 'left'})
        parameter_format_value = workbook.add_format({'align': 'left'})
        header_format = workbook.add_format({'bold': True,  'align': 'center','bg_color':'#D9D9D9'})

        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        internal_types = self._get_internal_types(data)
        target_move = self._get_target_move_types(data)

        # print title
        worksheet.merge_range(
            'A1:C1', 'Aged Partner Report By AR/AP', title_format)
        worksheet.set_row(0, 30)
        worksheet.write(1, 0, 'Position Date', parameter_format)
        worksheet.write(1, 1,  data['form']['date_from'], short_date_format_L)
        worksheet.write(2, 0, 'Type', parameter_format)
        worksheet.write(2, 1, ", ".join(internal_types))
        worksheet.write(3, 0, 'Period Length (days)', parameter_format)
        worksheet.write(3, 1, data['form']['period_length'],parameter_format_value)
        worksheet.write(4, 0, 'Target Moves', parameter_format)
        worksheet.write(4, 1, data['form']['target_move_text'])
      #  worksheet.write(4, 1, ", ".join(target_move))
        

        # print header
        period_length = data['form']['period_length']

        row = 6
        col = 0
        for key in self.columns:
            sheader=self.columns[key]
            sheader=sheader.replace("age1","0" )
            sheader=sheader.replace("age2", str(period_length) )
            sheader=sheader.replace("age3", str(period_length*2) )
            sheader=sheader.replace("age4", str(period_length*3) )
            sheader=sheader.replace("age5", str(period_length*4) )
            sheader=sheader.replace("+age", "+"+str(period_length*4) )
            
          #  worksheet.write(row, col, self.columns[key], header_format)
            worksheet.write(row, col, sheader, header_format)
            col += 1

        report_data = self._get_report_data(data)

        # print report
        row = 7
        
    
        for dict in report_data:
            col = 0
            for key in self.columns:
                value = dict[key]
                if isinstance(value, (datetime.datetime)):
                    worksheet.write(row, col, value, long_date_format)
                elif isinstance(value, (datetime.date)):
                    worksheet.write(row, col, value, short_date_format)
                elif isinstance(value, (float)):
                    worksheet.write(row, col, value, float_format)
                else:
                    worksheet.write(row, col, value)
                worksheet.set_column(
                    col, col, self._estimate_col_length(value))
                col += 1
            row += 1
    
        workbook.close()

        export_id = self.env['excel.report'].create({'excel_file': base64.encodestring(
            output.getvalue()), 'file_name': 'Aged Partner Balance By AR AP.xls'})
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

    def _get_target_move_types(self, data):
        res = data['form']['target_move']
        return [res]
        # if res == 'posted':
        #     return ['All Posted Entries']
        # else:
        #     return ['All Entries']

    def _get_report_data(self, data):
        position_date = data['form']['date_from']
        period_length = data['form']['period_length']
        selected_partner_ids = data['form']['selected_partner_ids']
        internal_types = self._get_internal_types(data)
        data_level = data['form']['data_level']
        _logger.info("_get_report_data")
        query = """
            Select
            --    a.company_id,
                a.company,	
                a.partner_code,
                a.partner,
                a.internal_type,               
            --   a.journal_id,
                a.journal_name,	
                a.journal_no,
                a.journal_state,
            --    a.journal_item_id,
                a.invoice_no,
                a.date,
                a.date_maturity, 
                a.age,
                a.age_category,
                a.currency,
                a.amount,
                a.amount_paid,
                case when a.age_category<0 then a.balance else 0 end as over_due,
                case when a.age_category=%s*1 then a.balance else 0 end as age_1,
                case when a.age_category=%s*2 then a.balance else 0 end as age_2,
                case when a.age_category=%s*3 then a.balance else 0 end as age_3,
                case when a.age_category=%s*4 then a.balance else 0 end as age_4,
                case when a.age_category>%s*4 then a.balance else 0 end as age_5,	
                a.balance,		
                a.invoice_origin,
                a.invoice_manual_delivery_no	
            from
            (
            Select 
                a.company_id,
                a.company,	
                a.partner_id,
                a.partner_code,
                a.partner,
                a.journal_id,
                a.journal_name,
                a.internal_type,	
                a.journal_no,
                a.journal_state,
                a.journal_item_id,
                a.invoice_no,
                a.date,
                a.date_maturity,                
                (extract(day from a.date_maturity - cast(%s as TIMESTAMP) )) as age,
                case
                    when (extract(day from date_maturity - cast(%s  as TIMESTAMP) )) < 0 then
                        (floor((extract(day from date_maturity - cast(%s as TIMESTAMP) )) / %s)) * %s
                    else
                        (floor((extract(day from date_maturity - cast(%s as TIMESTAMP) )) / %s) + 1) * %s
                end as age_category,                                            
                a.currency,
                a.balance as amount,
                coalesce(coalesce(pyr.payment_amount,pyp.payment_amount),0)  as amount_paid,
                a.balance+coalesce((coalesce(pyr.payment_amount,pyp.payment_amount)),0) as balance,
                a.invoice_origin,
                a.invoice_manual_delivery_no	
            from 
                vw_account_move_line a 
                left join 
                    (
                    Select a.debit_move_id, sum(b.balance) as payment_amount
                    from
                        account_partial_reconcile a
                        left join vw_account_move_line b on b.journal_item_id=a.credit_move_id
                        where b.journal_state='posted' and b.date<=cast(%s as TIMESTAMP)
                    group by a.debit_move_id	
                    ) pyr on pyr.debit_move_id=a.journal_item_id	and a.internal_type='receivable'
                left join 
                    (
                    Select a.credit_move_id, sum(b.balance) as payment_amount
                    from
                        account_partial_reconcile a
                        left join vw_account_move_line b on b.journal_item_id=a.debit_move_id
                        where b.journal_state='posted' and b.date<=cast(%s as TIMESTAMP)
                    group by a.credit_move_id	
                    ) pyp on pyp.credit_move_id=a.journal_item_id	and a.internal_type='payable'
            where 
                ((a.internal_type='receivable' and a.debit>0) or (a.internal_type='payable' and a.credit>0))
            """      

        if internal_types:
            types = ','.join("'{0}'".format(t) for t in internal_types)
            query = query + \
                " and a.internal_type in (" + types + ")"


        if selected_partner_ids:
            ids = [str(int) for int in selected_partner_ids]
            ids = ", ". join(ids)
            query = query + \
                " and a.partner_id in (" + ids + ")"                

#               a.internal_type in ('receivable','payable') 
#               and a.journal_state='posted' 	
#               -- and a.date<=cast('2022-10-20' as TIMESTAMP)
#                        and a.partner_code  in ('C0018','S0048') 
#               -- and a.partner_code  in ('C0051') 
#
        params = (period_length, period_length, period_length, period_length, period_length, 
                    position_date, position_date, position_date, 
                    period_length,period_length,
                    position_date,
                    period_length,period_length,
                    position_date,position_date)

        query = query + """
                ) a
            where coalesce(a.balance,0)<>0
            order by
                a.company,
                a.internal_type,
                a.partner,
                a.date
        """
        # _logger.info("==================")
        # _logger.info(query)
        # _logger.info(params)
        # _logger.info(query,params)
        # _logger.info("==================")


        self.env.cr.execute(query, params)
#        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
