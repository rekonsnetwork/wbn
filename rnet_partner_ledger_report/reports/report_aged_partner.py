import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, models, _
from odoo.tools import float_is_zero
import logging


_logger = logging.getLogger(__name__)


class BiReportAgedPartnerBalance(models.AbstractModel):
    _inherit = 'report.bi_partner_ledger_report.bi_report_agedpartnerbalance'

    # Terpaksa harus override semua fungsi
    @api.model
    def _get_report_values(self, docids, data=None):
        total = []
        model = self.env.context.get('active_model')
        docs = self.env['bi.account.aged.partner.balance'].browse(
            self.env.context.get('active_id'))

        target_move = data['form'].get('target_move', 'all')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))

        if data['form']['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']
        movelines, total, lines = self._get_partner_move_lines(account_type, date_from, target_move,
                                                               data['form']['period_length'], data['form']['selected_partner_ids'])

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_partner_lines': movelines,
            'get_direction': total,
            'lines': lines,
        }

    # Pisahkan fungsi query partners
    def _get_partners(self, reconciliation_clause, arg_list, selected_partner_ids):
        partner_ids = [p for p in selected_partner_ids]

        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND ''' + reconciliation_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
        '''

        if partner_ids:
            query = query + '''
                AND l.partner_id IN (''' + ",".join([str(id) for id in partner_ids]) + ''')
            '''

        query = query + '''
            ORDER BY UPPER(res_partner.name)
        '''

        # _logger.info("=== get partners ===")
        # _logger.info(query)
        # _logger.info(arg_list)
        # _logger.info("======")

        self.env.cr.execute(query, arg_list)
        return self.env.cr.dictfetchall()

    # Pisahkan fungsi undue amount
    def _get_undue_amount(self, move_state, account_type, date_from, partner_ids, company_ids):
        query = '''SELECT l.id
            FROM account_move_line AS l, account_account, account_move am
            WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND (COALESCE(l.date_maturity,l.date) >= %s)\
                AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
            AND (l.date <= %s)
            AND l.company_id IN %s'''
        self.env.cr.execute(query, (tuple(move_state), tuple(
            account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))

        # _logger.info("=== get undue amount ===")
        # _logger.info(query)
        # _logger.info((tuple(move_state), tuple(
        #     account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        # _logger.info("======")

        return self.env.cr.fetchall()

    # Pisahkan fungsi undue amount
    def _get_unreconsile_paymentamount(self, move_state, account_type, date_from, partner_ids, company_ids):
        query = '''SELECT l.id
            FROM 
               account_move_line AS l, 
               account_account, 
               account_move am,
               account_partial_reconcile b
            WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND (COALESCE(l.date_maturity,l.date) >= %s)\
                AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND ((a.internal_type='receivable' and a.credit>0) or (a.internal_type='payable' and a.debit>0))
                AND l.id=b.credit_move_id AND b.id is null
                AND l.company_id IN %s'''
        self.env.cr.execute(query, (tuple(move_state), tuple(
            account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))

        # _logger.info("=== get undue amount ===")
        # _logger.info(query)
        # _logger.info((tuple(move_state), tuple(
        #     account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        # _logger.info("======")

        return self.env.cr.fetchall()


    # Terpaksa harus override semua fungsi + ganti signature
    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length, selected_partner_ids):
        periods = {}
        if self._context.get('report_type') == 'excel':
            start = date_from
        else:
            start = datetime.strptime(date_from, "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5 - (i + 1)) * period_length + 1) + \
                '-' + str((5 - i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        res = []
        total = []
        cr = self.env.cr
        company_ids = self.env.context.get(
            'company_ids', (self.env.user.company_id.id,))
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        # build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s',
                   (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids))

        partners = self._get_partners(
            reconciliation_clause, arg_list, selected_partner_ids)
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id']
                       for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, [])
                     for partner in partners)
        if not partner_ids:
            return [], [], {}

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        aml_ids = self._get_undue_amount(
            move_state, account_type, date_from, partner_ids, company_ids)
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.balance
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                # ============== start fix ====================
                if isinstance(date_from, str):
                    if partial_line.max_date <= datetime.strptime(date_from, '%Y-%m-%d').date():
                        line_amount += partial_line.amount
                else:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.amount
                # ============== end fix ====================
            for partial_line in line.matched_credit_ids:
                # if partial_line.max_date <= date_from:
                line_amount -= partial_line.amount
            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(
                account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'],
                              periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    # ============== start fix ====================
                    if isinstance(date_from, str):
                        if partial_line.max_date <= datetime.strptime(date_from, '%Y-%m-%d').date():
                            line_amount += partial_line.amount
                    else:
                        if partial_line.max_date <= date_from:
                            line_amount += partial_line.amount
                    # ============== end fix ====================
                for partial_line in line.matched_credit_ids:
                    # if partial_line.max_date <= date_from:
                    line_amount -= partial_line.amount

                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    if partner_id:
                        partners_amount[partner_id] += line_amount
                        lines[partner_id].append({
                            'line': line,
                            'currency': line.move_id.currency_id.name,
                            'amount': line_amount,
                            'period': i + 1,
                        })
            history.append(partners_amount)

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            # Making sure this partner actually was found by the query
            if partner['partner_id'] in undue_amounts:
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] +
                                  [values[str(i)] for i in range(5)])
            # Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            currency = False
            if lines[partner['partner_id']]:
                currency = lines[partner['partner_id']][0].get(
                    'currency', False)

            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(
                    partner['partner_id'])
                values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[
                    0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
                values['ref'] = browsed_partner.ref
                values['currency'] = currency
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False
                values['ref'] = False
                values['currency'] = False

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)

        return res, total, lines
