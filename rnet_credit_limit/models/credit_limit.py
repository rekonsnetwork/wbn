import time

import logging

_logger = logging.getLogger(__name__)


class CreditLimit:
    def is_credit_so_reached(self, partner, inv_rec, sale_amount):
        if partner.credit_limit > 0:
            if partner.credit > partner.credit_limit:
                return True
            else:
                credit = 0
                inv_total_amt = 0

                sale_amt = sum([sale for sale in sale_amount])

                for inv in inv_rec:
                    inv_total_amt += inv.amount_total - inv.residual

                if partner.parent_id and partner.parent_id.credit < 0:
                    credit = partner.parent_id.credit

                elif partner.credit < 0:
                    credit = partner.credit

                total_sales = sale_amt + credit - inv_total_amt

                if total_sales > partner.credit_limit:
                    return True
                else:
                    return False
        else:
            return False

    def is_so_overdue(self, partner_id, env, overdue_days):
        account_type = ['receivable']
        date_from = time.strftime('%Y-%m-%d')
        target_move = 'all'
        period_length = 30

        balance, total, dummy = env['report.bi_partner_ledger_report.bi_report_agedpartnerbalance']._get_partner_move_lines(
            account_type, date_from, target_move, period_length, [partner_id])
        #overdue_days = int(env['ir.config_parameter'].sudo().get_param('rnet_credit_limit.maximum_allowed_ap_so'))

        partner_limit = self.is_partner_aged(partner_id, balance, overdue_days)
        if partner_limit['overdue'] > 0:
            return True
        return False

    def is_partner_aged(self, partner_id, partners, days):
        if days <= 0:
            raise Exception('Overdue days cannot negative')

        partner_limit = {
            'overdue': 0,
            'id': -1,
            'name': ''
        }

        age_range = 0
        partner = list(
            filter(lambda p: p['partner_id'] == partner_id, partners))
        if not partner:
            return partner_limit

        if days in range(0, 30, 1):
            age_range = 4
        elif days in range(31, 60, 1):
            age_range = 3
        elif days in range(61, 90, 1):
            age_range = 2
        elif days in range(91, 120, 1):
            age_range = 1

        limit = 0
        for i in range(age_range, -1, -1):
            limit = limit + partner[0][str(i)]

        partner_limit['id'] = partner[0]['partner_id']
        partner_limit['name'] = partner[0]['name']
        partner_limit['overdue'] = limit

        return partner_limit
