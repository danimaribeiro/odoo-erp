# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from finan.wizard.finan_relatorio import Report
import os
import base64

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    def _verifica_email(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            if len(item_obj.mail_message_ids) > 0:
                res[item_obj.id] = True
            else:
                res[item_obj.id] = False

        return res

    _columns = {
        'verifica_email': fields.function(_verifica_email, type='boolean', method=True, string=u'Verifica email'),
        'aprovado_uid': fields.many2one('res.users', u'Aprovado'),
        'eh_abastecimento': fields.boolean(u'É abastecimento?'),
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo'),
        'proprietario_id': fields.related('veiculo_id', 'proprietario_id', type='many2one', relation='res.partner', string=u'Proprietário/locadora'),
    }

    def onchange_veiculo_id(self, cr, uid, ids, veiculo_id, context={}):
        if not veiculo_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        veiculo_obj = self.pool.get('frota.veiculo').browse(cr, uid, veiculo_id)

        if veiculo_obj.proprietario_id:
            valores['proprietario_id'] = veiculo_obj.proprietario_id.id

        return res

    def imprime_ordem_compra(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        rel = Report('Ordem de Compra', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'ordem_compra_exata.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['UID'] = uid
        rel.parametros['ULTIMAS_COMPRAS'] = True

        nome = rel_obj.name + '.pdf'
        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'purchase.order'), ('res_id', '=', id), ('name', '=', nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome,
            'datas_fname': nome,
            'res_model': 'purchase.order',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True


purchase_order()
