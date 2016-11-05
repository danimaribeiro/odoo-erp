# -*- coding: utf-8 -*-

from osv import fields, osv



class email_template(osv.osv_memory):
    _name = 'email.template'
    _inherit = 'email.template'

    _columns = {
        'subject': fields.char('Subject', size=512, translate=False, help="Subject (placeholders may be used here)",),
        'body_text': fields.text('Text contents', translate=False, help="Plaintext version of the message (placeholders may be used here)"),
        'body_html': fields.text('Rich-text contents', translate=False, help="Rich-text/HTML version of the message (placeholders may be used here)"),
    }


email_template()
