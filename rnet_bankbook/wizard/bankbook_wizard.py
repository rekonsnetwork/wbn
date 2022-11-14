from datetime import datetime, timedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class BankbookWizard(models.TransientModel):
    _name = 'bankbook.wizard'

  #  _logger.info("START1 ===============")  

    start_date = fields.Date('Start Date',required=True, default=datetime.now().strftime('%Y-%m-01'))
    end_date = fields.Date('End Date',required=True, default=datetime.now().strftime('%Y-%m-%d'))

    bank_account_id = fields.Many2one('account.journal', required=True, string='Bank Account', domain="[('type', '=', 'bank')]")
    target_moves = fields.Selection([('posted', 'All Posted Entries'), ('all', 'All Entries'),],
                                    string='Target Moves', required=True, default='posted')

    def print(self):

        data = {}

        bank_account_desc= str(self.bank_account_id.name)  +' ('+str(self.bank_account_id.default_debit_account_id.code)+' - '+str(self.bank_account_id.default_debit_account_id.name)+')'
        bank_account_text= str(self.bank_account_id.name)  
        target_move_text = dict(self.fields_get(allfields=['target_moves'])['target_moves']['selection'])[self.target_moves]

        data['form'] = ({
            'bank_account_id': self.bank_account_id,
            'bank_account_text': bank_account_text,
            'bank_account_desc': bank_account_desc,
            'target_move': self.target_moves,
            'target_move_text': target_move_text,
            'start_date': self.start_date,
            'end_date': self.end_date,
        })

        report_data = self._get_report_data()
        if not report_data:
            raise ValidationError('Bankbook is empty')

        if self._context.get('report_type') == 'excel':
            return self.env['bankbook.excel'].print(report_data,data)
        else:
            raise ValidationError('Not implemented')

    def _get_report_data(self):
        params = []

        query_target_moves=""
        if (self.target_moves == 'posted'):
            query_target_moves = " and journal_state='posted' "

        query =  ''' Select
                        journal_date "Journal Date",  
												coalesce(partner,'') || coalesce(' ('||partner_code||')','')  as "Partner",												
												jurnal_item_label|| coalesce(', '||a.journal_no,'') || coalesce(', '||a.ref,'') || coalesce(', '||a.ref2,'')  || coalesce(', '||a.ref3,'')  as "Label",
												debit as "Debit",
												credit as "Credit",  
												begining_balance as "Begining Balance", 
												balance as "Mutasi",
												begining_balance+ running_balance as "Balance",
												journal_state as "State"												
                        from
                        (
                        Select 
                            a.journal_date, a.journal_create_date, a.journal_no, a.journal_state, a.payment_no, a.expense_lable, a.ref, a.ref2, a.ref3,  a.partner_code,a.partner, a.jurnal_item_label, 
														a.debit, a.credit, a.balance, b.begining_balance,   
														sum(a.balance) over (order by journal_date, journal_create_date asc rows between unbounded preceding and current row) as running_balance
                        from 
                        vw_account_move_line a
                            left join 
                            (  
                            Select sum(balance) as begining_balance from vw_account_move_line where   
															(account_id=(Select default_debit_account_id from account_journal where id= %s)  or 
													  	 account_id=(Select default_credit_account_id from account_journal where id= %s) )	and journal_date<%s 

                 '''
        query =  query + query_target_moves        
        query =  query + '''                                                
                             ) b on 1=1                            
                        where  
                            ( a.account_id=(Select default_debit_account_id from account_journal where id= %s)  or 
							  a.account_id=(Select default_credit_account_id from account_journal where id= %s) )	
							  and journal_date>=%s
							  and journal_date<=%s
                         '''
        query =  query + query_target_moves        
        query =  query + '''     

                        order by  journal_date, journal_create_date
                        ) a
												
										UNION ALL
										Select
										     NULL,
											 NULL,
											 null,
											 (Select sum(debit)  from vw_account_move_line where 
											        (account_id=(Select default_debit_account_id from account_journal where id= %s)  or 
													  	 account_id=(Select default_credit_account_id from account_journal where id= %s) )	
															 and journal_date>=%s and journal_date<=%s
                                                                          '''
        query =  query + query_target_moves        
        query =  query + '''         
                                                              ) as debit,		
															 
												(Select sum(credit)  from vw_account_move_line where 
											        (account_id=(Select default_debit_account_id from account_journal where id=  %s)  or 
													  	 account_id=(Select default_credit_account_id from account_journal where id=  %s) )	
															 and journal_date>= %s and journal_date<= %s
                         '''
        query =  query + query_target_moves        
        query =  query + '''                                                          
                                                             ) as credit,	
															 
										   (Select sum(balance)  from vw_account_move_line where  
											        (account_id=(Select default_debit_account_id from account_journal where id= %s)  or 
													  	 account_id=(Select default_credit_account_id from account_journal where id= %s) )	
														   and journal_date<%s
                          '''
        query =  query + query_target_moves        
        query =  query + '''                                                       
                                                           ) as begining_balance,
															 
												 (Select sum(balance)  from vw_account_move_line where 
											        (account_id=(Select default_debit_account_id from account_journal where id= %s)  or 
													  	 account_id=(Select default_credit_account_id from account_journal where id= %s) )	
															  and journal_date>= %s and journal_date<= %s
                         '''
        query =  query + query_target_moves        
        query =  query + '''                                                           
                                                              ) as mutasi,

											   (Select sum(balance) from vw_account_move_line where  
											        (account_id=(Select default_debit_account_id from account_journal where id= %s)  or 
													  	 account_id=(Select default_credit_account_id from account_journal where id= %s) )															
															and journal_date<=%s
                         '''
        query =  query + query_target_moves        
        query =  query + '''                                                         
                                                            ) as balance,									
										    'SYS_SUMMARY'
                    '''



        params = (
                    self.bank_account_id.id,self.bank_account_id.id, self.start_date, 
                    self.bank_account_id.id,self.bank_account_id.id, self.start_date, self.end_date,
                    self.bank_account_id.id,self.bank_account_id.id, self.start_date, self.end_date,
                    self.bank_account_id.id,self.bank_account_id.id, self.start_date, self.end_date,
                    self.bank_account_id.id,self.bank_account_id.id, self.start_date,
                    self.bank_account_id.id,self.bank_account_id.id, self.start_date, self.end_date,
                    self.bank_account_id.id,self.bank_account_id.id, self.end_date
                )

        # st=(query % params)
        # _logger.info(st)          
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()
