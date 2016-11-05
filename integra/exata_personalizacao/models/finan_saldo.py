# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import fields, osv
from pybrasil.data import hoje


class finan_conciliacao(osv.Model):
    _name = 'finan.conciliacao'
    _inherit = 'finan.conciliacao'
       
    def get_lancamento_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        for conc_obj in self.browse(cr, uid, ids):
            conc_obj = self.browse(cr, uid, ids[0])
            res_partner_bank_id = conc_obj.res_partner_bank_id.id
            data_inicial = conc_obj.data_inicial
            data_final = conc_obj.data_final

            lanc_ids = []
            if nome_campo == 'lancamento_a_conciliar_ids':
                conciliado = False
                #lanc_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('conciliado', '=', conciliado), ('id', '>', 0)])
                lanc_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('conciliado', '=', conciliado), ('id', '>', 0)])
                #lancamento_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('data_quitacao', '>=', data_inicial), ('data_quitacao', '<=', data_final), ('conciliado', '=', conciliado)])
                for id in lanc_ids:
                    cr.execute("""update finan_lancamento l set data = '{data}' where l.id = {id} and l.data is null""".format(data=conc_obj.data_final,id=id))

            else:
                conciliado = True
                data_inicial = data_final
                #lancamento_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('data_quitacao', '>=', data_inicial), ('data_quitacao', '<=', data_final), ('conciliado', '=', conciliado)])
                #lanc_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('data_compensacao', '>=', data_inicial), ('data_compensacao', '<=', data_final), ('conciliado', '=', conciliado), ('id', '>', 0)])
                lanc_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('data_compensacao', '>=', data_inicial), ('data_compensacao', '<=', data_final), ('conciliado', '=', conciliado)])


            lancamento_ids = []
            for id in lanc_ids:
                lancamento_ids.append(abs(id))
                #lancamento_ids[i] = abs(lancamento_ids[i])

            res[conc_obj.id] = lancamento_ids

        return res

    

finan_conciliacao()


