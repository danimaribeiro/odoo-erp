# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
from sped.models.fields import CampoDinheiro
from pybrasil.data import parse_datetime, hoje, dias_uteis, formata_data
from dateutil.relativedelta import relativedelta
from pybrasil.valor import formata_valor


class project_orcamento_item_planejamento(osv.Model):
    _name = 'project.orcamento.item.planejamento'
    _description = u'Planejamento de item do orçamento do projeto'
    _order = 'data_compra, data_inicial_execucao, data_final_execucao'
    _rec_name = 'descricao'

    def _get_data_compra(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for plan_obj in self.pool.get('project.orcamento.item.planejamento').browse(cr, uid, ids):
            data = parse_datetime(plan_obj.data_inicial_execucao or hoje()).date()
            dias = plan_obj.product_id.sale_delay or 7
            dias *= -1
            data += relativedelta(days=dias)

            res[plan_obj.id] = str(data)

        return res

    def _get_dias_execucao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for plan_obj in self.pool.get('project.orcamento.item.planejamento').browse(cr, uid, ids):
            du = []

            if plan_obj.data_inicial_execucao and plan_obj.data_final_execucao and plan_obj.item_id:
                du = dias_uteis(plan_obj.data_inicial_execucao, plan_obj.data_final_execucao, plan_obj.item_id.project_id.company_id.partner_id.estado or None, plan_obj.item_id.project_id.company_id.partner_id.cidade or None)

            res[plan_obj.id] = len(du)

        return res

    def _get_descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for plan_obj in self.pool.get('project.orcamento.item.planejamento').browse(cr, uid, ids):
            texto = plan_obj.product_id.name_template or ''
            texto += u' - etp.: ' + (plan_obj.etapa_id.nome_completo or '')
            texto += u' - orç.: ' + (plan_obj.orcamento_id.versao or '')
            texto += u' - compra: ' + formata_data(plan_obj.data_compra)
            texto += u' - qtd.: ' + formata_valor(plan_obj.quantidade)

            res[plan_obj.id] = texto

        return res

    _columns = {
        'descricao': fields.function(_get_descricao, type='char', string=u'Planejamento', store=True, select=True),

        'item_id': fields.many2one('project.orcamento.item', u'Item', ondelete='cascade'),

        'solicitacao_id': fields.related('item_id', 'solicitacao_id', type='many2one', relation='purchase.solicitacao.cotacao', string=u'Solicitação de materiais', store=True),
        'orcamento_id': fields.related('item_id', 'orcamento_id', type='many2one', relation='project.orcamento', string=u'Orçamento', store=True),
        'situacao': fields.related('orcamento_id', 'situacao', type='selection', string=u'Situação', store=True, select=True),
        'condicoes_ids': fields.one2many('project.orcamento.item.planejamento.parcela', 'planejamento_id', u'Condições de Pagamento'),
        'project_id': fields.related('item_id', 'project_id', type='many2one', relation='project.project', string=u'Projeto', store=True),
        'etapa_id': fields.related('item_id', 'etapa_id', type='many2one', relation='project.orcamento.etapa', string=u'Etapa', store=True),
        'codigo_completo': fields.related('item_id', 'codigo_completo', type='char', string=u'Código completo', store=False),
        'product_id': fields.related('item_id', 'product_id', type='many2one', relation='product.product', string=u'Produto/Serviço', store=True),
        #'uom_id': fields.related('product_id', 'uom_id', type='many2one', relation='product.uom', string=u'Unidade'),

        'data_inicial_execucao': fields.date(u'Data início execução', select=True),
        'data_final_execucao': fields.date(u'Data fim execução', select=True),
        'percentual': fields.float(u'Percentual', digits=(5,2)),
        'quantidade': fields.float(u'Quantidade', digits=(18, 2)),
        'vr_produto': fields.float(u'Valor', digits=(18,2)),

        'data_compra': fields.function(_get_data_compra, type='date', string=u'Data prevista da compra', store=True),
        'dias_execucao': fields.function(_get_dias_execucao, type='integer', string=u'Dias execução', store=True),
        'cotacao_ids': fields.one2many('purchase.cotacao.planejamento', 'planejamento_id', u'Cotações'),

        'data_compra_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De compra'),
        'data_compra_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A compra'),

    }

    def onchange_percentual_quantidade_vr_produto(self, cr, uid, ids, quantidade_original, vr_produto_original, percentual=0, quantidade=0, vr_produto=0, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        percentual = D(percentual or 0)
        quantidade = D(quantidade or 0)
        vr_produto = D(vr_produto or 0)

        if percentual:
            quantidade = D(quantidade_original or 0) * percentual / D(100)
            vr_produto = D(vr_produto_original or 0) * percentual / D(100)

        elif quantidade:
            percentual = quantidade / D(quantidade_original or 0) * D(100)
            vr_produto = D(vr_produto_original or 0) * percentual / D(100)

        elif vr_produto:
            percentual = vr_produto / D(vr_produto_original or 0) * D(100)
            quantidade = D(quantidade_original or 0) * percentual / D(100)

        valores['percentual'] = percentual
        valores['quantidade'] = quantidade
        valores['vr_produto'] = vr_produto

        return res

    def ajusta_percentual_item(self, cr, uid, ids, operacao='C'):
        itens = []

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for plan_obj in self.pool.get('project.orcamento.item.planejamento').browse(cr, uid, ids):
            if plan_obj.item_id.id not in itens:
                itens.append(plan_obj.item_id.id)

        item_pool = self.pool.get('project.orcamento.item')

        for item_obj in item_pool.browse(cr, uid, itens):
            total_planejado = D(0)

            for plan_obj in item_obj.planejamento_ids:
                if operacao == 'U' and plan_obj.id in ids:
                    continue

                total_planejado += D(plan_obj.percentual or 0)

            sql = 'update project_orcamento_item set percentual_planejado = {total_planejado} where id = {id};'
            sql = sql.format(total_planejado=total_planejado, id=item_obj.id)
            cr.execute(sql)

    def gerar_parcelas(self, cr, uid, ids, operacao='C'):
        itens = []

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for plan_obj in self.pool.get('project.orcamento.item.planejamento').browse(cr, uid, ids):
            if plan_obj.item_id.id not in itens:
                itens.append(plan_obj.item_id.id)

        item_pool = self.pool.get('project.orcamento.item')

        for item_obj in item_pool.browse(cr, uid, itens):

            for plan_obj in item_obj.planejamento_ids:

                if operacao == 'U' and plan_obj.id in ids:
                    continue

                if not item_obj.product_id.payment_term_id:
                    return


                payment_term_obj = item_obj.product_id.payment_term_id
                condicoes_objs = plan_obj.condicoes_ids

                vr_produto = plan_obj.vr_produto
                data_emissao = plan_obj.data_compra


                lista_vencimentos = payment_term_obj.compute(vr_produto, date_ref=data_emissao)
                if lista_vencimentos:

                    if len(condicoes_objs) > 0:
                        for condicao in condicoes_objs:
                            condicao.unlink()

                    condicao_obj = self.pool.get('project.orcamento.item.planejamento.parcela')
                    parcela = 1
                    for data, valor in lista_vencimentos:
                        dados = {
                            'planejamento_id': plan_obj.id,
                            'numero': str(parcela),
                            'data_vencimento': data,
                            'valor': valor
                        }
                        condicao_obj.create(cr, uid, dados)
                        parcela += 1


        return

    def create(self, cr, uid, dados, context={}):
        res = super(project_orcamento_item_planejamento, self).create(cr, uid, dados, context)
        
        for item_planejamento_obj in self.pool.get('project.orcamento.item.planejamento').browse(cr, uid, [res]):

            if item_planejamento_obj.item_id:   
                self.pool.get('project.orcamento.item.planejamento').ajusta_percentual_item(cr, uid, [res], 'C')
                self.pool.get('project.orcamento.item.planejamento').gerar_parcelas(cr, uid, [res], 'C')


        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(project_orcamento_item_planejamento, self).write(cr, uid, ids, dados, context)

        print(self, ids)
        
        for item_planejamento_obj in self.pool.get('project.orcamento.item.planejamento').browse(cr, uid, ids):
            
            if item_planejamento_obj.item_id and not item_planejamento_obj.etapa_id: 
                self.pool.get('project.orcamento.item.planejamento').ajusta_percentual_item(cr, uid, ids, 'W')
                self.pool.get('project.orcamento.item.planejamento').gerar_parcelas(cr, uid, ids, 'W')

        return res

    def unlink(self, cr, uid, ids, context={}):
        self.pool.get('project.orcamento.item.planejamento').ajusta_percentual_item(cr, uid, ids, 'U')
        self.pool.get('project.orcamento.item.planejamento').gerar_parcelas(cr, uid, ids, 'U')

        res = super(project_orcamento_item_planejamento, self).unlink(cr, uid, ids, context)

        return res
    
    def copy(self, cr, uid, ids, dados, context={}):
        #dados['cotacao_ids'] = False

        return super(project_orcamento_item_planejamento, self).copy(cr, uid, ids, dados, context)


project_orcamento_item_planejamento()


class project_orcamento_item(osv.Model):
    _inherit = 'project.orcamento.item'

    def _get_periodo_execucao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for item_obj in self.pool.get('project.orcamento.item').browse(cr, uid, ids):
            sql = """
                select
                    min(data_inicial_execucao),
                    max(data_final_execucao)
                from
                    project_orcamento_item_planejamento
                where
                    item_id = {item_id};
            """
            sql = sql.format(item_id=item_obj.id)
            cr.execute(sql)
            dados = cr.fetchall()

            data_inicial = False
            data_final = False
            dias = 0

            if len(dados) and dados[0]:
                print(dados)
                data_inicial = parse_datetime(dados[0][0])
                data_final = parse_datetime(dados[0][1])

                if data_inicial and data_final:
                    du = dias_uteis(data_inicial, data_final, item_obj.project_id.company_id.partner_id.estado or None, item_obj.project_id.company_id.partner_id.cidade or None)
                    dias = len(du)

            if nome_campo == 'data_inicial_execucao':
                if data_inicial:
                    res[item_obj.id] = str(data_inicial)
                else:
                    res[item_obj.id] =  False
            elif nome_campo == 'data_final_execucao':
                if data_final:
                    res[item_obj.id] = str(data_final)
                else:
                    res[item_obj.id] =  False
            else:
                res[item_obj.id] = dias

        return res

    _columns = {
        'planejamento_ids': fields.one2many('project.orcamento.item.planejamento', 'item_id', u'Planejamento'),
        'percentual_planejado': fields.float(u'Percentual planejado', digits=(5,2)),
        'dias_execucao': fields.function(_get_periodo_execucao, type='integer', string=u'Dias execução', store=True),
        'data_inicial_execucao': fields.function(_get_periodo_execucao, type='date', string=u'Data início execução', store=True, select=True),
        'data_final_execucao': fields.function(_get_periodo_execucao, type='date', string=u'Data fim execução', store=True, select=True),
        'data_compra_solicitacao': fields.date(u'Data da compra'),
    }

    def cria_planejamento_solicitacao(self, cr, uid, ids, data_aprovacao=None):
        planejamento_pool = self.pool.get('project.orcamento.item.planejamento')

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for item_obj in self.pool.get('project.orcamento.item').browse(cr, uid, ids):
            if (not item_obj.data_compra_solicitacao) and (not data_aprovacao):
                continue

            if item_obj.data_compra_solicitacao:
                data_execucao = parse_datetime(item_obj.data_compra_solicitacao).date()
            else:
                data_execucao = parse_datetime(data_aprovacao)
                
            dias = item_obj.product_id.sale_delay or 7
            data_execucao += relativedelta(days=dias)

            dados = {
                'item_id': item_obj.id,
                'quantidade': item_obj.quantidade,
                'percentual': 100,
                'data_inicial_execucao': str(data_execucao)[:10],
                'data_final_execucao': str(data_execucao)[:10],
            }

            if len(item_obj.planejamento_ids):
                plan_id = item_obj.planejamento_ids[0].id
                planejamento_pool.write(cr, uid, plan_id, dados)
            else:
                planejamento_pool.create(cr, uid, dados)

    def create(self, cr, uid, dados, context={}):
        res = super(project_orcamento_item, self).create(cr, uid, dados, context=context)

        self.pool.get('project.orcamento.item').cria_planejamento_solicitacao(cr, uid, res)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(project_orcamento_item, self).write(cr, uid, ids, dados, context=context)

        #self.pool.get('project.orcamento.item').cria_planejamento_solicitacao(cr, uid, ids)

        return res

    #def copy(self, cr, uid, ids, dados, context={}):
    #    dados['planejamento_ids'] = False

    #    return super(project_orcamento, self).copy(cr, uid, ids, dados, context)


project_orcamento_item()


class project_orcamento_item_planejamento_parcela(osv.Model):
    _description = u'Condição de Pagamneto do Item'
    _name = 'project.orcamento.item.planejamento.parcela'


    _columns = {
        'planejamento_id': fields.many2one('project.orcamento.item.planejamento', u'Item do Planejamento', ondelete='cascade'),
        'numero': fields.char(u'Número da duplicata/parcela', size=60, select=True),
        'data_vencimento': fields.date(u'Data de vencimento', select=True),
        'valor': CampoDinheiro(u'Valor da duplicata/parcela'),
    }

    _defaults = {
        'valor': D('0'),
    }


project_orcamento_item_planejamento_parcela()
