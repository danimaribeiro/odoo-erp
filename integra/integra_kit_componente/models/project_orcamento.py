# -*- coding: utf-8 -*-

from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class project_orcamento(osv.Model):
    _name = 'project.orcamento'
    _inherit = 'project.orcamento'

    _columns = {

    }

    def atualiza_valor_componentes(self, cr, uid, item_obj, dados, context={}):
        sql = """
        update project_orcamento_item set
            quantidade = coalesce(quantidade_componente, 0) * {quantidade},
            vr_produto = coalesce(vr_unitario, 0) * coalesce(quantidade_componente, 0) * {quantidade}

        where
            parent_id = {item_id};
        """
        sql = sql.format(item_id=item_obj.id, quantidade=item_obj.quantidade)
        cr.execute(sql)

    def ajusta_componentes(self, cr, uid, ids, dados, context={}):
        item_pool = self.pool.get('project.orcamento.item')

        for orcamento_obj in self.browse(cr, uid, ids):
            for item_obj in orcamento_obj.item_ids:
                if item_obj.parent_id or (not item_obj.product_id):
                    continue

                produto_obj = item_obj.product_id

                if len(item_obj.itens_componente_ids) <= 0:
                    if len(produto_obj.composicao_ids) > 0:
                        for composicao_obj in produto_obj.composicao_ids:
                            dados = {
                                'orcamento_id': orcamento_obj.id,
                                'parent_id': item_obj.id,
                                'product_id': composicao_obj.componente_id.id,
                                'uom_id': composicao_obj.uom_id.id,
                                'vr_unitario':  composicao_obj.vr_total,
                                'risco':  composicao_obj.risco,
                            }

                            if item_obj.etapa_id:
                                dados['etapa_id'] = item_obj.etapa_id.id

                            item_id = item_pool.create(cr, uid, dados)

                self.atualiza_valor_componentes(cr, uid, item_obj, dados, context)


            for item_obj in orcamento_obj.item_ids:
                if len(item_obj.itens_componente_ids) <= 0:
                    continue

                vr_item = D(item_obj.vr_produto).quantize(D('0.01'))
                vr_item_risco = D(item_obj.vr_risco).quantize(D('0.01'))
                vr_total = D(0)
                vr_total_risco = D(0)
                for componente_obj in item_obj.itens_componente_ids:
                    vr_total += D(componente_obj.vr_produto or 0)
                    vr_total_risco += D(componente_obj.vr_risco or 0)

                vr_total = vr_total.quantize(D('0.01'))
                vr_total_risco = vr_total_risco.quantize(D('0.01'))

                if vr_total != vr_item or vr_total_risco != vr_item_risco:
                    vr_unitario = vr_total / D(item_obj.quantidade or 1)

                    risco =  (vr_total_risco / vr_total * 100) - 100

                    item_obj.write({'vr_unitario': vr_unitario, 'vr_produto': vr_total, 'vr_risco':vr_total_risco, 'risco': risco })

    def create(self, cr, uid, dados, context={}):
        res = super(project_orcamento, self).create(cr, uid, dados, context=context)
        self.ajusta_componentes(cr, uid, [res], dados, context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(project_orcamento, self).write(cr, uid, ids, dados, context=context)
        self.ajusta_componentes(cr, uid, ids, dados, context=context)

        return res


project_orcamento()
