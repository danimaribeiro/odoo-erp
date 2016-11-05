# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.valor.decimal import Decimal as D
from finan.wizard.finan_relatorio import Report
import os
import base64

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class purchase_order(orm.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'


    _columns = {
                'sale_order_id': fields.many2one('sale.order', u'Pedido de Venda'),
    
    }
    
    
    def imprime_ordem_compra_id(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids
        rel = Report('Ordem de Compra', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'di_distribuidora_ordem_compra.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['UID'] = uid

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'purchase.order'), ('res_id', '=', id), ('name', '=', 'ordem_compra_di.pdf')])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': 'ordem_compra_di.pdf',
            'datas_fname': 'ordem_compra_di.pdf',
            'res_model': 'purchase.order',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True
    


purchase_order()
