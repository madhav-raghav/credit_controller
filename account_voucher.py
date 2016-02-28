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
from openerp import SUPERUSER_ID, api

class account_voucher(osv.osv.osv):
    _inherit='account.voucher'
    
    ''' overriding to check available credit amnt after receiving a payment comes out to be positive then,
    if the customer is blocked it will be automatically unblocked by the system'''
    def action_move_line_create(self, cr, uid, ids, context=None):
        res=super(account_voucher,self).action_move_line_create(cr, uid, ids, context=None)
        
        ''' code for calculating commission after payment received with help of reference from voucher '''
        for voucher in self.browse(cr,uid,ids,context=None):
            if voucher.partner_id.customer and not voucher.partner_id.cash_customer:
                        if voucher.partner_id.available_credit >=0:
                            if voucher.partner_id.is_blocked:
                                cust_blocking_obj=self.pool.get('customer.blocking')
                                cust_blocking_id=cust_blocking_obj.search(cr,uid,[('partner_id','=',voucher.partner_id.id)])
                                if cust_blocking_id:
                                    data={'state' : 'unblock', 'reason': 'Payment received from Customer and Credit Limit is now positive figure', 'blocked_by' : SUPERUSER_ID, 'blocking_date_time' : str(datetime.datetime.now())}
                                    vals={'block': [(0, 0, data)]}
                                    cust_blocking_obj.write(cr,uid,cust_blocking_id,vals)
        
        return res
            
        ''' commission end'''