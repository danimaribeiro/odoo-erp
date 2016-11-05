# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
import os
import base64
from finan.wizard.finan_relatorio import Report


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

SITUACAO = [
    ('A', u'Aberto'),
    ('P', u'Andamento'),
    ('F', u'Finalizada'),
]

class project_orcamento_medicao(osv.Model):
    _name = 'project.orcamento.medicao'
    _description = u'Projeto Medição'
    _rec_name = 'data'
    _order = 'id desc'

    _columns = {
        'state': fields.selection(SITUACAO, u'Situação', select=True),
        'orcamento_id': fields.many2one('project.orcamento', u'Orçamento', ondelete='restrict'),
        'data': fields.date(u'Data'),
        'etapa_id': fields.many2one('project.orcamento.etapa', u'Etapa'),
        'item_ids': fields.one2many('project.orcamento.medicao.item', 'medicao_id', u'Itens do Orçamento Medição', domain=[('parent_id', '=', False)]),
    }

    _defaults = {
        'data': fields.datetime.now,
        'state': 'A',
    }    
        
    def write(self, cr, uid, ids, dados, context={}):
        
        for medicao_obj in self.browse(cr, uid, ids):
            
            if medicao_obj.state == 'F':
                raise osv.except_osv(u'Erro!', u'Mediação ja Finalizada!')
                                        
            res = super(project_orcamento_medicao, self).write(cr, uid, ids, dados, context=context)
        
        return res    

    def buscar_itens(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('project.orcamento.medicao.item')

        medicao_obj = self.browse(cr, uid, ids[0])
        
        if medicao_obj.state == 'F':
            raise osv.except_osv(u'Erro!', u'Mediação ja Finalizada!')

        for item_obj in medicao_obj.item_ids:
            item_obj.unlink()

        orcamento_obj = medicao_obj.orcamento_id

        for item_obj in orcamento_obj.item_ids:
            if item_obj.parent_id:
                continue

            dados = {
                'medicao_id': medicao_obj.id,
                'orcamento_item_id': item_obj.id,
                'data': medicao_obj.data,
            }
            item_id = item_pool.create(cr, uid, dados)

            if hasattr(item_obj, 'itens_componente_ids') and getattr(item_obj, 'itens_componente_ids', False):
                for item_componente_obj in item_obj.itens_componente_ids:
                    dados = {
                        'medicao_id': medicao_obj.id,
                        'orcamento_item_id': item_componente_obj.id,
                        'data': medicao_obj.data,
                        'parent_id': item_id,
                    }
                    item_pool.create(cr, uid, dados)

                item_pool.write(cr, uid, [item_id], {'qtd_componentes': item_obj.qtd_componentes})
                
        medicao_obj.write({'state': 'P'})

        return True

    def ajusta_componentes(self, cr, uid, ids, context={}):
        for medicao_obj in self.browse(cr, uid, ids, context=context):
            for item_obj in medicao_obj.item_ids:
                if len(item_obj.itens_componente_ids) == 0:
                    continue

                sql = """
                update project_orcamento_medicao pom set
                where
                    pom.id = {id};
                """

    def finalizar(self, cr, uid, ids, context={}):
        if not ids:
            return {}
        
        medicao_obj = self.browse(cr, uid, ids[0])
        medicao_obj.write({'state': 'F'})
        
        return True


project_orcamento_medicao()
