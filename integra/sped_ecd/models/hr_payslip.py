# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class hr_payslip(osv.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'

    _columns = {
        'lote_id': fields.many2one('lote.contabilidade',u'Lançamentos contábeis'),
    }
    #def write(self, cr, uid, ids, vals, context={}):
        
    #    for lanc_obj in self.browse(cr, uid, ids):
    #        if lanc_obj.lote_id:
    #            raise osv.except_osv(u'Inválido !', u'Lançamento ja importado para contabildade! Lote: ' + str(lanc_obj.lote_id.codigo)) 

    #    res = super(finan_lancamento, self).write(cr, uid, ids, vals, context)
        
    #    return res
    
    def unlink(self, cr, uid, ids, context={}):
        
        for slip_obj in self.browse(cr, uid, ids):
            if slip_obj.lote_id:
                raise osv.except_osv(u'Inválido !', u'Lançamento ja importado para contabildade! Lote: ' + str(slip_obj.lote_id.codigo)) 

        res = super(hr_payslip, self).unlink(cr, uid, ids, context)
        
        return res

hr_payslip()
