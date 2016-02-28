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

{
    'name': 'Credit Controller ',
    'version': '1.1',
    'author': 'Drishti Tech',
    'category' : 'Accounting & Finance',
    'sequence': 21,
    'website': 'http://www.drishtitech.com',
    'summary': 'Customer Credit Controller',
    'description': """
Credit Controller
==========================

This application enables you to manage the credit limit of the customers...

    """,
    'author': 'DrishtiTech',
    'website': 'http://www.drishtitech.com',
    'images': [],
    'depends': ['account','account_accountant','warning','hr','simdi_employee_tags'],
    'data': [
             'overdue_customer_blocking_cron.xml',
             'data/customer_blocking_notification_email.xml',
             'data/customer_unblocking_notification_email.xml',
             'credit_controller_view.xml',
            'credit_conroller_sequence.xml'

             ],
   
    'demo': [],
    'test': [
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [  ],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
