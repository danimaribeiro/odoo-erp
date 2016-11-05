# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

import os
import base64
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora, hoje
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

PROPRIEDADE = [
    ['P', u'Próprio'],
    ['T', u'Terceiros'],
    ['L', u'Terceiros-Locação'],
    ['A', u'Terceiros-Grupo Exata'],
    ['TA', u'Terceiros-Associados'],
]


class const_imovel(osv.Model):
    _inherit = 'const.imovel'

    _columns = {
        'propriedade': fields.selection(PROPRIEDADE, u'Propriedade', select=True),
        'chaves_ids': fields.one2many('const.imovel.controle.chave', 'imovel_id', u'Chaves dos Imóveis'),
        'posicao': fields.integer(u'Posição no Mural'),
        'reserva_ids': fields.one2many('const.reserva.imovel', 'imovel_id', u'Contrato'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', select=True, ondelete='restrict'),
        'cc_project_id': fields.related('centrocusto_id', 'project_id', type='many2one', relation='project.project', string=u'Projeto CC', readonly=True),
        'conta_id': fields.many2one('finan.conta', u'Conta Financeira', select=True, ondelete='restrict'),
    }

    def imprime_etiqueta(self, cr, uid, ids, context={}):

        for imovel_obj in self.browse(cr, uid, ids):

            dados = {
                'numero': str(imovel_obj.posicao) or '',
                'codigo': imovel_obj.codigo or '',
                'endereco': imovel_obj.endereco or '',
                'bairro': imovel_obj.bairro or '',
                'edificio': imovel_obj.condominio or '',
                'apto': imovel_obj.apartamento or '',
                'agenciador': '',
            }
            for agenciador_obj in imovel_obj.agenciador_ids:
                dados['agenciador'] = agenciador_obj.name or ''
                break

            nome_arquivo = JASPER_BASE_DIR + 'exata_controle_chaves.ods'
            print(dados)

            planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados)
            nome = u'Controle_Chaves_' + imovel_obj.descricao_lista + '.xlsx'

            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'const.imovel'), ('res_id', '=', imovel_obj.id), ('name', '=', nome)])
            #
            # Apaga os recibos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': planilha,
                'name': nome,
                'datas_fname': nome,
                'res_model': 'const.imovel',
                'res_id':imovel_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

        return True

    def verifica_reserva_imovel(self, cr, uid, ids=[], context={}):

        reserva_pool = self.pool.get('const.reserva.imovel')

        if not ids:
            ids = reserva_pool.search(cr, 1, [('imovel_id.situacao', '=', 'R'), ('data_inicial', '!=', False), ('data_final', '=', False)])
        else:
            ids = reserva_pool.search(cr, 1, [('imovel_id', '=', ids[0]), ('data_inicial', '!=', False), ('data_final', '=', False)])

        for reserva_obj in reserva_pool.browse(cr, uid, ids):

            imovel_obj = reserva_obj.imovel_id

            dias = hoje() - parse_datetime(reserva_obj.data_inicial).date()

            if dias.days > 3:
                reserva_obj.write({'data_final': hoje()})
                situacao = 'D'

                proxima_reseva_ids = reserva_pool.search(cr, 1, [('imovel_id', '=', reserva_obj.imovel_id.id), ('data_inicial', '=', False), ('data_final', '=', False)], limit=1, order='data_reserva')

                if len(proxima_reseva_ids) > 0:
                    reserva_pool.write(cr, uid, proxima_reseva_ids, {'data_inicial': hoje()})
                    situacao = 'R'

                imovel_obj.write({'situcao': situacao})

const_imovel()

class const_imovel_controle_chave(osv.Model):
    _name = 'const.imovel.controle.chave'
    _description = u'Controle de chaves do Imóvel'

    _columns = {
        'imovel_id': fields.many2one('const.imovel', u'Imóvel', on_delete='cascade'),
        'corretor_id': fields.many2one('res.partner', u'Corretor', ondelete='restrict'),
        'data_retirada': fields.datetime(u'Data Retirada'),
        'data_entrega': fields.datetime(u'Data Entrega'),
    }

    _defaults = {
       'data_retirada': fields.datetime.now,
    }


const_imovel_controle_chave()

