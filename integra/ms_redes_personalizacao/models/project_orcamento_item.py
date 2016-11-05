# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime
from dateutil.relativedelta import relativedelta



class project_orcamento_item(osv.Model):
    _name = 'project.orcamento.item'
    _inherit = 'project.orcamento.item'

    def _vr_unitario_risco(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids, context=context):
            valor = D(item_obj.vr_risco or 0)
            quantidade = D(item_obj.quantidade or 1)

            res[item_obj.id] = valor / quantidade

        return res

    _columns = {
        'replicado_planejamento': fields.boolean(u'Replicado o planejamento?'),
        'task_id': fields.many2one('project.task', u'Tarefa'),
        'quantidade_referencia': fields.float(u'Quantidade'),

        #'vr_unitario_risco': fields.function(_vr_unitario_risco, type='float', string=u'Unitário com margem', digits=(18,2), store=True),
        'vr_unitario_risco': fields.float(u'Unitário com margem', digits=(18,2)),
        'vr_risco': fields.float(u'Valor com margem', digits=(18,2)),
        'sale_item_id': fields.many2one('sale.order.line', u'Item do Pedido Venda'),       
    }

    _defaults = {
        'quantidade_referencia': 1,
    }

    def replica_planejamento_etapa(self, cr, uid, ids, context={}):
        plan_pool = self.pool.get('project.orcamento.item.planejamento')

        for item_obj in self.browse(cr, uid, ids):
            if not len(item_obj.planejamento_ids):
                continue

            orcamento_obj = item_obj.orcamento_id

            for item_etapa_obj in orcamento_obj.item_ids:
                if item_etapa_obj.id == item_obj.id:
                    continue

                if not (item_obj.etapa_id and item_etapa_obj.etapa_id and \
                    item_obj.etapa_id.id == item_etapa_obj.etapa_id.id):
                    continue

                #
                # Vamos agora copiar cada planejamento
                #
                for plan_obj in item_obj.planejamento_ids:
                    dados = {
                        'item_id': item_etapa_obj.id,
                        'data_inicial_execucao': plan_obj.data_inicial_execucao,
                        'data_final_execucao': plan_obj.data_final_execucao,
                        'percentual': plan_obj.percentual,
                        'replicado_planejamento': True,
                    }

                    ajuste = plan_pool.onchange_percentual_quantidade_vr_produto(cr, uid, False, item_etapa_obj.quantidade, item_etapa_obj.vr_unitario, plan_obj.percentual, 0, 0, context)

                    dados.update(ajuste['value'])
                    plan_pool.create(cr, uid, dados)

            item_obj.write({'replicado_planejamento': True})

    def gera_task(self, cr, uid, ids, context={}):
        task_pool = self.pool.get('project.task')

        for item_obj in self.browse(cr, uid, ids):
            if item_obj.product_id:
                dados = {
                    'orcamento_item_id': item_obj.id,
                    'name': item_obj.product_id.name,
                }

                orcamento_obj = item_obj.orcamento_id

                if orcamento_obj.project_id:
                    dados['project_id'] = orcamento_obj.project_id.id

                task_id = task_pool.create(cr, uid, dados)

                item_obj.write({'task_id': task_id})

    def onchange_quantidade_vr_unitario_risco(self, cr, uid, ids, quantidade, vr_unitario, risco, vr_unitario_risco):
        if not quantidade:
            quantidade = D('0')
        else:
            quantidade = D(quantidade)

        if not vr_unitario:
            vr_unitario = D('0')
        else:
            vr_unitario = D(vr_unitario)

        if not risco:
            risco = D('0')
        else:
            risco = D(risco)

        if not vr_unitario_risco:
            vr_unitario_risco = D(0)
        else:
            vr_unitario_risco = D(vr_unitario_risco)

        vr_produto = quantidade * vr_unitario
        vr_produto = vr_produto.quantize(D('0.01'))


        if risco != 0:
            vr_risco = vr_produto * risco / D('100')
            vr_risco = vr_risco.quantize(D('0.01'))
            vr_risco += vr_produto
            quantidade_risco = quantidade * risco / D('100')
            quantidade_risco = quantidade_risco.quantize(D('0.01'))
            quantidade_risco += quantidade
            vr_unitario_risco = vr_risco / (quantidade or 1)
        else:
            vr_risco = vr_unitario_risco * quantidade
            vr_risco = vr_risco.quantize(D('0.01'))

            risco = vr_unitario_risco / (vr_unitario or 1)
            risco -= 1
            risco *= 100

            quantidade_risco = quantidade * risco / D('100')
            quantidade_risco = quantidade_risco.quantize(D('0.01'))
            quantidade_risco += quantidade

        res = {
            'value': {
                'vr_produto': vr_produto,
                'vr_risco': vr_risco,
                'quantidade_risco': quantidade_risco,
                'vr_unitario_risco': vr_unitario_risco,
                'risco': risco,
            }
        }

        return res

    #def create(self, cr, uid, dados, context={}):
    #    res = super(project_orcamento_item, self).create(cr, uid, dados, context=context)

    #    for item_obj in self.pool.get('project.orcamento.item').browse(cr, uid, [res]):

    #        if item_obj.etapa_id:
    #            etapa_obj = item_obj.etapa_id

    #            for planejamento_obj in etapa_obj.planejamento_ids:
    #                self.pool.get('project.orcamento.item.planejamento').copy(cr, uid, planejamento_obj.id, {'item_id': item_obj.id, 'etapa_id': False, 'cotacao_ids': False})

    #    return res

    #def write(self, cr, uid, ids, dados, context={}):
    #    res = super(project_orcamento_item, self).write(cr, uid, ids, dados, context)

    #    for item_obj in self.pool.get('project.orcamento.item').browse(cr, uid, ids):

    #        if item_obj.etapa_id and len(item_obj.planejamento_ids) == 0:
    #            etapa_obj = item_obj.etapa_id

    #            for planejamento_obj in etapa_obj.planejamento_ids:
    #                self.pool.get('project.orcamento.item.planejamento').copy(cr, uid, planejamento_obj.id, {'item_id': item_obj.id, 'etapa_id': False})

    #    return res


project_orcamento_item()
