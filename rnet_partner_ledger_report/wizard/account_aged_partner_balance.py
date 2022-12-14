import base64
import io
import time

import xlwt
from dateutil.relativedelta import relativedelta
from odoo import fields, models, _
from odoo.exceptions import UserError
import logging


_logger = logging.getLogger(__name__)


class AccountAgedPartnerBalance(models.TransientModel):
    _inherit = 'bi.account.aged.partner.balance'

    data_level = fields.Selection([
        ('summary', 'Aged Partner Balance by Partner'),
        ('summaryarap', 'Aged Partner Balance by AR/AP'),   
        ('summaryaraphistory', 'Aged Partner Balance by AR/AP (History)'),   
        ('detail', 'Detail'),
        ('detailhistory', 'Detail (History)')
    ], required=True, default='summary')

    partner_ids = fields.Many2many('res.partner', string='Partner')

    # Terpaksa harus override semua fungsi wizard
    def print_report_aged_partner(self):
        if self.period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not self.date_from:
            raise UserError(_('You must set a start date.'))

        start = self.date_from
        data = {}
        res = {}
        used_context = {}
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=self.period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (
                    str((5 - (i + 1)) * self.period_length) + '-' + str((5 - i) * self.period_length)) or (
                    '+' + str(4 * self.period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)

        selected_partner_ids = [p.id for p in self.partner_ids]

      #  kay_val_dict = dict(self.target_move)
      #  _logger.info("========111111111111111==========")
        target_move_text = dict(self.fields_get(allfields=['target_move'])['target_move']['selection'])[self.target_move]
        data_level_text = dict(self.fields_get(allfields=['data_level'])['data_level']['selection'])[self.data_level]
      #  _logger.info("========xxxxxxxxxxx==========")
      #  _logger.info(kay_val_dict)
      #  _logger.info("==========xxxxxxxx========")  

        data['form'] = ({
            'target_move': self.target_move,
            'target_move_text': target_move_text,
            'result_selection': self.result_selection,
            'period_length': self.period_length,
            'journal_ids': [a.id for a in self.env['account.journal'].search([])],
            'date_from': self.date_from,
            'data_level': self.data_level,
            'data_level_text': data_level_text,
            'selected_partner_ids': selected_partner_ids,
        })
        used_context.update(
            {
                'state': self.target_move,
                'strict_range': True,
                'journal_ids': [a.id for a in self.env['account.journal'].search([])],
                'date_from': self.date_from,
                'data_level': self.data_level,
                'selected_partner_ids': selected_partner_ids,
            }
        )
        data['form']['used_context'] = used_context
        data['form'].update(res)

        # _logger.info("========xxxxxxxxxxx==========")
        # _logger.info(self.data_level)
        # _logger.info("==========xxxxxxxx========")  
         
        if not self._context.get('report_type') == 'excel':
            if self.data_level in ('summary','summaryarap','summaryaraphistory','detail','detailhistory'):
                raise UserError(
                    _('Print pdf not available, try print to excel.'))
            return self.env.ref('bi_partner_ledger_report.action_aged_partner_balance_report').with_context(
                landscape=True).report_action(self, data=data)
        else:
            if self.data_level == ('summary'):
                _logger.info("===============>"+"rnet.aged_partner_report_summary")  
                return self.env['rnet.aged_partner_report_summary'].to_excel(data)
            elif self.data_level in ('summaryarap','summaryaraphistory'):
                _logger.info("===============>"+"rnet.aged_partner_report_byarap") 
                return self.env['rnet.aged_partner_report_byarap'].to_excel(data)  
            elif self.data_level in ('detail','detailhistory'):
                _logger.info("===============>"+"rnet.aged_partner_report_detail")  
                return self.env['rnet.aged_partner_report_detail'].to_excel(data)
             
            else:
                _logger.info("===============>"+"Aged Partner Balance") 
                filename = 'Aged Partner Balance.xls'
                workbook = xlwt.Workbook()
                worksheet = workbook.add_sheet('Sheet 1')
                date_format = xlwt.XFStyle()
                date_format.num_format_str = 'dd/mm/yyyy'
                style_header = xlwt.easyxf(
                    "font:height 300; font: name Liberation Sans, bold on,color black; align: horiz center")
                style_table_header = xlwt.easyxf(
                    "font: name Liberation Sans, bold on,color black; align: horiz center")

                worksheet.row(0).height_mismatch = True
                worksheet.row(0).height = 500
                worksheet.write_merge(
                    0, 0, 0, 5, "Aged Partner Balance", style=style_header)
                worksheet.write(2, 0, 'Start Date')
                worksheet.write(2, 1, 'Period Length (days)')
                worksheet.write(2, 2, "Partner's")
                worksheet.write(2, 3, "Target Moves")
                worksheet.write(3, 0, self.date_from or '-', date_format)
                worksheet.write(3, 1, self.period_length)
                worksheet.write(3, 2, self.result_selection)
                worksheet.write(
                    3, 3, 'All Posted Entries' if self.target_move == 'posted' else 'All Entries')
                worksheet.write(5, 0, 'Partners', style=style_table_header)
                worksheet.write(5, 1, 'Unreconsile Payment', style=style_table_header)
                worksheet.write(5, 2, 'Over due', style=style_table_header)
                worksheet.write(5, 3, res['4']['name'],
                                style=style_table_header)
                worksheet.write(5, 4, res['3']['name'],
                                style=style_table_header)
                worksheet.write(5, 5, res['2']['name'],
                                style=style_table_header)
                worksheet.write(5, 6, res['1']['name'],
                                style=style_table_header)
                worksheet.write(5, 7, res['0']['name'],
                                style=style_table_header)
                worksheet.write(5, 8, "Total")
                row = 6
                col = 0
                report_values = self.env['report.bi_partner_ledger_report.bi_report_agedpartnerbalance']._get_report_values(
                    self, data=data)
                if report_values['get_partner_lines']:
                    worksheet.write(row, col, 'Account Total',
                                    style=style_table_header)
                    worksheet.write(
                        row, col + 2, report_values['get_direction'][6], style=style_table_header)
                    worksheet.write(
                        row, col + 3, report_values['get_direction'][4], style=style_table_header)
                    worksheet.write(
                        row, col + 4, report_values['get_direction'][3], style=style_table_header)
                    worksheet.write(
                        row, col + 5, report_values['get_direction'][2], style=style_table_header)
                    worksheet.write(
                        row, col + 6, report_values['get_direction'][1], style=style_table_header)
                    worksheet.write(
                        row, col + 7, report_values['get_direction'][0], style=style_table_header)
                    worksheet.write(
                        row, col + 8, report_values['get_direction'][5], style=style_table_header)
                row += 1
                for partner in report_values['get_partner_lines']:
                    worksheet.write(row, col, partner['name'])

                    worksheet.write(row, col + 2, partner['direction'])
                    worksheet.write(row, col + 3, partner['4'])
                    worksheet.write(row, col + 4, partner['3'])
                    worksheet.write(row, col + 5, partner['2'])
                    worksheet.write(row, col + 6, partner['1'])
                    worksheet.write(row, col + 7, partner['0'])
                    worksheet.write(row, col + 8, partner['total'])
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
