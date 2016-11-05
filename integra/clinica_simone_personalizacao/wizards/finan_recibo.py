# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv
import os
from finan.wizard.finan_relatorio import Report, JASPER_BASE_DIR
import base64


class finan_recibos(osv.osv_memory):
    _description = u'Recibos de lançamentos'
    _name = 'finan.recibos'
    _inherit = 'ir.wizard.screen'
    _rec_name = 'nome'
    _order = 'nome'

    _columns = {
        'nome': fields.char(u'Nome do arquivo', 60, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
    }

    _defaults = {
        'nome': lambda *a: 'recibo.pdf',
    }

    def gerar_recibos(self, cr, uid, ids, context=None):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        lancamento_ids = context['active_ids']
        lancamento_pool = self.pool.get('finan.lancamento')

        lista_recibo = []
        partner_id = False
        tipo = ''
        complemento = ''
        #
        # Fazemos uma pré-validação das informações
        #
        for lancamento_obj in lancamento_pool.browse(cr, uid, lancamento_ids, context):
            #if not partner_id:
            #    partner_id = lancamento_obj.partner_id.id
            #elif lancamento_obj.partner_id.id != partner_id:
            #    raise osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos de clientes/fornecedores diferentes!')

            if tipo == '':
                tipo = lancamento_obj.tipo
            elif lancamento_obj.tipo != tipo:
                raise osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos de tipos diferentes!')

            if complemento == '':
                complemento = lancamento_obj.complemento
            elif lancamento_obj.complemento != complemento:
                raise osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos com complementos diferentes!')

        rel = Report('Recibo', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'clinica_recibo_financeiro.jrxml')
        rel.parametros['IDS_PLAIN'] = str(lancamento_ids).replace('[', '(').replace(']', ')')
        rel.parametros['COMPANY_ID'] = self.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio')

        pdf, formato = rel.execute()

        banco_de_dados = cr.dbname
        nome = 'Recibo_' + banco_de_dados + '.pdf'
        self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})


finan_recibos()
