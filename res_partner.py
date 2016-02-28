# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, osv
import datetime

class res_partner(osv.osv.osv):
    _name='res.partner'
    _inherit='res.partner'
    
    '''overriding the res.partner model method of functional fields from addons/account/partner.py  '''
    def _credit_debit_get(self, cr, uid, ids, field_names, arg, context=None):
        ctx = context.copy()
        ctx['all_fiscalyear'] = True
        query = self.pool.get('account.move.line')._query_get(cr, uid, context=ctx)
        cr.execute("""SELECT l.partner_id, a.type, SUM(l.debit-l.credit)
                      FROM account_move_line l
                      LEFT JOIN account_account a ON (l.account_id=a.id)
                      WHERE a.type IN ('receivable','payable')
                      AND l.partner_id IN %s
                      AND l.reconcile_id IS NULL
                      AND """ + query + """
                      GROUP BY l.partner_id, a.type
                      """,
                   (tuple(ids),))
        data=cr.fetchall()
        maps = {'receivable':'credit', 'payable':'debit' }
        res = {}
         
        '''setting available_credit as credit_limit value for each partner if 
        their credit_limit is assigned in credit.details model,
            else setting them 0 and applicable_date as false'''
        for id in ids:
            res[id] = {}.fromkeys(field_names, 0.0)
            credit_details_obj=self.pool.get('credit.details')
            credit_details_id=credit_details_obj.search(cr,uid,[('partner_id','=',id)])
            credit_limit_details_obj=self.pool.get('credit.limit.details')
            cl_details_ids=credit_limit_details_obj.search(cr,uid,[('credit_details_id','in',credit_details_id),('cl_applicable_date','<=',datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))],order='cl_applicable_date desc')
            if cl_details_ids:
                credit_limit= credit_limit_details_obj.browse(cr,uid,cl_details_ids[0],context=None).credit_limit
                available_credit= credit_limit
                applicable_date= credit_limit_details_obj.browse(cr,uid,cl_details_ids[0],context=None).cl_applicable_date
                res[id].update({'credit_limit': credit_limit, 'cl_applicable_date': str(applicable_date), 'available_credit':available_credit})
            else:
                res[id].update({'cl_applicable_date': False})
         
        ''' checking in data for each parnter if their is any amount receivable- then calculating credit amnt, available_amount= credit_limit - credit amnt'''    
        for pid,type,val in data:
            if val is None: val=0
            res[pid][maps[type]] = (type=='receivable') and val or -val
             
            credit_details_obj=self.pool.get('credit.details')
            credit_details_id=credit_details_obj.search(cr,uid,[('partner_id','=',pid)])
            credit_limit_details_obj=self.pool.get('credit.limit.details')
            cl_details_ids=credit_limit_details_obj.search(cr,uid,[('credit_details_id','in',credit_details_id),('cl_applicable_date','<=',datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))],order='cl_applicable_date desc')
            if cl_details_ids:
                credit_amnt=res[pid].get('credit',0.0)
                credit_limit= credit_limit_details_obj.browse(cr,uid,cl_details_ids[0],context=None).credit_limit
                available_credit= credit_limit-credit_amnt
                applicable_date=credit_limit_details_obj.browse(cr,uid,cl_details_ids[0],context=None).cl_applicable_date
                 
                res[pid].update({'credit': credit_amnt,'credit_limit': credit_limit, 'cl_applicable_date': str(applicable_date), 'available_credit':available_credit})
             
        return res

        
    def _credit_search(self, cr, uid, obj, name, args, context=None):
        return self._asset_difference_search(cr, uid, obj, name, 'receivable', args, context=context)

    def _debit_search(self, cr, uid, obj, name, args, context=None):
        return self._asset_difference_search(cr, uid, obj, name, 'payable', args, context=context)
   
    
    _columns={ 
                'cash_customer' : osv.fields.boolean('Cash Customer'),
                'is_blocked': osv.fields.boolean('Blocked'),
                'cl_applicable_date': osv.fields.function(_credit_debit_get, type='date', string='Credit Limit Applicable Date', multi='dc', store=False, help='Credit Limit Applicable Date'),
                'available_credit': osv.fields.function(_credit_debit_get, type='float', string='Available Credit', store=False, multi='dc', help='Available Credit') ,
                'credit_details_id': osv.fields.many2one('credit.details'),
                'credit_limit': osv.fields.function(_credit_debit_get, type='float', string='Credit Limit', store=False, multi='dc', help='Credit Limit'),
                'credit': osv.fields.function(_credit_debit_get,fnct_search=_credit_search, string='Total Receivable', multi='dc', help="Total amount this customer owes you."),
                'debit': osv.fields.function(_credit_debit_get, fnct_search=_debit_search, string='Total Payable', multi='dc', help="Total amount you have to pay to this supplier."),
                'customer_blocking_created': osv.fields.boolean('Customer Blocking Created',default=False),
              }
    
    _defaults={
                'cash_customer': True

                }
    
