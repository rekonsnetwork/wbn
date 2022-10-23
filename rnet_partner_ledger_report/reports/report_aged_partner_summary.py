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
    _name = 'rnet.aged_partner_report_summary'
    _description = 'Report Aged Partner Balance'
    _logger.info(_description)

    columns = OrderedDict([  ('partner_code', 'Partner Code'),
                            ('partner', 'Partner Name'),
                            ('internal_type', 'Internal Type'),
                            # ('journal_name', 'Journal'),
                            # ('journal_no', 'Journal No'),
                            # ('journal_state', 'Jourbal State'),
                            # ('invoice_no', 'Invoice No'),
                            # ('date', 'Date'),
                            # ('date_maturity', 'Due Date'),
                            # ('age', 'Age (days)'),
                            # ('age_category', 'Age Category'),
                            ('currency', 'Currency'),
                            # ('amount', 'Amount'),
                            # ('amount_paid', 'Amount Paid'),
                            ('unreconsiled_payment', 'Unreconsiled Payment'),
                            ('over_due', 'Over Due'),
                            ('age_1', 'age1-age2'),
                            ('age_2', 'age2-age3'),
                            ('age_3', 'age3-age4'),
                            ('age_4', 'age4-age5'),
                            ('age_5', '+age'),
                            ('balance', 'Total'),
                            # ('invoice_origin', 'Invoice Origin'),
                            # ('invoice_manual_delivery_no', 'DO'),
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
        worksheet.merge_range(
            'A1:C1', 'Aged Partner Report', title_format)
        worksheet.set_row(0, 30)
        worksheet.write(1, 0, 'Position Date', parameter_format)
        worksheet.write(1, 1,  data['form']['date_from'], parameter_format_date)
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
        
        total={}    
        total["unreconsiled_payment"]=0
        total["over_due"]=0
        total["age_1"]=0
        total["age_2"]=0
        total["age_3"]=0
        total["age_4"]=0
        total["age_5"]=0
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

                if key=="unreconsiled_payment":
                    total[key]+= value    
                if key=="over_due":
                    total[key]+= value                        
                if key=="age_1":
                    total[key]+= value  
                if key=="age_2":
                    total[key]+= value  
                if key=="age_3":
                    total[key]+= value  
                if key=="age_4":
                    total[key]+= value  
                if key=="age_5":
                    total[key]+= value                     
                if key=="balance":
                    total[key]+= value  

                col += 1
            row += 1
        
        worksheet.write(row, 4, total["unreconsiled_payment"], total_float_format)
        worksheet.write(row, 5, total["over_due"], total_float_format)
        worksheet.write(row, 6, total["age_1"], total_float_format)
        worksheet.write(row, 7, total["age_2"], total_float_format)
        worksheet.write(row, 8, total["age_3"], total_float_format)
        worksheet.write(row, 9, total["age_4"], total_float_format)
        worksheet.write(row, 10, total["age_5"], total_float_format)
        worksheet.write(row, 11, total["balance"], total_float_format)

        workbook.close()

        export_id = self.env['excel.report'].create({'excel_file': base64.encodestring(
            output.getvalue()), 'file_name': 'Aged Partner Balance.xls'})
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

        _logger.info("_get_report_data")
        query = """
            Select
            --    a.company_id,
            --    a.company,	
                a.partner_code,
                a.partner,
                a.internal_type,               
            --   a.journal_id,
            --    a.journal_name,	
            --    a.journal_no,
            --    a.journal_state,
            --    a.journal_item_id,
            --    a.invoice_no,
            --    a.date,
            --    a.date_maturity, 
            --    a.age,
            --    a.age_category,
                 a.currency,
            --   a.amount,
            --    a.amount_paid,
                sum(case when a.age_category is null then a.balance else 0 end) as unreconsiled_payment,
                sum(case when a.age_category<0 then a.balance else 0 end) as over_due,
                sum(case when a.age_category=%s*1 then a.balance else 0 end) as age_1,
                sum(case when a.age_category=%s*2 then a.balance else 0 end) as age_2,
                sum(case when a.age_category=%s*3 then a.balance else 0 end) as age_3,
                sum(case when a.age_category=%s*4 then a.balance else 0 end) as age_4,
                sum(case when a.age_category>%s*4 then a.balance else 0 end) as age_5,	
                sum(a.balance) as balance		
            --    a.invoice_origin,
            --    a.invoice_manual_delivery_no	
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
                a.balance-coalesce((coalesce(pyr.payment_amount,pyp.payment_amount)),0) as balance,
                a.invoice_origin,
                a.invoice_manual_delivery_no	
            from 
                vw_account_move_line a 
                left join 
                    (
                    Select a.debit_move_id, 
                    		--sum(b.balance) as payment_amount
							sum(a.amount) as payment_amount
                    from
                        account_partial_reconcile a
                        left join vw_account_move_line b on b.journal_item_id=a.credit_move_id
                        where b.date<=cast(%s as TIMESTAMP) 
                """
        if target_move=="posted":                       
            query = query + " and b.journal_state='posted' "
            
        query = query + """                        
                    group by a.debit_move_id	
                    ) pyr on pyr.debit_move_id=a.journal_item_id and a.internal_type='receivable'
                left join 
                    (
                    Select a.credit_move_id, 
                            --sum(b.balance) as payment_amount
							-sum(a.amount) as payment_amount
                    from
                        account_partial_reconcile a
                        left join vw_account_move_line b on b.journal_item_id=a.debit_move_id
                        where b.date<=cast(%s as TIMESTAMP)
                """
        if target_move=="posted":                       
            query = query + " and b.journal_state='posted' "
        query = query + """                        
                    group by a.credit_move_id	
                    ) pyp on pyp.credit_move_id=a.journal_item_id	and a.internal_type='payable'
            where 
                ((a.internal_type='receivable' and a.debit>0) or (a.internal_type='payable' and a.credit>0))
                and a.date<=cast(%s as TIMESTAMP)
            """      
        if target_move=="posted":
            query = query + " and a.journal_state='posted' "

        query = query + " and a.balance-coalesce((coalesce(pyr.payment_amount,pyp.payment_amount)),0)<>0 " 

        if internal_types:
            types = ','.join("'{0}'".format(t) for t in internal_types)
            query = query + \
                " and a.internal_type in (" + types + ")"


        if selected_partner_ids:
            ids = [str(int) for int in selected_partner_ids]
            ids = ", ". join(ids)
            query = query + \
                " and a.partner_id in (" + ids + ")"                
     
        query = query + """

                UNION ALL

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
                NULL as age_category,                                            
                a.currency,
                a.balance as amount,
                a.balance as amount_paid,
                a.balance as balance,
                a.invoice_origin,
                a.invoice_manual_delivery_no	
            from 
                vw_account_move_line a 
                left join account_partial_reconcile b on (a.internal_type='receivable' and a.journal_item_id=b.credit_move_id) or 
														(a.internal_type='payable' and a.journal_item_id=b.debit_move_id) 
            where 
                ((a.internal_type='receivable' and a.credit>0) or (a.internal_type='payable' and a.debit>0))
                and a.date<=cast(%s as TIMESTAMP)
                and b.id is null
            """  

        if target_move=="posted":
            query = query + " and a.journal_state='posted' "    

        query = query + " and coalesce(a.balance,0)<>0 "                 

        if internal_types:
            types = ','.join("'{0}'".format(t) for t in internal_types)
            query = query + \
                " and a.internal_type in (" + types + ")"


        if selected_partner_ids:
            ids = [str(int) for int in selected_partner_ids]
            ids = ", ". join(ids)
            query = query + \
                " and a.partner_id in (" + ids + ")"  
 

        query = query + """
                ) a   
            group by 
                a.company_id,
                a.company,
                a.partner_id,
                a.partner_code,
                a.partner,
                a.internal_type,  
                a.currency         
            order by
                a.company,
                a.partner,
                a.internal_type,
                a.currency              
             
        """

        params = (period_length, period_length, period_length, period_length, period_length, 
                    position_date, position_date, position_date, 
                    period_length,period_length,
                    position_date,
                    period_length,period_length,
                    position_date,position_date,position_date,position_date,position_date)

        _logger.info("==================")
        _logger.info(query)
        _logger.info(params)
        _logger.info(query % params)
        _logger.info("==================")


        self.env.cr.execute(query, params)
#        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
