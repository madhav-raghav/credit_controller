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

from openerp.tools.translate import _
from openerp import models, fields, api, osv
from openerp import SUPERUSER_ID
import datetime

class account_invoice(models.Model):
    _inherit = "account.invoice"
   
    ''' Overriding to prevent a blocked customer or customer having available_credit <0.0 while validating the invoice'''
    @api.multi
    def action_date_assign(self):
        for inv in self:
            if inv.partner_id.commercial_partner_id :
                partner_id=inv.partner_id.commercial_partner_id
                credit_limit=partner_id.credit_limit
                available_credit=partner_id.available_credit
            else:
                partner_id=inv.partner_id
                credit_limit=partner_id.credit_limit
                available_credit=partner_id.available_credit
            
            ''' checking if partner is credit customer (not a cash customer)'''
            if partner_id.customer and not partner_id.cash_customer:
                '''if the partner is not blocked'''
                if partner_id.is_blocked == False :
                    ''' if the credit limits are set and available credit are less than or equal to zero'''
                    if credit_limit > 0.0 and available_credit <0.0:
                        raise osv.osv.except_osv(_('Warning'), _("The Customer has exceeded his credit limit of %s !  Available Credit:' %s ' ") % (credit_limit,available_credit))
                    else:
                        pass
                else:
                    raise osv.osv.except_osv(_('Warning'), _("The Customer has been Blocked by the system as he has over utilized his Credit Limit: '%s' and Available Credit:'%s' ") % (credit_limit,available_credit))
            res = inv.onchange_payment_term_date_invoice(inv.payment_term.id, inv.date_invoice)
            if res and res.get('value'):
                inv.write(res['value'])
        return True
    
    
    ''' Overriding to block the customer if available credit turns out to be negative after validating the invoice'''
    @api.multi
    def invoice_validate(self):
        res =super(account_invoice,self).invoice_validate()
        if self.partner_id.commercial_partner_id :
            partner_id=self.partner_id.commercial_partner_id
            credit_limit=partner_id.credit_limit
            available_credit=partner_id.available_credit
        else:
            partner_id=self.partner_id
            credit_limit=partner_id.credit_limit
            available_credit=partner_id.available_credit
            
        if partner_id.customer and not partner_id.cash_customer:
            if credit_limit > 0.0 and available_credit <0.0:
                partner_id.is_blocked = True
                cust_blocking_obj=self.env['customer.blocking'].search([('partner_id','=',partner_id.id)])
                if cust_blocking_obj:
                    data={'state' : 'block', 'reason': 'The system has blocked the customer due to Credit Unavailability', 'blocked_by' : SUPERUSER_ID, 'blocking_date_time' : str(datetime.datetime.now())}
                    vals={'block': [(0,0,data)]}
                    cust_blocking_obj.write(vals)
                    
                else:
                    data={'state' : 'block', 'reason': 'The system has blocked the customer due to Credit Unavailability', 'blocked_by' : SUPERUSER_ID, 'blocking_date_time' : str(datetime.datetime.now())}
                    vals={'partner_id': partner_id.id,'block': [(0, 0, data)]}
                    cust_blocking_obj.create(vals)
        
        
        return res