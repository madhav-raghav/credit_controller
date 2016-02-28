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
from openerp import SUPERUSER_ID, api
import datetime
import time
from datetime import date
from operator import itemgetter
from dateutil.relativedelta import relativedelta
from openerp.exceptions import Warning


'''class for credit_limit one2many field from credit_details model'''
class credit_limit_details(models.Model):
    _name='credit.limit.details'
    
    _order='cl_applicable_date desc'
    
    cl_details_no = fields.Char('Credit Details No.')
    credit_details_id=fields.Many2one('credit.details','Credit Details')
    credit_limit = fields.Float('Credit Limit')
    cl_applicable_date = fields.Datetime('Applicable From')
    assigned_by = fields.Many2one('res.users','Users')
    make_readonly=fields.Boolean('Make fields readonly')
    
    _sql_constraints = [('cl_applicable_date_uniq', 'unique(cl_applicable_date,credit_details_id)', 'You cannot assign another credit limit on same date!')]

    def default_get(self, cr, uid, fields, context=None):
        res = super(credit_limit_details, self).default_get(cr, uid, fields, context=context)
        res.update({
            'cl_applicable_date': time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        return res
        
    @api.model
    def create(self,vals):
        credit_limit=float(vals.get('credit_limit',0.0))
        x=tuple(map(int,str(vals.get('cl_applicable_date').split()[0]).split('-')))
        '''creating date object from a tuple of format(2014,16,08) '''
        cl_applicable_date=datetime.date(x[0],x[1],x[2])
        '''if new credit limit is assigned or created then checking then checking with the current date
            if  yes then calcualting the available credit, if available credit is >=0 
            and customer is blocked then make a unblock entry in cusotmer blocking table '''
        current_date_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cd_obj=self.env['credit.details'].search([('id','=',vals.get('credit_details_id'))])
        cld_obj=list(self.search([('credit_details_id','=',vals.get('credit_details_id')),('cl_applicable_date','<',current_date_time)],order='cl_applicable_date desc'))
        if cld_obj:
            fetched_cl_date_time=datetime.datetime.strptime(vals.get('cl_applicable_date'), '%Y-%m-%d %H:%M:%S')
            latest_cl_date_time= datetime.datetime.strptime(cld_obj[0].cl_applicable_date, '%Y-%m-%d %H:%M:%S')
            if fetched_cl_date_time < latest_cl_date_time:
                raise osv.osv.except_osv(_('Warning'), _("You cannot make a back dated entry from the recent applicable date!"))
                    
        if cl_applicable_date == date.today():    
            utilised_credit=cd_obj.partner_id.credit
            available_credit= credit_limit - utilised_credit
            
            if available_credit >=0 :
                if cd_obj.partner_id.is_blocked:
                    cust_blocking_obj=self.env['customer.blocking'].search([('partner_id','=',cd_obj.partner_id.id)])
                    if cust_blocking_obj:
                        data={'state' : 'unblock', 'reason': 'Credit Limit Extended', 'blocked_by' : SUPERUSER_ID, 'blocking_date_time' : str(datetime.datetime.now())}
                        dict={'block': [(0, 0, data)]}
                        cust_blocking_obj.write(dict)
            else:
                if not cd_obj.partner_id.is_blocked:
                    cust_blocking_obj=self.env['customer.blocking'].search([('partner_id','=',cd_obj.partner_id.id)])
                    if cust_blocking_obj:
                        data={'state' : 'block', 'reason': 'Credit Limit Shortened', 'blocked_by' : SUPERUSER_ID, 'blocking_date_time' : str(datetime.datetime.now())}
                        dict={'block': [(0, 0, data)]}
                        cust_blocking_obj.write(dict) 
        
        seq=self.env['ir.sequence'].get('credit.limit.details')
        vals.update({'make_readonly' : True, 'cl_details_no': seq})  
#         credit_details_obj=self.env['credit.details'].search([('id','=',vals.get('cl_details_no',False))])
#         credit_details_obj.credit_limit_latest= vals.get('credit_limit',False)
#         vals.update({'assigned_by': self.env.uid})
        return super(credit_limit_details,self).create(vals)
    
    '''Overriding unlink() so that credit limit once assigned cannot be deleted'''
    @api.multi
    def unlink(self):
        return True
    
'''class to maintain details of the customer credit.
It is credit controller which allows to assign credit limit to a customer '''    
class credit_details(models.Model):
    _name='credit.details'
    _rec_name='credit_details_no'
    
    credit_details_no = fields.Char('Credit Details ID',default = '/')
    partner_id =      fields.Many2one('res.partner', help='Customer Name')
    customer_phone =   fields.Char(related = 'partner_id.phone',readonly=True,store=False, help='Customer Phone')
    available_credit = fields.Float(related = 'partner_id.available_credit',store=False, help='Available Credit')
    utilized_credit = fields.Float(related='partner_id.credit',readonly=True, store=False, help='Utilized Credit')
    credit_limit =   fields.One2many('credit.limit.details','credit_details_id', help='Credit Limit Details')
    reg_form = fields.Binary('Scanned Reg. Form', help="Add Scanned Customer Registration Form Here")
    credit_limit_latest= fields.Float(related='partner_id.credit_limit',readonly=True, store=False,string="Credit Limit",help="Latest Credit Limit Assigned")
    company_id = fields.Many2one(related='partner_id.company_id', store=True, help='Selected Customer Company')
    make_readonly=fields.Boolean('Make fields readonly')
    
    _sql_constraints = [('partner_id_uniq', 'unique(partner_id)', 'Credit Limit Form Already Exists For The Customer!')]
    
    ''' On create disable cash_customer checkbox in partner and its child_partners-(cash_customer field used for setting domain)'''
    @api.model        
    def create(self,vals):
        credit_details_seq=self.env['ir.sequence'].get('credit.details')
        vals.update({'credit_details_no':credit_details_seq, 'make_readonly': True})
        res=super(credit_details,self).create(vals)
        partners=self.env['res.partner'].search([('commercial_partner_id','=',vals.get('partner_id',False))])
        for part in partners:
            part.write({'cash_customer' : False, 'credit_details_id': res.id})
        return res
        
    ''' On delete enable the cash_stuomer checkbox in partner'''
    @api.multi
    def unlink(self):
        for record in self:
            record.partner_id.cash_customer=True
        return super(credit_details,self).unlink()
    
    

class blocking_details(models.Model):
    _name='blocking.details'
    _rec_name='blocking_no'
    
    _order='blocking_no desc'
    
    blocking_no = fields.Char('Blocking No.')
    blocking_date_time= fields.Datetime('Blocking Date & Time', default= datetime.datetime.now())
    state=fields.Selection([('block','Blocked'),('unblock','Un-blocked')],'State')
    reason= fields.Text('Reason')
    blocked_by= fields.Many2one('res.users')
    customer_blocking_id= fields.Many2one('customer.blocking')
    make_readonly=fields.Boolean('Make fields readonly')
    
    ''' method called from create() to block partners'''
    @api.multi
    def block_partner(self,partners,vals):
        for rec in partners:
            rec.is_blocked=True
            rec.sale_warn='block'
            rec.sale_warn_msg=vals.get('reason')
            rec.invoice_warn='block'
            rec.invoice_warn_msg=vals.get('reason')
        return True
    
    ''' method called from create() to unblock partners'''
    @api.multi
    def unblock_partner(self,partners,vals):
        for rec in partners:
            rec.is_blocked=False
            rec.sale_warn='no-message'
            rec.invoice_warn='no-message'
        return True
    
    @api.multi
    def email_blocked_partners(self,child_partners,blocking_details_id,status):
        template_obj = self.env['email.template']
        if status=='block':
            template_id = template_obj.search([('model_id.model', '=','blocking.details'),('name','=','Customer Blocking Notification Email')])
        else:
            template_id = template_obj.search([('model_id.model', '=','blocking.details'),('name','=','Customer Unblocking Notification Email')])
            
        if not template_id:
            raise Warning('Template Not Found')
        emails=str()
        email_cc=str()
        
        categ_ids=self.env['hr.employee.category'].search([('name','in',['Sales Person','Credit Controller', 'HOD'])]).ids
        
        incharge_emp=self.env['hr.employee'].search([('category_ids','in',categ_ids),('company_id','=',child_partners[0].company_id.id)])
        
        emp_objs = incharge_emp if categ_ids else []
        
#         if len(emp_objs) == 0:
#             raise Warning('No Employee Incharge found with HOD or SalesPerson or CreditController tag for keeping into the CC for a notification mail !')
        
        for emp in emp_objs:
            if emp.work_email:
                email_cc+=(str(emp.work_email))+','
                
        for partner in child_partners:
            if partner.email:
                emails+=(str(partner.email))+',' 
        
#         if email_cc =='':
#             raise Warning('Atleast one email id should be present among Employees having HOD,SalesPerson and CreditController Tags !')
        
        if emails !='':
            template_id.write({'email_to': emails,'email_cc': email_cc})#'email_from':'vipin.tripathi@drishtigroup.com'},context=None)
            mail_id=template_id.send_mail(blocking_details_id)
        else:
            raise Warning('Please define an Email-ID for the blocked/unblocked partner')
        return True
    
    '''All blocking / unblocking functionality is triggered with a create record in customer blocking'''
    @api.model
    def create(self,vals):
        vals.update({'blocking_no': self.env['ir.sequence'].get('block.customer')})
        customer_blocking_obj=self.env['customer.blocking'].search([('id','=',vals.get('customer_blocking_id',False))])
        child_partners=self.env['res.partner'].search([('commercial_partner_id','=',customer_blocking_obj.partner_id.id)])
        if vals.get('state')=='block':
            self.block_partner(child_partners,vals)  
            
        elif vals.get('state')=='unblock':
            self.unblock_partner(child_partners,vals)  
        
        customer_blocking_obj.status= vals.get('state')
        vals.update({'make_readonly' : True})   
        res= super(blocking_details,self).create(vals)
        if vals.get('state')=='block':
            self.email_blocked_partners(child_partners,res.id,'block')
        else:
            self.email_blocked_partners(child_partners,res.id,'unblock')
            
        return res
        
    '''Overriding unlink() so that blocking/unblocking entries cannot be deleted'''
    @api.multi
    def unlink(self):
        return True
 

class customer_blocking(models.Model):
    _name='customer.blocking'
    _rec_name='customer_blocking_id'
    
    customer_blocking_id=fields.Char('Customer Blocking No.')
    partner_id= fields.Many2one('res.partner', help='Customer Name')
    customer_phone= fields.Char(related='partner_id.phone', store=False, help='Customer Phone')
#     customer_code= fields.Char(related='partner_id.customer_code', store=False, help='Customer ID No.')
#     tin_no= fields.Char(related='partner_id.tin_no', store=False, help='TIN Number from Customer')
    credit_limit=fields.Float(related='partner_id.credit_limit', store=False, string="Credit Limit")
    utilized_credit= fields.Float(related='partner_id.credit', store=False, string='Utilized Credit')
    available_credit=fields.Float(related='partner_id.available_credit',store=False, string='Available Credit')
    status= fields.Selection([('block','Blocked'),('unblock','Un-blocked')],'Status')
    company_id = fields.Many2one(related='partner_id.company_id', store=True, help='Selected Customer Company')
    block= fields.One2many('blocking.details','customer_blocking_id',help='Blocking Details')
    
    '''On create enable the checkbox customer_blocking_created in partner (used for setting domain ) '''
    @api.model
    def create(self,vals):
        partner_obj=self.env['res.partner'].search([('id','=',vals.get('partner_id',False))])
        if partner_obj.is_blocked:
            vals.update({'status' : 'block'})
        else:
            vals.update({'status' : 'unblock'})
            
        partner_obj.write({'customer_blocking_created' : True})
        seq=self.env['ir.sequence'].get('customer.blocking.no')
        vals.update({'customer_blocking_id': seq})
        return super(customer_blocking,self).create(vals)
    
    @api.multi
    def unlink(self):
        for record in self:
            record.partner_id.customer_blocking_created=False
        return super(customer_blocking,self).unlink()
    
    '''Method called from Scheduler for blocking the customers whose payment is due by 90days '''
    @api.model
    def block_overdue_customer(self):
        date_year_start= date(date.today().year, 1, 1)
        date_today= date.today()
        date_due= date_today + relativedelta( days = -90 )
        invoices=self.env['account.invoice'].search([('state','=','open'),('date_invoice','>',date_year_start),('date_invoice','<',date_due),('type','=','out_invoice') ])
        customer_set=set()
        for inv in invoices:
            if inv.partner_id.cash_customer ==False:
                customer_set.add(inv.partner_id)
        
        customers=list(customer_set)
#         customers=self.env['res.partner'].search([('id','in',list(customer_set))])
        for cust in customers:
            if cust.is_blocked==False:
                cust.is_blocked = True
                
                cust_blocking_obj=self.env['customer.blocking'].search([('partner_id','=',cust.id)])
                if cust_blocking_obj:
                    data={'state' : 'block', 'reason': 'The customer is over due by 90 days on one of his invoices', 'blocked_by' : SUPERUSER_ID, 'blocking_date_time' : str(datetime.datetime.now())}
                    vals={'block': [(0, 0, data)]}
                    cust_blocking_obj.write(vals)
                else:
                    data={'state' : 'block', 'reason': 'The customer is over due by 90 days on one of his invoices', 'blocked_by' : SUPERUSER_ID, 'blocking_date_time' : str(datetime.datetime.now())}
                    vals={'partner_id': cust.id,'block': [(0, 0, data)]}
                    cust_blocking_obj.create(vals)
        return True
    
    
