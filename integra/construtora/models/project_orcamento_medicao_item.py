# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class project_orcamento_medicao_item(osv.Model):
    _name = 'project.orcamento.medicao.item'
    _description = u'Orçamento do Projeto Medição Item'
    _rec_name = 'orcamento_item_id'

    def _get_planejada(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            soma = D('0')

            if item_obj.orcamento_item_id:
                orcamento_item_obj = item_obj.orcamento_item_id

                for planejamento_obj in orcamento_item_obj.planejamento_ids:
                    soma += planejamento_obj.quantidade

            soma = soma.quantize(D('0.01'))

            res[item_obj.id] = soma

        return res

    def _get_acumulada(self, cr, uid, ids, nome_campo, args, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            soma = D('0')

            if nome_campo == 'quantidade_acumulada':
                sql = """
                    select
                        coalesce(sum(pm.quantidade_medida),0) as quantidade

                    from
                        project_orcamento_medicao m
                        join project_orcamento_medicao_item pm on pm.medicao_id = m.id
                    where
                        pm.orcamento_item_id = {orcamento_item_id}
                        and m.data <= '{data}';
                """
            else:
                sql = """
                    select
                        coalesce(sum(pm.vr_produto_medido),0) as vr_produto

                    from
                        project_orcamento_medicao m
                        join project_orcamento_medicao_item pm on pm.medicao_id = m.id
                    where
                        pm.orcamento_item_id = {orcamento_item_id}
                        and m.data <= '{data}';
                """

            sql = sql.format(data=item_obj.data,orcamento_item_id=item_obj.orcamento_item_id.id)
            cr.execute(sql)
            dados = cr.fetchall()

            for valor in dados:
                soma += valor[0]

            soma = soma.quantize(D('0.01'))

            res[item_obj.id] = soma

        return res

    def _qtd_componentes(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            res[item_obj.id] = len(item_obj.itens_componente_ids)

        return res

    _columns = {
        'medicao_id': fields.many2one('project.orcamento.medicao', u'Projeto Medição', ondelete='cascade'),
        'data': fields.related('medicao_id', 'data',  type='date', string=u'Data', store=True),
        'orcamento_item_id': fields.many2one('project.orcamento.item', u'Itens do Orçamento'),
        'codigo_completo': fields.related('orcamento_item_id','codigo_completo',  type='char', string=u'Código completo', store=True),
        'product_id': fields.related('orcamento_item_id', 'product_id', type='many2one', relation='product.product', string=u'Produto/Serviço', store=True),
        'uom_id': fields.related('orcamento_item_id', 'uom_id', type='many2one', relation='product.uom', string=u'Unidade', store=True),
        'uom_id': fields.related('orcamento_item_id', 'uom_id', type='many2one', relation='product.uom', string=u'Unidade', store=True),
        'etapa_id': fields.related('orcamento_item_id', 'etapa_id', type='many2one', relation='project.orcamento.etapa', string=u'Etapa', store=True),
        'quantidade': fields.related('orcamento_item_id','quantidade',  type='float', string=u'Quantidade', store=True),
        'quantidade_planejada': fields.function(_get_planejada, type='float', string=u'Quantidade Planejada', store=True, digits=(18, 2)),
        'quantidade_medida': fields.float(u'Quantidade Medida'),
        'quantidade_acumulada': fields.function(_get_acumulada, type='float', string=u'Quantidade acum.', store=True, digits=(18, 2)),
        'quantidade_percentual': fields.float(u'% Medido'),
        'vr_unitario': fields.related('orcamento_item_id', 'vr_unitario',  type='float', string=u'Unitário', store=True),
        'vr_produto': fields.related('orcamento_item_id', 'vr_produto',  type='float', string=u'Valor', store=True),
        #'vr_unitario_planejado': fields.function(_get_planejada, type='float', string=u'Unitário planejado', store=True, digits=(18, 2)),
        'vr_unitario_medido': fields.float(u'Unitário medido'),
        'vr_produto_medido': fields.float(u'Valor medido'),
        'vr_produto_percentual': fields.float(u'% Medido'),
        'vr_produto_acumulado': fields.function(_get_acumulada, type='float', string=u'Valor acum.', store=True, digits=(18, 2)),

        'parent_id': fields.many2one('project.orcamento.medicao.item', u'Componente de'),
        'parent_left': fields.integer(u'Conta à esquerda', select=1),
        'parent_right': fields.integer(u'Conta a direita', select=1),

        'itens_componente_ids': fields.one2many('project.orcamento.medicao.item', 'parent_id', u'Componentes'),
        'qtd_componentes': fields.function(_qtd_componentes, type='float', string=u'Qtde. componentes', store=True),
    }

    def onchange_quantidade_medida(self, cr, uid, ids, quantidade, quantidade_medida=0, quantidade_percentual=0, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        quantidade = D(quantidade or 0)
        quantidade_medida = D(quantidade_medida or 0)
        quantidade_percentual = D(quantidade_percentual or 0)

        if quantidade_percentual:
            quantidade_medida = D(quantidade or 0) * quantidade_percentual / D(100)
            valores['quantidade_medida'] = quantidade_medida

        else:
            quantidade_percentual = quantidade_medida / D(quantidade or 0) * D(100)
            valores['quantidade_percentual'] = quantidade_percentual

        return res

    def onchange_vr_produto_medido(self, cr, uid, ids, quantidade_medida, vr_produto, vr_unitario_medido=0, vr_produto_medido=0, vr_produto_percentual=0, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        quantidade_medida = D(quantidade_medida or 0)
        vr_produto = D(vr_produto or 0)
        vr_unitario_medido = D(vr_unitario_medido or 0)
        vr_produto_medido = D(vr_produto_medido or 0)
        vr_produto_percentual = D(vr_produto_percentual or 0)

        if vr_produto_percentual:
            vr_produto_medido = vr_produto * vr_produto_percentual / D(100)
            valores['vr_produto_medido'] = vr_produto_medido
            valores['vr_unitario_medido'] = vr_produto_medido / (quantidade_medida or 1)

        elif vr_unitario_medido:
            vr_produto_medido = vr_unitario_medido * quantidade_medida
            vr_produto_percentual = vr_produto_medido / (vr_produto or 1) * 100
            valores['vr_produto_medido'] = vr_produto_medido
            valores['vr_produto_percentual'] = vr_produto_percentual

        else:
            vr_unitario_medido = vr_produto_medido / (quantidade_medida or 1)
            vr_produto_percentual = vr_produto_medido / (vr_produto or 1) * 100
            valores['vr_unitario_medido'] = vr_produto_medido
            valores['vr_produto_percentual'] = vr_produto_percentual

        return res


project_orcamento_medicao_item()
