# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields


class ir_attachment(orm.Model):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    def unlink(self, cr, uid, ids, context={}):
        for anexo_obj in self.browse(cr, uid, ids, context=context):
            print('apagando anexo model', anexo_obj.res_model, uid)
            if anexo_obj.res_model == 'res.partner':
                #
                # Só pode excluir anexo a Simone Fior, id 3
                #
                if uid != 1 and uid != 3:
                    raise osv.except_osv(u'Erro', u'Você não tem permissão de excluir anexos do cadastro de clientes')

        return super(ir_attachment, self).unlink(cr, uid, ids, context=context)


ir_attachment()
