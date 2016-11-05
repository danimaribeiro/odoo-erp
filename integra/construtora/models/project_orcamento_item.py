# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime
from dateutil.relativedelta import relativedelta
from pybrasil.valor import formata_valor


STORE_ETAPA = {
    'project.orcamento': (
        lambda orcamento_pool, cr, uid, ids, context={}:
        ids,
        ['situacao'],
        10  #  Prioridade
    ),
}

ULTIMA_ORDEM = 0


class project_orcamento_item(osv.Model):
    _name = 'project.orcamento.item'
    _description = u'Item do orçamento do projeto'
    _order = 'orcamento_id, codigo_completo'
    _rec_name = 'descricao'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'codigo_completo'


    def monta_codigo(self, cr, uid, id):
        item_obj = self.browse(cr, uid, id)

        if item_obj.parent_id:
            filtro = {
                'orcamento_id': item_obj.parent_id.orcamento_id.id,
                'etapa_id': item_obj.parent_id.etapa_id.id or 'null',
            }

        else:
            filtro = {
                'orcamento_id': item_obj.orcamento_id.id,
                'etapa_id': item_obj.etapa_id.id or 'null',
            }

        #
        # Determina o tamanho máximo dos itens vinculados a essa etapa
        #
        sql = """
            select
                max(poi.ordem)

            from
                project_orcamento_item poi

            where
                poi.orcamento_id = {orcamento_id}
                and poi.etapa_id = {etapa_id};
        """
        sql = sql.format(**filtro)
        cr.execute(sql)
        tms = cr.fetchall()[0][0] or 1
        tamanho_maximo = len(str(tms))

        #
        # Determina o código desse item, baseado na etapa, ordem do item, e descrição
        #
        sql = """
            select
                poi.id

            from
                project_orcamento_item poi
                join product_product p on p.id = poi.product_id

            where
                poi.orcamento_id = {orcamento_id}
                and poi.etapa_id = {etapa_id}

            order by
                poi.orcamento_id,
                poi.etapa_id,
                poi.ordem,
                p.name_template;
        """
        sql = sql.format(**filtro)
        cr.execute(sql)
        item_ids = cr.fetchall()
        print(item_ids, item_obj.id)

        codigo = 1
        for item_id, in item_ids:
            if item_id == item_obj.id:
                break

            codigo += 1

        if item_obj.etapa_id:
            codigo = item_obj.etapa_id.codigo_completo + '.' + str(codigo).zfill(tamanho_maximo)
        else:
            codigo = str(codigo).zfill(tamanho_maximo)

        return codigo

    def get_codigo(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for id in ids:
            res += [(id, self.monta_codigo(cr, uid, id))]

        return res

    def _get_codigo_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_codigo(cr, uid, ids, context=context)
        return dict(res)

    def get_descricao(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            texto = u''

            texto += item_obj.product_id.name or u''
            texto += u'; '
            texto += formata_valor(item_obj.quantidade or 0)
            texto += u'; '
            texto += item_obj.project_id.name or u''
            texto += u'; '
            texto += item_obj.orcamento_id.versao or u''

            res[item_obj.id] = texto

        return res

    def _qtd_componentes(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            res[item_obj.id] = len(item_obj.itens_componente_ids)

        return res

    _columns = {
        'solicitacao_id': fields.many2one('purchase.solicitacao.cotacao', u'Solicitação de materiais', ondelete='restrict'),
        'orcamento_id': fields.many2one('project.orcamento', u'Orçamento', ondelete='cascade'),
        'orcamento_aprovado': fields.related('solicitacao_id', 'aprovador_id', type='integer', string=u'Aprovado solicitacao', store=True, select=True),
        'situacao': fields.related('orcamento_id', 'situacao', type='selection', string=u'Situação', store=STORE_ETAPA, select=True),
        'project_id': fields.many2one('project.project', u'Projeto'),
        'etapa_id': fields.many2one('project.orcamento.etapa', u'Etapa', ondelete='restrict'),
        'codigo_completo': fields.function(_get_codigo_funcao, type='char', string=u'Código completo', store=True, select=True),
        'descricao': fields.function(get_descricao, type='char', string=u'Item orçado', store=True, select=True, size=255),
        'ordem': fields.integer(u'Ordem', select=True),
        'product_id': fields.many2one('product.product', u'Produto/Serviço', ondelete='restrict'),
        'uom_id': fields.related('product_id', 'uom_id', type='many2one', relation='product.uom', string=u'Unidade'),
        'quantidade': fields.float(u'Quantidade', digits=(18, 2)),
        'vr_unitario': fields.float(u'Unitário', digits=(18,2)),
        'vr_produto': fields.float(u'Valor', digits=(18,2)),
        'risco': fields.float(u'Risco %%', digits=(18,2)),
        'quantidade_risco': fields.float(u'Quantidade risco', digits=(18,2)),
        'vr_risco': fields.float(u'Valor risco', digits=(18,2)),

        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo/modelo de rateio'),
        'rateio_ids': fields.one2many('finan.rateio', 'project_orcamento_item_id', u'Modelo de rateio'),

        'parent_id': fields.many2one('project.orcamento.item', u'Componente de'),
        'parent_left': fields.integer(u'Conta à esquerda', select=1),
        'parent_right': fields.integer(u'Conta a direita', select=1),

        'itens_componente_ids': fields.one2many('project.orcamento.item', 'parent_id', u'Componentes'),
        'qtd_componentes': fields.function(_qtd_componentes, type='float', string=u'Qtde. componentes', store=True),
    }

    def _ajusta_ordem(self, cr, uid, context={}):
        global ULTIMA_ORDEM

        if ULTIMA_ORDEM == 0:
            ULTIMA_ORDEM = 90

        ULTIMA_ORDEM += 10

        return ULTIMA_ORDEM

    _defaults = {
        'ordem': _ajusta_ordem,
    }

    def onchange_product_id(self, cr, uid, ids, product_id, project_id):
        if not product_id or not project_id:
            return {}

        project_obj = self.pool.get('project.project').browse(cr, uid, project_id)
        produto_obj = self.pool.get('product.product').browse(cr, uid, product_id, context={'company_id': project_obj.company_id.id})

        custo = D(0)
        if produto_obj.custo_ultima_compra:
            custo += D(produto_obj.custo_ultima_compra)

        res = {
            'value': {
                'uom_id': produto_obj.uom_id.id,
                'vr_unitario': D(custo),
            }
        }

        return res

    def onchange_quantidade_vr_unitario(self, cr, uid, ids, quantidade, vr_unitario, risco):
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

        vr_produto = quantidade * vr_unitario
        vr_produto = vr_produto.quantize(D('0.01'))
        vr_risco = vr_produto * risco / D('100')
        vr_risco = vr_risco.quantize(D('0.01'))
        vr_risco += vr_produto
        quantidade_risco = quantidade * risco / D('100')
        quantidade_risco = quantidade_risco.quantize(D('0.01'))
        quantidade_risco += quantidade
        res = {
            'value': {
                'vr_produto': vr_produto,
                'vr_risco': vr_risco,
                'quantidade_risco': quantidade_risco,
                'vr_unitario_risco': vr_risco / (quantidade or 1)
            }
        }

        return res

    #def copy(self, cr, uid, ids, dados, context={}):
    #    dados['planeja'] = False
    #    dados['solicitacao_id'] = False
    #    dados['data_compra_solicitacao'] = False
    #    dados['percentual_planejado'] = False
    #    dados['planejamento_ids'] = False


    #    return super(project_orcamento, self).copy(cr, uid, ids, dados, context)

    #def onchange_centrocusto_id(self, cr, uid, ids, centrocusto_id, valor_documento, valor, project_id, company_id, context={}):
        #valores = {}
        #res = {'value': valores}

        #if not context:
            #context = {}

        #valor_documento = valor_documento or 0
        #valor = valor or 0

        #print('passou aqui', centrocusto_id, valor_documento, valor)

        #if centrocusto_id:
            #centrocusto_obj = self.pool.get('finan.centrocusto').browse(cr, uid, centrocusto_id)

            ##
            ## Define os valores padrão para o rateio
            ## outros valores podem vir do contexto
            ##
            #padrao = {
                #'company_id': company_id,
                #'project_id': project_id,
                #'centrocusto_id': centrocusto_id,
            #}
            #rateio = {}
            #rateio = self.pool.get('finan.centrocusto').realiza_rateio(cr, uid, [centrocusto_id], context=context, rateio=rateio, padrao=padrao, valor=valor_documento)

            #campos = self.pool.get('finan.centrocusto').campos_rateio(cr, uid)

            #dados = []
            #self.pool.get('finan.centrocusto').monta_dados(rateio, campos=campos, lista_dados=dados, valor=valor_documento)
            #valores['rateio_ids'] = dados

        ##
        ## Força a geração de pelo menos 1 registro para a conta financeira
        ##
        #elif conta_id:
            #rateio_ids = []
            #valores['rateio_ids'] = rateio_ids

            #dados = {
                #'company_id': company_id,
                #'centrocusto_id': False,
                #'porcentagem': 100,
                #'valor_documento': valor_documento,
                #'valor': valor,
                #'project_id': project_id,
            #}

            #rateio_ids.append([0, False, dados])

        #return res

    def realiza_rateio(self, cr, uid, ids, padrao={}, rateio={}, context={}):
        if not ids:
            return D(0)

        cc_pool = self.pool.get('finan.centrocusto')
        campos = cc_pool.campos_rateio(cr, uid)

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        total = D(0)
        for item_obj in self.browse(cr, uid, ids):
            p = copy(padrao)
            p['company_id'] = item_obj.project_id.company_id.id
            p['project_id'] = item_obj.project_id.id
            produto_obj = item_obj.product_id

            if getattr(item_obj.product_id, 'conta_despesa_id', False):
                conta_entrada_obj = item_obj.product_id.conta_despesa_id
            elif getattr(item_obj.product_id, 'account_despesa_id', False):
                conta_entrada_obj = item_obj.product_id.account_despesa_id.finan_conta_id
            else:
                conta_entrada_obj = item_obj.documento_id.finan_conta_id

            conta_id = [
                'tipo_conta',
                {
                    'D': conta_entrada_obj.id,
                    'C': conta_entrada_obj.id,
                    False: conta_entrada_obj.id,
                }
            ]

            p['conta_id'] = conta_id
            valor = D(item_obj.vr_produtos)

            if valor <= 0:
                continue

            total += valor

            if item_obj.rateio_ids:
                cc_pool.realiza_rateio(cr, uid, [item_obj.id], valor=valor, padrao=p, rateio=rateio, context=context, tabela_pool=self.pool.get('sped.documentoitem'))

            elif item_obj.centrocusto_id:
                cc_pool.realiza_rateio(cr, uid, [item_obj.finan_centrocusto_id.id], valor=valor, padrao=p, rateio=rateio, context=context)

            else:
                cc_pool._realiza_rateio(valor, 100, campos, p, rateio)

        return total


project_orcamento_item()
