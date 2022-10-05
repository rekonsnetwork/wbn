from odoo import _, api, fields, models
import xlwt
import base64
import io


class AccountingReportBi(models.TransientModel):
    _inherit = "accounting.report.bi"

    # Terpaksa harus override semua method karena perlu update query,
    # dimana dalam addon bi_financial_pdf_reports antara query/data dan logic jadi satu fungsi.
    # Bad practice.

    def _get_account_move_entry(self, accounts, init_balance, sortby, display_account):
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(
                date_from=self.env.context.get('date_from'), date_to=False, initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace(
                'account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, 0.0 AS amount_currency, '' AS lref, '' AS lref2, '' AS lref3, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                WHERE l.account_id IN %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace(
            'account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, m.ref2 AS mref2, m.ref3 AS mref3, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE l.account_id IN %s ''' + filters + ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, m.ref2, m.ref3, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)

        return account_res

    # Terpaksa harus override semua method karena perlu nambah kolom Excel.
    @api.multi
    def _print_general_ledger_excel_report(self, report_lines):
        filename = 'General Ledger.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'
        style_header = xlwt.easyxf(
            "font:height 300; font: name Liberation Sans, bold on,color black; align: horiz center")
        style_line = xlwt.easyxf(
            "font:bold on,color black;")
        worksheet.row(0).height_mismatch = True
        worksheet.row(0).height = 500
        worksheet.write_merge(0, 0, 0, 5, self.env['res.users'].browse(
            self.env.uid).company_id.name + " : General Ledger Report", style=style_header)
        worksheet.write(2, 0, 'Journals')
        worksheet.write(2, 1, 'Display Account')
        worksheet.write(2, 2, 'Target Moves')
        worksheet.write(2, 3, 'Sorted By')
        if self.date_from:
            worksheet.write(2, 4, 'Date From')
        if self.date_to:
            worksheet.write(2, 5, 'Date To')
        journals = ', '.join([lt.code or '' for lt in self.journal_ids])
        if self.display_account == 'all':
            display_account = 'All accounts'
        elif self.display_account == 'movement':
            display_account = 'With movements'
        else:
            display_account = 'With balance not equal to zero'
        worksheet.write(3, 0, journals)
        worksheet.write(3, 1, display_account)
        worksheet.write(
            3, 2, 'All Posted Entries' if self.target_move == 'posted' else 'All Entries')
        worksheet.write(3, 3, 'Date' if self.sortby ==
                        'sort_date' else 'Journal and Partner')
        if self.date_from:
            worksheet.write(3, 4, self.date_from, date_format)
        if self.date_to:
            worksheet.write(3, 5, self.date_to, date_format)

        worksheet.write(5, 0, 'Date')
        worksheet.write(5, 1, 'JRNL')
        worksheet.write(5, 2, 'Partner')
        worksheet.write(5, 3, 'Ref')
        worksheet.write(5, 4, 'Ref 2')
        worksheet.write(5, 5, 'Ref 3')
        worksheet.write(5, 6, 'Move')
        worksheet.write(5, 7, 'Entry Label')
        worksheet.write(5, 8, 'Debit')
        worksheet.write(5, 9, 'Credit')
        worksheet.write(5, 10, 'Balance')
        row = 6
        col = 0

        for line in report_lines:
            flag = False
            worksheet.write_merge(row, row, 0, 5, line.get(
                'code') + line.get('name'), style=style_line)
            worksheet.write(row, col+6, line.get('debit'), style=style_line)
            worksheet.write(row, col+7, line.get('credit'), style=style_line)
            worksheet.write(row, col+8, line.get('balance'), style=style_line)
            for move_line in line.get('move_lines'):
                row += 1
                worksheet.write(row, col, move_line.get('ldate'), date_format)
                worksheet.write(row, col + 1, move_line.get('lcode'))
                worksheet.write(row, col + 2, move_line.get('partner_name'))
                worksheet.write(row, col + 3, move_line.get('lref'))
                worksheet.write(row, col + 4, move_line.get('mref2'))
                worksheet.write(row, col + 5, move_line.get('mref3'))
                worksheet.write(row, col + 6, move_line.get('move_name'))
                worksheet.write(row, col + 7, move_line.get('lname'))
                worksheet.write(row, col + 8, move_line.get('debit'))
                worksheet.write(row, col + 9, move_line.get('credit'))
                worksheet.write(row, col + 10, move_line.get('balance'))
                row += 1
                flag = True
            if not flag:
                row += 1
        fp = io.BytesIO()
        workbook.save(fp)

        export_id = self.env['excel.report'].create(
            {'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
        res = {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'excel.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res
