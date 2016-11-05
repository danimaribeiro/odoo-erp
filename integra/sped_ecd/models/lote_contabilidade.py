# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.data import parse_datetime, formata_data, agora, hoje, mes_passado, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.valor import formata_valor
from pybrasil.telefone.telefone import separa_fone
from integra_questor.models.integracao_questor import integracao_questor, integracao_questor_fiscal_A, integracao_questor_fiscal_B, integracao_questor_fiscal_C, integracao_questor_fiscal_D, integracao_questor_fiscal_E, integracao_questor_fiscal_F, integracao_questor_fiscal_G, integracao_questor_fiscal_H, integracao_questor_fiscal_J, integracao_questor_fiscal_K, integracao_questor_fiscal_KI, integracao_questor_fiscal_L, integracao_questor_fiscal_L, integracao_questor_fiscal_M, integracao_questor_fiscal_N, integracao_questor_fiscal_O, integracao_questor_fiscal_R
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes
import base64
import os
from finan.wizard.finan_relatorio import Report
from pybrasil.inscricao import limpa_formatacao
from sped.constante_tributaria import *
from pybrasil.base import DicionarioBrasil
from finan.wizard.relatorio import *
from pybrasil.valor.decimal import Decimal as D

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


TIPO_LOTE = [
    ('D', u'Documentos Fiscais'),
    ('F', u'Financeiro'),
    ('FG', u'Folha de Pagamento'),
    ('PF', u'Provisão de Férias'),
    ('PD', u'Provisão de 13º'),
    ('PT', u'Patrimonio'),
    #('G', u'Geral'),
]


class lote_contabilidade(osv.Model):
    _description = u'Lote Contabilidade'
    _name = 'lote.contabilidade'
    _rec_name = 'nome'
    _order = 'codigo desc'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for exp_obj in self.browse(cr, uid, ids):
            res[exp_obj.id] = exp_obj.id

        return res

    def _nome(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for exp_obj in self.browse(cr, uid, ids):
            res[exp_obj.id] = str(exp_obj.id)

        return res

    _columns = {
        'tipo': fields.selection(TIPO_LOTE, u'Tipo'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=True, select=True),
        'nome': fields.function(_nome, type='char', string=u'Nome', store=True, select=True),
        'emissao': fields.selection(TIPO_EMISSAO_TODAS, u'Tipo de emissão'),
        'diario_conta_id': fields.many2one('finan.conta', u'Conta Contábil'),
        'nome_diario': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo_diario': fields.binary(u'Arquivo', readonly=True),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'importado': fields.boolean(u'Importado?'),
        'gerar_rateio': fields.boolean(u'Gerar com Rateio?'),
        'somente_cnpj': fields.boolean(u'Somente CNPJ'),
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),
        'write_date': fields.datetime( u'Data Alteração'),
        'plano_id': fields.many2one('ecd.plano.conta', u'Plano de Conta'),
        'data': fields.datetime(u'Data'),

        'documento_sempartida_ids': fields.many2many('sped.documento', 'documento_sempartida', 'lote_id', 'documento_id', u'Documento não contabilizado'),
        'finan_sempartida_ids': fields.many2many('finan.lancamento', 'finan_sempartida',  'lote_id', 'lancamento_id', u'Lançamento não contabilizado'),
        #'holerite_sempartida_ids': fields.many2many('hr.payslip', 'holerite_sempartida',  'lote_id', 'slip_id', u'Holerite não contabilizado'),
        'holerite_sempartida_ids': fields.one2many('lote.holerite.sempartida', 'lote_id', u'Holerite não contabilizado'),

        'item_ids': fields.one2many('lote.contabilidade.item', 'lote_id', string=u'Itens a lançar'),
        'lancamento_ids': fields.one2many('ecd.partida.lancamento', 'lote_id', string=u'Lançamentos contábies'),

    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'lote.contabilidaderelatorio', context=c),
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        'emissao': '%',
        'gerar_rateio': False,
        'somente_cnpj': False,
        'data': fields.datetime.now,
    }

    def onchange_data(self, cr, uid, ids, data_inicial, data_final, context={}):
        valores = {}
        retorno = {'value': valores}

        if not data_inicial or not data_inicial:
            return retorno

        data_inicial = parse_datetime(data_inicial).date()
        data_final = parse_datetime(data_final).date()
        data_mes_inicial = primeiro_dia_mes(agora())        
                
        if data_inicial > data_final:
            raise osv.except_osv(u'Inválido!', u'Data inicial maior que a Data final!')
        
        elif data_inicial >= data_mes_inicial or data_final >= data_mes_inicial:
            raise osv.except_osv(u'Aviso!', u'Datas no periodo Atual, usar datas menor que {a}!'.format(a=formata_data(data_mes_inicial)))        
        
        return retorno

    def create(self, cr, uid, vals, context={}):
        self.lote_periodo_contabil(cr, uid, [], vals)

        res = super(lote_contabilidade, self).create(cr, uid, vals, context)

        return res

    def write(self, cr, uid, ids, vals, context={}):
        self.lote_periodo_contabil(cr, uid, ids, vals)

        res = super(lote_contabilidade, self).write(cr, uid, ids, vals, context)

        return res

    def unlink(self, cr, uid, ids, context={}):
        lancamento_pool = self.pool.get('ecd.lancamento.contabil')
        
        if len(ids) > 1:
            raise osv.except_osv(u'ATENÇÃO!', u'Exclua 1 lote por vez!')            

        self.lote_periodo_contabil(cr, uid, ids, vals={})

        for lote_obj in self.browse(cr, uid, ids):
            
            if lote_obj.importado:
                if uid not in [1,435] :
                    raise osv.except_osv(u'ATENÇÃO!', u'Lote ja impotado! Você não tem permissão para excluir o lote!')

            dados = self.pool.get('ecd.recomposicao.saldo').gera_dados_contas_recompor(cr, uid, lote_obj.id, False, context)

            lancamento_ids = lancamento_pool.search(cr, uid, [('lote_id', '=', lote_obj.id)])

            for lancamento_obj in lancamento_pool.browse(cr, uid, lancamento_ids):
                lancamento_obj.unlink(context={'lote_excluir': True})

            res = super(lote_contabilidade, self).unlink(cr, uid, ids, context=context)

            cr.execute('delete from lote_contabilidade_item where lote_id = {id}'.format(id=lote_obj.id))
            cr.execute('delete from account_asset_depreciation_line where lote_id = {id}'.format(id=lote_obj.id))
            cr.execute('delete from documento_sempartida where lote_id = {id}'.format(id=lote_obj.id))
            cr.execute('delete from finan_sempartida where lote_id = {id}'.format(id=lote_obj.id))

            self.pool.get('ecd.recomposicao.saldo').gera_saldo_contas(cr, uid, dados, context)

            return res

    def lote_periodo_contabil(self, cr, uid, ids, vals, context=None):
        if ids:
            id = ids[0]
            lote_obj = self.browse(cr, uid, id)
            
            if 'company_id' in vals:
                company_id = vals.get('company_id')
            else:               
                company_id = lote_obj.company_id.id
            
            if 'data_inicial' in vals:
                data_inicial = vals.get('data_inicial')
            else:
                data_inicial = lote_obj.data_inicial
                
            if 'data_final' in vals:
                data_final = vals.get('data_final')
            else:
                data_final = lote_obj.data_final
                
        else:
            company_id = vals.get('company_id')
            data_inicial = vals.get('data_inicial')
            data_final = vals.get('data_final')

        data_inicial = parse_datetime(data_inicial).date()
        data_final = parse_datetime(data_final).date()
        data_inicial = str(data_inicial)[:10]
        data_final = str(data_final)[:10]


        periodo_pool = self.pool.get('ecd.periodo')
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        sql = """
            select
                id
            from
                ecd_periodo
            where
                cnpj_cpf = '{cnpj_cpf}'
                and '{data_inicial}' >= data_inicial
                and '{data_final}' <= data_final
            order by
                company_id,
                data_final desc

        """
        sql = sql.format(cnpj_cpf=company_obj.partner_id.cnpj_cpf,data_inicial=data_inicial,data_final=data_final)
        cr.execute(sql)
        #print(sql)

        dados = cr.fetchall()
        if not dados:
            raise osv.except_osv(u'ATENÇÃO!', u'Não existe período contábil na Empresa selecionada!')
        for id in dados:
            periodo_obj = periodo_pool.browse(cr, uid, id[0])

            if periodo_obj.permitir_lancamento in ['3'] and periodo_obj.situacao == 'F':
                raise osv.except_osv(u'ATENÇÃO!', u'Período contábil já Fechado!')

    def busca_dados(self, cr, uid, ids, period_id, context={}):
        if not period_id:
            return {}

        period_pool = self.pool.get('account.period')
        period_obj = period_pool.browse(cr, uid, period_id)

        retorno = {}
        valores = {}
        retorno['value'] = valores
        valores['data_inicial'] = period_obj.date_start
        valores['data_final'] = period_obj.date_stop
        return retorno
    
    def on_change_plano(self, cr, uid, ids, company_id, context={}):
        if not company_id:
            return {}
        retorno = {}
        valores = {}
        retorno['value'] = valores
     
        company_pool = self.pool.get('res.company')
        company_obj = company_pool.browse(cr, uid, company_id)
        if company_obj.plano_id:
            valores['plano_id'] = company_obj.plano_id.id             
        else:
            raise osv.except_osv(u'Inválido !', u'Não existe plano de Contas na Empresa selecionada!')             
        return retorno

    def _exporta_lote_patrimonio(self, cr, uid, ids, context={}):

        item_pool = self.pool.get('lote.contabilidade.item')

        arquivo_texto = u''

        for export_obj in self.browse(cr, uid, ids):
            cnpj = export_obj.company_id.partner_id.cnpj_cpf

            sql = """

            select *
                from exporta_patrimonio_view a

            where
                a.cnpj_cpf = '{cnpj}'"""

            if not export_obj.somente_cnpj:
                sql +="""
                    and a.company_id = """ + str(export_obj.company_id.id)

            sql +="""
                and a.data between '{data_inicial}' and '{data_final}'

            order by
                data,
                patrimonio_id;"""


            sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final, cnpj=cnpj)

            cr.execute(sql)
            dados = cr.fetchall()

            if not dados:
                raise osv.except_osv(u'ATENÇÃO!', u'Não existem dados nos parâmentros informados!')

            patrimonio_ids = []
            patrimonio_sempartida_ids = []
            for cnpj_cpf, company_id, patrimonio_id, valor, data, tipo, conta_debito, conta_credito in dados:


                patrimonio_obj = self.pool.get('account.asset.asset').browse(cr, uid, patrimonio_id)

                if not conta_debito or not conta_credito:
                    raise osv.except_osv(u'ATENÇÃO!', u'Categoria sem conta definidas! {categoria}'.format(categoria=patrimonio_obj.category_id.name))

                export = integracao_questor()
                historico = u''
                if tipo == 'D':
                    if patrimonio_obj.category_id.historico_id_depreciacao:
                        historico += patrimonio_obj.category_id.historico_id_depreciacao.nome or ''
                    historico += ' - ' + patrimonio_obj.category_id.name
                    historico += ' ' + patrimonio_obj.company_id.partner_id.name or ''

                elif tipo == 'BA':
                    if patrimonio_obj.category_id.historico_id_baixa_patrimonio:
                        historico += patrimonio_obj.category_id.historico_id_baixa_patrimonio.nome or ''
                    historico += ' - ' + patrimonio_obj.name
                    historico += ' - ' + patrimonio_obj.nf_venda_id.descricao
                    #historico += ' ' + patrimonio_obj.company_id.partner_id.name or ''

                elif tipo == 'BD':
                    if patrimonio_obj.category_id.historico_id_baixa_depreciacao:
                        historico += patrimonio_obj.category_id.historico_id_baixa_depreciacao.nome or ''
                    historico += ' - ' + patrimonio_obj.name
                    historico += ' - ' + patrimonio_obj.nf_venda_id.descricao
                    #historico += ' ' + patrimonio_obj.company_id.partner_id.name or ''

                valor = D(valor)
                export.numero_documento = patrimonio_obj.code

                export.complemento_historico = historico

                dados_item = {
                    'lote_id': export_obj.id,
                    'cnpj_cpf': cnpj_cpf,
                    'company_id': company_id,
                    'patrimonio_id': patrimonio_id,
                    'data': data,
                    'conta_debito_id': conta_debito,
                    'conta_credito_id':conta_credito,
                    'valor': valor,
                    'historico': export.complemento_historico,
                }
                item_pool.create(cr, uid, dados_item)


        return arquivo_texto

    def _exporta_documentos_fiscais(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('lote.contabilidade.item')

        arquivo_texto = u''
        for export_obj in self.browse(cr, uid, ids):
            cnpj = export_obj.company_id.partner_id.cnpj_cpf
            #cnpj = cnpj[:10]

            sql = """
            select
                sd.id

            from
                sped_documento sd
                join res_company c on c.id = sd.company_id
                join res_partner p on p.id = c.partner_id

            where
                p.cnpj_cpf = '{cnpj}'"""

            if not export_obj.somente_cnpj:
                sql +="""
                    and c.id = """ + str(export_obj.company_id.id)

            sql +="""
                and sd.situacao in ('00','01')
                and sd.emissao like '{emissao}'
                and sd.modelo != 'TF'
                and (
                    (sd.emissao = '0' and sd.state = 'autorizada' and sd.modelo in ('55','SE'))
                    or
                    (sd.emissao = '1')
                    or
                    (sd.modelo not in ('55','SE'))
                )
                and (
                    (       sd.emissao = '0'
                        and sd.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
                    ) or
                    (       sd.emissao = '1'
                        and sd.data_entrada_saida_brasilia between '{data_inicial}' and '{data_final}'
                    )
                )
                and sd.lote_id is null


            order by
                sd.data_emissao_brasilia,
                sd.emissao,
                sd.serie,
                sd.numero;
            """
            sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final, cnpj=cnpj, emissao=export_obj.emissao or '%')

            cr.execute(sql)

            dados = cr.fetchall()

            if not dados:
                return arquivo_texto

            documento_ids = []
            documento_sempartida_ids = []
            for ret in dados:
                documento_ids.append(ret[0])

            documento_objs = self.pool.get('sped.documento').browse(cr, 1, documento_ids)

            for documento_obj in documento_objs:
                partida_objs = documento_obj.get_partidas_dobradas()

                if not len(partida_objs):

                    documento_sempartida_ids.append(documento_obj.id)

                for partida_obj in partida_objs:
                    export = integracao_questor()
                    cnpj_cpf = documento_obj.company_id.partner_id.cnpj_cpf
                    if documento_obj.emissao == '0':
                        export.data_lancamento = parse_datetime(documento_obj.data_emissao_brasilia).date()
                    else:
                        export.data_lancamento = parse_datetime(documento_obj.data_entrada_saida_brasilia).date()

                    export.numero_documento = documento_obj.numero

                    try:
                        export.conta_debito = partida_obj.conta_debito_id.codigo or partida_obj.conta_debito_id.id
                    except:
                        pass

                    try:
                        export.conta_credito = partida_obj.conta_credito_id.codigo or partida_obj.conta_debito_id.id
                    except:
                        pass

                    export.valor_documento = partida_obj.valor

                    historico = u''
                    if partida_obj.codigo_historico:
                        export.codigo_historico = partida_obj.codigo_historico
                        historico += partida_obj.historico


                    #if documento_obj.entrada_saida == '0':
                        #historico = u'Entrada '
                    #else:
                        #historico = u'Saída '

                    #if documento_obj.modelo in ['65','55']:
                        #historico += u'NFe '
                    #elif documento_obj.modelo in ['01','1B','04','21','22','07','27','02','06','29','28']:
                        #historico += u'NF '
                    #elif documento_obj.modelo in ['2D','2B','2C']:
                        #historico += u'CF '
                    #elif documento_obj.modelo in ['SC','SE']:
                        #historico += u'NFS '
                    #elif documento_obj.modelo == 'RL':
                        #historico += u'RL '
                    #elif documento_obj.modelo == '57':
                        #historico += u'CTe '
                    #else:
                        #historico += 'Doc '

                    historico += formata_valor(documento_obj.numero, casas_decimais=0)
                    historico += ' - '

                    if documento_obj.partner_id.razao_social:
                        historico += documento_obj.partner_id.razao_social
                    else:
                        historico += documento_obj.partner_id.name

                    export.complemento_historico = historico

                    arquivo_texto += export.registro_contabil()

                    dados_item = {
                        'lote_id': export_obj.id,
                        'cnpj_cpf': cnpj_cpf,
                        'company_id': documento_obj.company_id.id,
                        'documento_id': documento_obj.id,
                        'data': str(export.data_lancamento),
                        'valor': partida_obj.valor,
                        'historico': export.complemento_historico,
                        'codigo_historico': str(export.codigo_historico),
                        'centrocusto_id': partida_obj.centrocusto_id.id if partida_obj.centrocusto_id else False,
                    }

                    if partida_obj.conta_debito_id:
                        dados_item['conta_debito_id'] = partida_obj.conta_debito_id.id

                    if partida_obj.conta_credito_id:
                        dados_item['conta_credito_id'] = partida_obj.conta_credito_id.id

                    item_pool.create(cr, uid, dados_item)

            export_obj.write({'documento_sempartida_ids': [[6, False, documento_sempartida_ids]]})


        return arquivo_texto

    def _exporta_folha_pagamento(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('lote.contabilidade.item')
        holerite_sempartida = self.pool.get('lote.holerite.sempartida')

        arquivo_texto = u''
        for export_obj in self.browse(cr, uid, ids):
            cnpj = export_obj.company_id.partner_id.cnpj_cpf

            if export_obj.tipo == 'FG':
                sql = """
                    select
                        h.id

                    from
                        hr_payslip h
                        join res_company c on c.id = h.company_id
                        join res_partner rp on rp.id = c.partner_id

                    where
                        rp.cnpj_cpf = '{cnpj}'
                        and h.simulacao = False
                        and ((
                                h.tipo = 'N'
                                and h.date_from >= '{data_inicial}'
                                and h.date_to <= '{data_final}'
                            )
                            or (
                                h.tipo = 'R'
                                and h.data_afastamento between '{data_inicial}' and '{data_final}'
                            )
                            or (
                                h.tipo = 'D'
                                and h.date_from >= '{data_inicial}'
                                and h.date_to <= '{data_final}'
                            )
                            or (
                                h.tipo = 'F'
                                and to_char(h.date_from - interval '2 days', 'YYYY-MM-DD') between '{data_inicial}' and '{data_final}'
                            )
                        )
                """

                if not export_obj.somente_cnpj:
                    sql +="""
                        and c.id = """ + str(export_obj.company_id.id)

                sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)

            elif export_obj.tipo == 'PF':
                sql = """
                    select
                        h.id

                    from
                        hr_payslip h
                        join res_company c on c.id = h.company_id
                        join res_partner rp on rp.id = c.partner_id

                    where
                        rp.cnpj_cpf = '{cnpj}'
                        and h.provisao = True
                        and h.tipo = 'F'
                        and h.date_from between '{data_inicial}' and '{data_final}'
                """

                if not export_obj.somente_cnpj:
                    sql +="""
                        and c.id = """ + str(export_obj.company_id.id)

                sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final, cnpj=cnpj)
                #print(sql)

            elif export_obj.tipo == 'PD':
                sql = """
                    select
                        h.id

                    from
                        hr_payslip h
                        join res_company c on c.id = h.company_id
                        join res_partner rp on rp.id = c.partner_id

                    where
                        rp.cnpj_cpf = '{cnpj}'
                        and h.provisao = True
                        and h.tipo = 'D'
                        and h.date_to between '{data_inicial}' and '{data_final}'
                """

                if not export_obj.somente_cnpj:
                    sql +="""
                        and c.id = """ + str(export_obj.company_id.id)

                sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final, cnpj=cnpj)

            #print(sql)

            cr.execute(sql)

            dados = cr.fetchall()

            if not dados:
                return arquivo_texto

            documento_ids = []
            for ret in dados:
                documento_ids.append(ret[0])

            documento_objs = self.pool.get('hr.payslip').browse(cr, uid, documento_ids)

            partidas_acumuladas = {}
            holerite_sempartida_ids = []
            for holerite_obj in documento_objs:

                partida_objs = holerite_obj.get_partidas_dobradas_folha()

                #for partida_obj in partida_objs:
                #    chave_acumulada = str(holerite_obj.company_id.partner_id.cnpj_cpf)
                #    chave_acumulada += '|' + str(partida_obj.data)
                #    chave_acumulada += '|' + str(partida_obj.conta_debito_id.codigo or partida_obj.conta_debito_id.id)
                #    chave_acumulada += '|' + str(partida_obj.conta_credito_id.codigo or partida_obj.conta_credito_id.id)
                #    chave_acumulada += '|' + partida_obj.historico
                #
                #    print(chave_acumulada)
                #    if chave_acumulada in partidas_acumuladas:
                #        partidas_acumuladas[chave_acumulada].valor += partida_obj.valor
                #    else:
                #        partidas_acumuladas[chave_acumulada] = partida_obj
                if not len(partida_objs):

                    sem_obj = {
                        'lote_id': export_obj.id,
                        'slip_id': holerite_obj.id,
                    }
                    holerite_sempartida_ids.append(sem_obj)
                #    holerite_sempartida_ids.append(holerite_obj.id)


            #for chave_acumulada in partidas_acumuladas:
                for partida_obj in partida_objs:
            #       partida_obj = partidas_acumuladas[chave_acumulada]
                    if partida_obj.sem_partida:

                        sem_obj = {
                            'lote_id': export_obj.id,
                            'slip_id': holerite_obj.id,
                            'rule_id': partida_obj.rule_id,
                        }
                        holerite_sempartida_ids.append(sem_obj)
                        continue

                    export = integracao_questor()
                    export.cnpj_cpf = limpa_formatacao(partida_obj.cnpj)
                    export.data_lancamento = partida_obj.data
                    export.numero_documento = holerite_obj.id

                    try:
                        export.conta_debito = partida_obj.conta_debito_id.codigo or partida_obj.conta_debito_id.id
                    except:
                        pass

                    try:
                        export.conta_credito = partida_obj.conta_credito_id.codigo or partida_obj.conta_debito_id.id
                    except:
                        pass

                    export.valor_documento = partida_obj.valor

                    if partida_obj.codigo_historico:
                        export.codigo_historico = partida_obj.codigo_historico

                    historico = u''

                    historico += partida_obj.historico

                    export.complemento_historico = historico

                    arquivo_texto += export.registro_contabil()

                    dados_item = {
                        'lote_id': export_obj.id,
                        'slip_id': holerite_obj.id,
                        'data': str(export.data_lancamento),
                        'valor': partida_obj.valor,
                        'centrocusto_id': partida_obj.centrocusto_id if partida_obj.centrocusto_id else False,
                        'historico': export.complemento_historico,
                        'codigo_historico': str(export.codigo_historico),
                    }

                    if partida_obj.conta_debito_id:
                        dados_item['conta_debito_id'] = partida_obj.conta_debito_id.id

                    if partida_obj.conta_credito_id:
                        dados_item['conta_credito_id'] = partida_obj.conta_credito_id.id

                    item_pool.create(cr, uid, dados_item)

            for holerite_sempartida_id in holerite_sempartida_ids:
                holerite_sempartida.create(cr, uid, holerite_sempartida_id)

        return arquivo_texto

    def _exporta_financeiro(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('lote.contabilidade.item')

        arquivo_texto = u''
        for export_obj in self.browse(cr, uid, ids):
            cnpj = export_obj.company_id.partner_id.cnpj_cpf

            sql = """
            select
                fl.id
            from
                finan_lancamento fl                
                join res_company c on c.id = fl.company_id
                join res_partner p on p.id = c.partner_id                

            where                
                (
                    (fl.data is not null and fl.data between '{data_inicial}' and '{data_final}')
                 or
                    (fl.data is null and fl.data_quitacao is not null and fl.data_quitacao between '{data_inicial}' and '{data_final}')
                )
                and p.cnpj_cpf = '{cnpj}'
            """

            if not export_obj.somente_cnpj:
                sql +="""
                    and c.id = """ + str(export_obj.company_id.id)

            sql +="""
                and fl.tipo in ('E', 'S', 'T')
                and fl.lote_id is null
                and (fl.provisionado = false or fl.provisionado = null)                
            order by
                fl.data_quitacao, fl.tipo;
            """
            sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final, cnpj=cnpj)

            cr.execute(sql)

            dados = cr.fetchall()

            lancamento_ids = []
            for ret in dados:
                lancamento_ids.append(ret[0])

            sql = """
            select
                fl.id
            from
                finan_lancamento fl
                join finan_lancamento l on l.id = fl.lancamento_id
                join res_company c on c.id = l.company_id
                join res_partner p on p.id = c.partner_id                
            where
                (
                    (fl.data is not null and fl.data between '{data_inicial}' and '{data_final}')
                 or
                    (fl.data is null and fl.data_quitacao is not null and fl.data_quitacao between '{data_inicial}' and '{data_final}')
                )
                and p.cnpj_cpf = '{cnpj}'"""

            if not export_obj.somente_cnpj:
                sql +="""
                    and c.id = """ + str(export_obj.company_id.id)

            sql +="""
                and fl.tipo in ('PP', 'PR')
                and l.tipo not in ('LR', 'LP')
                and fl.lote_id is null
                and (l.provisionado = false or l.provisionado = null)                
            order by
                fl.data_quitacao, fl.tipo;
            """
            sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)

            cr.execute(sql)

            dados = cr.fetchall()

            for ret in dados:
                lancamento_ids.append(ret[0])

            sql = """
            select distinct
                fl.id
            from
                finan_lancamento fl
                join res_company c on c.id = fl.company_id
                join finan_documento d on d.id = fl.documento_id
                join sped_modelo_partida_dobrada mpd on mpd.id = d.modelo_partida_dobrada_receber_id               
                left join sped_documento sd on sd.id = fl.sped_documento_id
                left join sped_operacao so on so.id = sd.operacao_id
                left join finan_contrato fc on fc.id = fl.contrato_id
            where
                fl.data_documento between '{data_inicial}' and '{data_final}'
                and c.cnpj_cpf = '{cnpj}'
                and so.modelo_partida_dobrada_id is null
            """

            if not export_obj.somente_cnpj:
                sql +="""
                    and c.id = """ + str(export_obj.company_id.id)

            sql +="""
                and fl.tipo = 'R'
                and fl.lote_id is null
                and (fl.provisionado = false or fl.provisionado = null)
                and (fc.natureza not in ('PP','RP') or fc.natureza is null)
            """
            sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)

            cr.execute(sql)

            dados = cr.fetchall()

            for ret in dados:
                lancamento_ids.append(ret[0])

            #
            # Duplicatas e provisões a pagar
            #
            sql = """
            select distinct
                fl.id
            from
                finan_lancamento fl
                join res_company c on c.id = fl.company_id
                join finan_documento d on d.id = fl.documento_id
                join sped_modelo_partida_dobrada mpd on mpd.id = d.modelo_partida_dobrada_pagar_id               
                left join sped_documento sd on sd.id = fl.sped_documento_id
                left join sped_operacao so on so.id = sd.operacao_id
                left join finan_contrato fc on fc.id = fl.contrato_id
            where
                fl.data_documento between '{data_inicial}' and '{data_final}'
                and c.cnpj_cpf = '{cnpj}'
                and so.modelo_partida_dobrada_id is null
            """
            if not export_obj.somente_cnpj:
                sql +="""
                    and c.id = """ + str(export_obj.company_id.id)

            sql +="""
                and fl.tipo = 'P'
                and fl.lote_id is null
                and fl.provisionado = false
                and (fl.provisionado = false or fl.provisionado = null)
                and (fc.natureza not in ('PP','RP') or fc.natureza is null);
            """
            sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final, cnpj=cnpj)
            print(sql)

            cr.execute(sql)

            dados = cr.fetchall()

            for ret in dados:
                lancamento_ids.append(ret[0])

            #
            # Lançamentos baixados
            #
            sql = """
            select
                fl.id
            from
                finan_lancamento fl
                join res_company c on c.id = fl.company_id
                join finan_motivobaixa mb on mb.id = fl.motivo_baixa_id                                
            where
                fl.data_baixa between '{data_inicial}' and '{data_final}'
                and c.cnpj_cpf = '{cnpj}'                
            """

            if not export_obj.somente_cnpj:
                sql +="""
                    and c.id = """ + str(export_obj.company_id.id)

            sql +="""
                and fl.tipo in ('P', 'R')                
                and fl.lote_id is null
                and (fl.provisionado = false or fl.provisionado = null)                
            order by
                fl.data_quitacao, fl.tipo;
            """
            sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final, cnpj=cnpj)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()

            for ret in dados:
                lancamento_ids.append(ret[0])

            sql = """
            select distinct
                l.id,
                l.data_quitacao,
                l.tipo
            from
                finan_lancamento fl
                join finan_lancamento l on l.id = fl.lancamento_id
                join res_company c on c.id = l.company_id
                join res_partner p on p.id = c.partner_id                
            where
                (
                    (fl.data is not null and fl.data between '{data_inicial}' and '{data_final}')
                 or
                    (fl.data is null and fl.data_quitacao is not null and fl.data_quitacao between '{data_inicial}' and '{data_final}')
                )
                and p.cnpj_cpf = '{cnpj}'"""

            if not export_obj.somente_cnpj:
                sql +="""
                    and c.id = """ + str(export_obj.company_id.id)

            sql +="""
                and fl.tipo in ('PP', 'PR')
                and l.tipo in ('LR', 'LP')
                and l.lote_id is null
                and (l.provisionado = false or l.provisionado = null)                
            order by
                l.data_quitacao, l.tipo;
            """
            sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)

            cr.execute(sql)

            dados = cr.fetchall()

            for ret in dados:
                lancamento_ids.append(ret[0])

            if len(lancamento_ids) == 0:
                return arquivo_texto

            lancamento_objs = self.pool.get('finan.lancamento').browse(cr, uid, lancamento_ids)

            finan_sempartida_ids = []

            for lancamento_obj in lancamento_objs:
                
                partida_objs = lancamento_obj.get_partidas_dobradas(rateio=True)

                if not len(partida_objs):
                    if not  lancamento_obj.id in finan_sempartida_ids:
                        finan_sempartida_ids.append(lancamento_obj.id)

                company_obj = lancamento_obj.company_id

                #
                # Trata o company para pagamentos e pagamentos em lote
                #
                if lancamento_obj.tipo in ('PR', 'PP'):
                    company_obj = lancamento_obj.lancamento_id.company_id

                cnpj_cpf = company_obj.partner_id.cnpj_cpf

                for partida_obj in partida_objs:
                    export = integracao_questor()

                    if lancamento_obj.tipo in ['R', 'P']:
                        if lancamento_obj.data_baixa and lancamento_obj.motivo_baixa_id:
                            export.data_lancamento = parse_datetime(lancamento_obj.data_baixa).date()
                        else:
                            export.data_lancamento = parse_datetime(lancamento_obj.data_documento).date()

                    else:
                        if lancamento_obj.data:
                            export.data_lancamento = parse_datetime(lancamento_obj.data).date()
                        elif lancamento_obj.data_quitacao:
                            export.data_lancamento = parse_datetime(lancamento_obj.data_quitacao).date()
                        else:
                            export.data_lancamento = parse_datetime(lancamento_obj.data_documento).date()


                    if lancamento_obj.tipo in ['S', 'E', 'T', 'R', 'P']:
                        export.numero_documento = lancamento_obj.numero_documento or ''
                    
                    elif lancamento_obj.tipo in ['PR', 'PP']:
                        export.numero_documento = lancamento_obj.lancamento_id.numero_documento or ''
                        
                    elif lancamento_obj.tipo in ['LR', 'LP']:
                        if partida_obj.numero_documento:
                            export.numero_documento =  partida_obj.numero_documento or ''
                        else:
                            export.numero_documento =  lancamento_obj.numero_documento or ''

                    export.conta_debito = partida_obj.conta_debito_id.codigo or partida_obj.conta_debito_id.id
                    export.conta_credito = partida_obj.conta_credito_id.codigo or partida_obj.conta_debito_id.id
                    export.valor_documento = partida_obj.valor

                    if partida_obj.codigo_historico:
                        export.codigo_historico = partida_obj.codigo_historico

                    historico = u''
                    if partida_obj.historico:
                        historico += partida_obj.historico + ' '

                    if lancamento_obj.tipo in ['S', 'E', 'T']:
                        historico += lancamento_obj.descricao or u's/nº'
                        
                    if lancamento_obj.tipo in ['R','P']:
                        historico += lancamento_obj.numero_documento or u's/nº'
                        
                    elif lancamento_obj.tipo in ['PR', 'PP']:
                        historico += lancamento_obj.lancamento_id.numero_documento or u's/nº'
                        historico += u' Ref. '
                        historico += lancamento_obj.numero_documento or ''
                                                
                    elif lancamento_obj.tipo in ['LR', 'LP']:
                        if partida_obj.numero_documento:                            
                            historico += partida_obj.numero_documento or ''
                            historico += u' no '
                            historico += lancamento_obj.numero_documento or ''
                        else:
                            historico += u' Ref. '
                            historico += lancamento_obj.numero_documento or ''
                            

                    if lancamento_obj.complemento:
                        historico += ' '
                        historico += lancamento_obj.complemento

                    partner_obj = None
                    if lancamento_obj.tipo in ['S', 'E', 'T', 'P', 'R']:
                        partner_obj = lancamento_obj.partner_id
                    else:
                        partner_obj = lancamento_obj.lancamento_id.partner_id

                    if partner_obj:
                        historico += ' - '

                        if partner_obj.razao_social:
                            historico += partner_obj.razao_social
                        else:
                            historico += partner_obj.name

                    export.complemento_historico = historico

                    arquivo_texto += export.registro_contabil()

                    dados_item = {
                        'lote_id': export_obj.id,
                        'cnpj_cpf': cnpj_cpf,
                        'company_id': company_obj.id,
                        'data': str(export.data_lancamento),
                        'lancamento_id': lancamento_obj.id,
                        'conta_debito_id': partida_obj.conta_debito_id.id,
                        'conta_credito_id': partida_obj.conta_credito_id.id,
                        'valor': partida_obj.valor,
                        'historico': export.complemento_historico,
                        'codigo_historico': str(export.codigo_historico),
                        'centrocusto_id': partida_obj.centrocusto_id.id if partida_obj.centrocusto_id else False,
                    }
                    item_pool.create(cr, uid, dados_item)

            #print(finan_sempartida_ids)
            export_obj.write({'finan_sempartida_ids': [[6, False, finan_sempartida_ids]]})

        return arquivo_texto

    def gera_exportacao(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        arquivo_texto = u''
        for export_obj in self.browse(cr, uid, ids):
            cr.execute('delete from lote_contabilidade_item where lote_id = {id}'.format(id=export_obj.id))

            if export_obj.documento_sempartida_ids:
                cr.execute('delete from documento_sempartida where lote_id = {id}'.format(id=export_obj.id))

            if export_obj.finan_sempartida_ids:
                cr.execute('delete from finan_sempartida where lote_id = {id}'.format(id=export_obj.id))

            if export_obj.holerite_sempartida_ids:
                cr.execute('delete from lote_holerite_sempartida where lote_id = {id}'.format(id=export_obj.id))

            print(u'Buscando lancamento contabilidade', export_obj.company_id.name)

            if export_obj.tipo in ['D', 'G']:
                arquivo_texto += self._exporta_documentos_fiscais(cr, uid, ids, context)

            elif export_obj.tipo in ['F', 'G']:
                arquivo_texto += self._exporta_financeiro(cr, uid, ids, context)

            elif export_obj.tipo in ('FG','PF','PD'):
                arquivo_texto += self._exporta_folha_pagamento(cr, uid, ids, context)

            elif export_obj.tipo == 'PT':
                arquivo_texto += self._exporta_lote_patrimonio(cr, uid, ids, context)

            return True

    def gera_contabilidade(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for lote_obj in self.browse(cr, uid, ids):
            if not lote_obj.item_ids:
                return {}
            
            self.verifica_contas(cr, uid, lote_obj)
            
            sql_lote = ("""
                        select
                            distinct
                            l.id as lancamento,
                            sp.id as documento,
                            h.id as holerite
                            
                        from lote_contabilidade_item ci
                        left join finan_lancamento l on l.id = ci.lancamento_id
                        left join sped_documento sp on sp.id = ci.documento_id
                        left join hr_payslip h on h.id = ci.slip_id
                            
                        where
                            ci.lote_id = {id}
                            and (l.lote_id is not null or sp.lote_id is not null or h.lote_id is not null)""".format(id=lote_obj.id))
            cr.execute(sql_lote)
            sql_lote_dados = cr.fetchall()
            
            if len(sql_lote_dados) > 0:
                raise osv.except_osv(u'ATENÇÃO!', u'Existe Lançamentos já Contabilizados! Gerar Nova Busca!')                  
            

            cr.execute('delete from ecd_lancamento_contabil_rateio where lote_id = {id}'.format(id=lote_obj.id))

            if lote_obj.tipo == 'PT':
                self.gera_contabilidade_patrimonio(cr, uid, lote_obj)

            else:
                sql = """
                    select
                        distinct
                        ci.cnpj_cpf,
                        ci.company_id,
                        ci.data,
                        ci.lancamento_id,
                        ci.documento_id
                    from lote_contabilidade_item ci
                    where
                        ci.lote_id = """ + str(lote_obj.id) + """

                    order by
                        ci.data """
                cr.execute(sql)
                dados = cr.fetchall()

                for cnpj_cpf, company_id, data, lancamento_id, documento_id  in dados:

                    print(u'Gerando lote contabilidade',lote_obj.company_id.name)

                    if  lote_obj.tipo in ('FG','PF','PD'):
                        self.gera_lancamento_folha(cr, uid, lote_obj, data)

                    elif lancamento_id:
                        self.gera_lancamento_financeiro(cr, uid, lote_obj, lancamento_id, cnpj_cpf, company_id, data)

                    elif documento_id:

                        self.gera_lancamento_fiscal(cr, uid, lote_obj, documento_id, cnpj_cpf, company_id, data)

            lote_obj.write({'importado': True})
            dados = self.pool.get('ecd.recomposicao.saldo').gera_dados_contas_recompor(cr, uid, lote_obj.id, False, context)
            self.pool.get('ecd.recomposicao.saldo').gera_saldo_contas(cr, uid, dados, context)



        return True

    def gera_rateio(self, cr, uid, ids, context={}):

        if not ids:
            return {}

        lancamento_pool = self.pool.get('ecd.lancamento.contabil')

        for lote_obj in self.browse(cr, uid, ids):
            if not lote_obj.lancamento_ids:
                return {}

            cr.execute('delete from ecd_lancamento_contabil_rateio where lote_id = {id}'.format(id=lote_obj.id))

            lancamentos_ids = lancamento_pool.search(cr, uid, [('lote_id', '=', lote_obj.id)])

            for lanc_obj in lancamento_pool.browse(cr, uid, lancamentos_ids):

                if lanc_obj.finan_lancamento_id:
                    self.gera_rateio_gerencial(cr, uid, lanc_obj.id, lanc_obj.finan_lancamento_id.id, False)

                elif lanc_obj.sped_documento_id:
                    self.gera_rateio_gerencial(cr, uid, lanc_obj.id, False, lanc_obj.sped_documento_id.id)


    def gera_lancamento_folha(self, cr, uid, lote_obj, data):
        lancamento_contabil_pool = self.pool.get('ecd.lancamento.contabil')
        partida_pool = self.pool.get('ecd.partida.lancamento')
        slip_pool = self.pool.get('hr.payslip')

        #self.verifica_contas(cr, uid, lote_obj)

        filtro = {
            'lote_id': str(lote_obj.id),
            'data': data,
        }

        sql = """
            select
                li.data_lancamento,
                li.tipo,
                rp.name,
                li.conta,
                li.contra_partida,
                historico,
                li.numero_documento,
                case
                when li.tipo in ('R','D','C') then
                li.centrocusto_id
                else null
                end as centrocusto_id,
                sum(valor)

            from lote_lancamento_importacao li
                join hr_payslip p on p.id = li.slip_id
                join res_company c on c.id = p.company_id
                join res_partner rp on rp.id = c.partner_id

            where
                li.lote_id = {lote_id}
                and li.data_lancamento = '{data}'

            group by
            li.data_lancamento,
            li.tipo,
            rp.name,
            li.conta,
            li.contra_partida,
            numero_documento,
            historico,
            8

            order by
            li.data_lancamento, rp.name;
        """

        sql = sql.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        old_empresa = ''
        for data_doc, tipo, empresa, conta_id, contra_partida,  historico, numero_documento, centrocusto_id, valor  in dados:
            if not old_empresa or old_empresa != empresa:
                dados_lancamento= {
                    'data': str(data),
                    'tipo': 'N',
                    'lanc': 'I',
                    'user_id': uid,
                    'lote_id': lote_obj.id,
                    'plano_id': lote_obj.plano_id.id,
                    'company_id': lote_obj.company_id.id,
                    'cnpj_cpf': lote_obj.company_id.partner_id.cnpj_cpf,
                }
                lancamento_contabil_id = lancamento_contabil_pool.create(cr, uid, dados_lancamento)
                old_empresa = empresa

            if tipo == 'D':
                dados_debito = {
                    'data': str(data),            
                    'company_id': lote_obj.company_id.id,
                    'cnpj_cpf': lote_obj.company_id.partner_id.cnpj_cpf,
                    'plano_id': lote_obj.plano_id.id,
                    'tipo': 'D',
                    'lancamento_id': lancamento_contabil_id,
                    'conta_id': conta_id,
                    'contra_partida_id':  contra_partida,
                    'numero_documento': numero_documento,
                    'centrocusto_id': centrocusto_id,
                    'vr_debito': D(valor),
                    'vr_credito': 0,
                    'historico': historico,
                            }
                partida_pool.create(cr, uid, dados_debito)

            elif tipo == 'C':
                dados_credito = {
                    'data': str(data),
                    'company_id': lote_obj.company_id.id,
                    'cnpj_cpf': lote_obj.company_id.partner_id.cnpj_cpf,
                    'plano_id': lote_obj.plano_id.id,
                    'tipo': 'C',
                    'lancamento_id': lancamento_contabil_id,
                    'conta_id': conta_id,
                    'contra_partida_id':  contra_partida,
                    'numero_documento': numero_documento,
                    'centrocusto_id': centrocusto_id,
                    'vr_debito': 0,
                    'vr_credito': D(valor),
                    'historico': historico,
                }
                partida_pool.create(cr, uid, dados_credito)


        sql = """
            select
                distinct
                ci.slip_id

            from lote_contabilidade_item ci
                where
                ci.lote_id = """ + str(lote_obj.id)

        cr.execute(sql)
        dados = cr.fetchall()

        for slip_id in dados:
            sql = 'update hr_payslip set lote_id = {lote_id} where id = {slip_id}'.format(lote_id=str(lote_obj.id),slip_id=str(slip_id[0]))
            cr.execute(sql)

    def gera_lancamento_financeiro(self, cr, uid, lote_obj, lancamento_id, cnpj_cpf, company_id, data):
        lancamento_contabil_pool = self.pool.get('ecd.lancamento.contabil')
        partida_pool = self.pool.get('ecd.partida.lancamento')
        lancamento_pool = self.pool.get('finan.lancamento')

        #self.verifica_contas(cr, uid, lote_obj)


        dados_lancamento = {
            'data': str(data),
            'tipo': 'N',
            'lanc': 'I',
            'user_id': uid,
            'lote_id': lote_obj.id,
            'plano_id': lote_obj.plano_id.id,
            'company_id': company_id,
            'cnpj_cpf': cnpj_cpf,
            'finan_lancamento_id': lancamento_id,
        }

        lancamento_contabil_id = lancamento_contabil_pool.create(cr, uid, dados_lancamento)

        sql_debito = """
            select
                *
            from
                lote_lancamento_importacao
            where
                lote_id = """ +  str(lote_obj.id) + """
                and lancamento_id = """ + str(lancamento_id)

        cr.execute(sql_debito)
        dados = cr.fetchall()

        for lote_id, _cnpj_cpf, _company_id, data_doc, tipo, _lancamento_id, _documento_id, _slip_id, patrimonio_id, conta_id, contra_partida, centrocusto_id, historico, numero_documento, numero, valor  in dados:

            if tipo == 'D':
                dados_debito = {
                    'data': str(data),
                    'company_id': company_id,
                    'cnpj_cpf': cnpj_cpf, 
                    'plano_id': lote_obj.plano_id.id,           
                    'tipo': 'D',
                    'lancamento_id': lancamento_contabil_id,
                    'conta_id': conta_id,
                    'contra_partida_id':  contra_partida,
                    'numero_documento': numero_documento,
                    'centrocusto_id': centrocusto_id,
                    'vr_debito': D(valor),
                    'vr_credito': 0,
                    'historico': historico,
                }
                partida_pool.create(cr, uid, dados_debito)

            elif tipo == 'C':
                dados_credito = {
                    'data': str(data),             
                    'company_id': company_id,
                    'cnpj_cpf': cnpj_cpf,
                    'plano_id': lote_obj.plano_id.id,
                    'tipo': 'C',
                    'lancamento_id': lancamento_contabil_id,
                    'conta_id': conta_id,
                    'contra_partida_id':  contra_partida,
                    'numero_documento': numero_documento,
                    'centrocusto_id': centrocusto_id,
                    'vr_debito': 0,
                    'vr_credito': D(valor),
                    'historico': historico,
                }
                partida_pool.create(cr, uid, dados_credito)

        sql = 'update finan_lancamento set lote_id = {lote_id} where id = {lancamento_id}'.format(lote_id=str(lote_obj.id),lancamento_id=str(lancamento_id))
        cr.execute(sql)

    def gera_lancamento_fiscal(self, cr, uid, lote_obj, documento_id, cnpj_cpf, company_id, data):
        lancamento_contabil_pool = self.pool.get('ecd.lancamento.contabil')
        partida_pool = self.pool.get('ecd.partida.lancamento')
        documento_pool = self.pool.get('sped.documento')

        #self.verifica_contas(cr, uid, lote_obj)

        dados_lancamento= {
            'data': str(data),
            'tipo': 'N',
            'lanc': 'I',
            'user_id': uid,
            'lote_id': lote_obj.id,
            'plano_id': lote_obj.plano_id.id,
            'company_id': company_id,
            'cnpj_cpf': cnpj_cpf,
            'sped_documento_id': documento_id,
        }
        lancamento_contabil_id = lancamento_contabil_pool.create(cr, uid, dados_lancamento)

        sql_debito = """
            select * from lote_lancamento_importacao
            where
            lote_id = """ +  str(lote_obj.id) + """
            and documento_id = """ + str(documento_id)

        cr.execute(sql_debito)
        dados = cr.fetchall()

        for lote_id, _cnpj_cpf, _company_id, data_doc, tipo, _lancamento_id, _documento_id, _slip_id, _patrimonio_id, conta_id, contra_partida, centrocusto_id, historico, numero_documento, numero, valor  in dados:

            if tipo == 'D':
                dados_debito = {
                    'data': str(data),            
                    'company_id': company_id,
                    'cnpj_cpf': cnpj_cpf,   
                    'plano_id': lote_obj.plano_id.id,         
                    'tipo': 'D',
                    'lancamento_id': lancamento_contabil_id,
                    'conta_id': conta_id,
                    'contra_partida_id':  contra_partida,
                    'numero_documento': numero,
                    'centrocusto_id': centrocusto_id,
                    'vr_debito': D(valor),
                    'vr_credito': 0,
                    'historico': historico,
                }
                partida_pool.create(cr, uid, dados_debito)

            elif tipo == 'C':
                dados_credito = {
                    'data': str(data), 
                    'company_id': company_id,
                    'cnpj_cpf': cnpj_cpf,   
                    'plano_id': lote_obj.plano_id.id,              
                    'tipo': 'C',
                    'lancamento_id': lancamento_contabil_id,
                    'conta_id': conta_id,
                    'contra_partida_id':  contra_partida,
                    'numero_documento': numero,
                    'centrocusto_id': centrocusto_id,
                    'vr_debito': 0,
                    'vr_credito': D(valor),
                    'historico': historico,
                }
                partida_pool.create(cr, uid, dados_credito)

        sql = 'update sped_documento set lote_id = {lote_id} where id = {documento_id}'.format(lote_id=str(lote_obj.id),documento_id=str(documento_id))
        cr.execute(sql)

    def gera_contabilidade_patrimonio(self, cr, uid, lote_obj):

        lancamento_contabil_pool = self.pool.get('ecd.lancamento.contabil')
        partida_pool = self.pool.get('ecd.partida.lancamento')

        #self.verifica_contas(cr, uid, lote_obj)

        filtro = {
            'lote_id': str(lote_obj.id),
            'data_inicial': lote_obj.data_inicial,
            'data_final': lote_obj.data_final,
        }

        sql = """
            select
                li.cnpj_cpf,
                li.company_id,
                to_char(li.data_lancamento,'YYYY-MM') as data_lancamento,
                li.tipo,
                li.conta,
                li.contra_partida,
                historico,
                sum(cast(valor as numeric (18,2))) as valor

            from
                lote_lancamento_importacao li
                join account_asset_asset a on a.id = li.patrimonio_id
                join account_asset_category ac on ac.id = a.category_id

            where
                li.lote_id = {lote_id}
                and li.data_lancamento between '{data_inicial}' and '{data_final}'
                and a.nf_venda_id is null

            group by
                li.cnpj_cpf,
                li.company_id,
                3,
                ac.id,
                li.tipo,
                li.conta,
                li.contra_partida,
                historico

            order by
                li.cnpj_cpf,
                li.company_id,
                3,
                ac.id;
        """

        sql = sql.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        old_data_doc = ''
        for cnpj_cpf, company_id, data_doc, tipo, conta_id, contra_partida, historico, valor  in dados:

            if not old_data_doc or old_data_doc != data_doc:

                data_inicial, data_final = primeiro_ultimo_dia_mes(int(data_doc[:4]), int(data_doc[6:]))

                dados_lancamento= {
                    'data': data_final,
                    'tipo': 'N',
                    'lanc': 'I',
                    'user_id': uid,
                    'lote_id': lote_obj.id,
                    'plano_id': lote_obj.plano_id.id,
                    'company_id': company_id,
                    'cnpj_cpf': cnpj_cpf,
                }
                old_data_doc = data_doc
                lancamento_contabil_id = lancamento_contabil_pool.create(cr, uid, dados_lancamento)


            if tipo == 'D':
                dados_debito = {
                    'data': data_final,
                    'company_id': company_id,
                    'cnpj_cpf': cnpj_cpf,
                    'plano_id': lote_obj.plano_id.id,
                    'lancamento_id': lancamento_contabil_id,
                    'tipo': 'D',
                    'conta_id': conta_id,
                    'contra_partida_id':  contra_partida,
                    #'numero_documento': numero_documento,
                    #'centrocusto_id':
                    'vr_debito': D(valor),
                    'vr_credito': 0,
                    'historico': historico,
                            }
                partida_pool.create(cr, uid, dados_debito)

            elif tipo == 'C':                
                dados_credito = {
                    'data': data_final,
                    'company_id': company_id,
                    'cnpj_cpf': cnpj_cpf,
                    'plano_id': lote_obj.plano_id.id,
                    'lancamento_id': lancamento_contabil_id,
                    'tipo': 'C',
                    'conta_id': conta_id,
                    'contra_partida_id':  contra_partida,
                    #'numero_documento': numero_documento,
                    #'centrocusto_id':
                    'vr_debito': 0,
                    'vr_credito': D(valor),
                    'historico': historico,
                }
                partida_pool.create(cr, uid, dados_credito)

        sql = """
            select
                distinct
                pi.patrimonio_id

            from lote_contabilidade_item pi
                join account_asset_asset a on a.id = pi.patrimonio_id
                where
                pi.lote_id = """ + str(lote_obj.id) + """
                and a.nf_venda_id is null"""


        cr.execute(sql)
        dados = cr.fetchall()

        for patrimonio_id in dados:
            sql = """update account_asset_depreciation_line dp set lote_id = {lote_id} where dp.asset_id = {patrimonio_id} and dp.depreciation_date between '{data_inicial}' and '{data_final}'""".format(lote_id=str(lote_obj.id),patrimonio_id=str(patrimonio_id[0]),data_inicial=lote_obj.data_inicial,data_final=lote_obj.data_final)
            cr.execute(sql)


        sql = """
            select
                li.cnpj_cpf,
                li.company_id,
                li.data_lancamento as data_lancamento,
                li.tipo,
                li.conta,
                li.contra_partida,
                historico,
                sum(cast(valor as numeric (18,2))) as valor

            from
                lote_lancamento_importacao li
                join account_asset_asset a on a.id = li.patrimonio_id

            where
                li.lote_id = {lote_id}
                and li.data_lancamento between '{data_inicial}' and '{data_final}'
                and a.nf_venda_id is not null

            group by
                li.cnpj_cpf,
                li.company_id,
                3,
                li.tipo,
                li.conta,
                li.contra_partida,
                historico

            order by
                li.cnpj_cpf,
                li.company_id,
                3
        """

        sql = sql.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        old_data_doc = ''
        for cnpj_cpf, company_id, data_doc, tipo, conta_id, contra_partida, historico, valor  in dados:

            if not old_data_doc or old_data_doc != data_doc:

                dados_lancamento= {
                    'data': data_doc,
                    'tipo': 'N',
                    'lanc': 'I',
                    'user_id': uid,
                    'lote_id': lote_obj.id,
                    'plano_id': lote_obj.plano_id.id,
                    'company_id': company_id,
                    'cnpj_cpf': cnpj_cpf,
                }
                old_data_doc = data_doc
                lancamento_contabil_id = lancamento_contabil_pool.create(cr, uid, dados_lancamento)


            if tipo == 'D':
                dados_debito = {
                    'data': data_doc,
                    'company_id': company_id,
                    'cnpj_cpf': cnpj_cpf,
                    'plano_id': lote_obj.plano_id.id,                                
                    'lancamento_id': lancamento_contabil_id,
                    'tipo': 'D',
                    'conta_id': conta_id,
                    'contra_partida_id':  contra_partida,
                    #'numero_documento': numero_documento,
                    #'centrocusto_id':
                    'vr_debito': D(valor),
                    'vr_credito': 0,
                    'historico': historico,
                            }
                partida_pool.create(cr, uid, dados_debito)

            elif tipo == 'C':
                dados_credito = {
                    'data': data_doc,                
                    'company_id': company_id,
                    'cnpj_cpf': cnpj_cpf,
                    'plano_id': lote_obj.plano_id.id,
                    'lancamento_id': lancamento_contabil_id,
                    'tipo': 'C',
                    'conta_id': conta_id,
                    'contra_partida_id':  contra_partida,
                    #'numero_documento': numero_documento,
                    #'centrocusto_id':
                    'vr_debito': 0,
                    'vr_credito': D(valor),
                    'historico': historico,
                }
                partida_pool.create(cr, uid, dados_credito)

        sql = """
            select
                distinct
                pi.patrimonio_id

            from lote_contabilidade_item pi
                join account_asset_asset a on a.id = pi.patrimonio_id
                where
                pi.lote_id = """ + str(lote_obj.id) + """
                and a.nf_venda_id is not null"""

        cr.execute(sql)
        dados = cr.fetchall()

        for patrimonio_id in dados:
            sql = """update account_asset_asset a set lote_id = {lote_id} where a.id  = {patrimonio_id} """.format(lote_id=str(lote_obj.id),patrimonio_id=str(patrimonio_id[0]))
            cr.execute(sql)

    def verifica_contas(self, cr, uid, lote_obj):
        conta_pool = self.pool.get('finan.conta')
        cnpj_cpf = lote_obj.company_id.partner_id.cnpj_cpf

        sql = """
            select distinct
                conta

            from lote_lancamento_importacao ci
                join finan_conta fc on fc.id = ci.conta

            where
                ci.lote_id = {lote_id}

            EXCEPT

            select distinct
                conta

            from lote_lancamento_importacao ci
                join finan_conta fc on fc.id = ci.conta
                join ecd_plano_conta ep on ep.id = fc.plano_id
                join res_company c on c.plano_id = ep.id
                join res_partner rp on rp.id = c.partner_id

            where
                ci.lote_id = {lote_id}
                and rp.cnpj_cpf = '{cnpj_cpf}'
            limit 1

        """
        sql = sql.format(cnpj_cpf=cnpj_cpf,lote_id=lote_obj.id)
        cr.execute(sql)
        dados = cr.fetchall()

        if not dados:
            return

        for conta_id in dados:
            conta_obj = conta_pool.browse(cr, uid, conta_id[0])
            raise osv.except_osv(u'ATENÇÃO!', u'Conta não vinculada a Empresa selecionada! Conta: ' + conta_obj.nome_simples + u'!')

    def gera_rateio_gerencial(self, cr, uid, lancamento_contabil_id, lancamento_id, documento_id):
        #
        # De acordo com o tipo (fiscal ou financeiro), vamos buscar o rateio gerencial
        # a ser aplicado
        #
        rateio_pool = self.pool.get('ecd.lancamento.contabil.rateio')

        rateios = []
        if documento_id:
            rateios = self.pool.get('sped.documento').browse(cr, uid, documento_id).get_rateio_contabil_gerencial()
        elif lancamento_id:
            rateios = self.pool.get('finan.lancamento').browse(cr, uid, lancamento_id).get_rateio_contabil_gerencial()

        for rateio in rateios:
            rateio['lancamento_contabil_id'] = lancamento_contabil_id
            rateio_pool.create(cr, uid, rateio)

    def gera_relatorio_conferencia(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            if not rel_obj.item_ids:
                return {}

            sql = """
                select
                    l.data_lancamento,
                    '[' || coalesce(f.codigo, 0) || '] ' || coalesce(f.nome,'') as nome_conta,
                    h.name as holerite,
                    a.name as patrimonio,
                    l.historico,
                    a.code as numero_patrimonio,
                    case
                    when l.numero_documento = '' then
                    cast(l.numero as varchar)
                    else
                    l.numero_documento end as documento,
                    case
                    when l.tipo = 'D' then
                    cast(l.valor as numeric(18,2))
                    else
                    0 end as valor_debito,
                    case
                    when l.tipo = 'C' then
                    cast(l.valor as numeric(18,2))
                    else
                    0 end as valor_credito
                from
                    lote_lancamento_importacao l
                    join finan_conta f on f.id = l.conta
                    left join hr_payslip h on h.id = l.slip_id
                    left join account_asset_asset a on a.id = l.patrimonio_id
                where
                    l.lote_id = """ + str(rel_obj.id)

            if rel_obj.diario_conta_id:
                sql += """
                        and l.conta = """ + str(rel_obj.diario_conta_id.id)

            sql += """
                    order by
                        l.data_lancamento,
                        l.lancamento_id,
                        l.documento_id,
                        l.slip_id,
                        l.patrimonio_id,
                        l.tipo desc;"""
            #print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            saldo = D(0)
            for data_lancamento, nome_conta, holerite, patrimonio, historico, numero_patrimonio, documento, conta_debito, conta_crebito in dados:
                linha = DicionarioBrasil()
                linha['data_lancamento'] = formata_data(data_lancamento)
                linha['nome_conta'] =  nome_conta
                linha['holerite'] = holerite
                linha['patrimonio'] = patrimonio
                linha['historico'] = historico
                linha['numero_patrimonio'] = numero_patrimonio
                linha['documento'] = documento
                linha['conta_debito'] = D(conta_debito)
                linha['conta_crebito'] = D(conta_crebito)
                saldo += conta_debito - conta_crebito
                linha['saldo'] = saldo
                linhas.append(linha)

            if rel_obj.tipo == 'FG':
                rel = FinanRelatorioAutomaticoRetrato()
            else:
                rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Conferência de Importação'
            rel.colunas = [
                ['data_lancamento', 'D', 10, u'Data', False],
            ]

            if not rel_obj.diario_conta_id:
                rel.colunas += [
                    ['nome_conta', 'C', 35, u'Conta Contábil', False],
                ]

            if rel_obj.tipo in ['FG','PD','PF']:
                rel.colunas += [
                    ['holerite',   'C', 50, u'Holerite de.', False],
                    #['historico',   'C', 80, u'Histórico.', False],
                    ['documento', 'C', 10, u'Nº doc.', False],
                    ['conta_debito', 'F', 15, u'Débito', True],
                    ['conta_crebito', 'F', 15, u'Crédito', True],
                    #['saldo', 'F', 10, u'Diferença', False],
                ]
            elif rel_obj.tipo == 'PT':
                rel.colunas += [
                    ['numero_patrimonio', 'C', 10, u'Plaqueta', False],
                    ['patrimonio',   'C', 70, u'Patrimônio', False],
                    ['conta_debito', 'F', 10, u'Débito', True],
                    ['conta_crebito', 'F', 10, u'Crédito', True],
                    ['saldo', 'F', 10, u'Diferença', False],
                ]
            else:
                rel.colunas += [
                    ['historico',   'C', 50, u'Histórico.', False],
                    ['documento', 'C', 10, u'Nº doc.', False],
                    ['conta_debito', 'F', 15, u'Débito', True],
                    ['conta_crebito', 'F', 15, u'Crédito', True],
                    ['saldo', 'F', 10, u'Diferença', False],
                ]

            rel.monta_detalhe_automatico(rel.colunas)
            
            if rel_obj.tipo in ['FG','PD','PF']:                                
                rel.grupos = [
                   ['holerite', u'Holetite', False],
                ]                
                rel.monta_grupos(rel.grupos)

            rel.band_page_header.elements[-1].text = rel_obj.company_id.name + u' - DATA ' + formata_data(rel_obj.data_inicial) + u' - ' + formata_data(rel_obj.data_final)
            rel.band_page_header.height += 10

            nome_rel = u''
            if rel_obj.diario_conta_id:
                rel.band_page_header.elements[-1].text += u'<br/>CONTA CONTÁBIL: ' '[' + str(rel_obj.diario_conta_id.codigo) + '] ' + rel_obj.diario_conta_id.codigo_completo + ' ' + rel_obj.diario_conta_id.nome
                nome_rel =  rel_obj.diario_conta_id.nome.replace(' ', '_').replace('/', '_')
            else:
                rel.band_page_header.elements[-1].text += u'<br/>TODAS AS CONTAS GERADAS'


            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome_diario': 'conferencia_importacao_' + nome_rel + '_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo_diario': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True
    
    def gera_relatorio_conferencia_sintetico(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            if not rel_obj.item_ids:
                return {}

            sql = """
                select 
                    l.data_lancamento,
                    '[' || coalesce(f.codigo, 0) || '] ' || coalesce(f.nome,'') as nome_conta,                                        
                    case
                    when l.tipo = 'D' then
                    sum(cast(l.valor as numeric(18,2)))
                    else
                    0 end as valor_debito,
                    case
                    when l.tipo = 'C' then
                    sum(cast(l.valor as numeric(18,2)))
                    else
                    0 end as valor_credito
                from
                    lote_lancamento_importacao l
                    join finan_conta f on f.id = l.conta
                    left join hr_payslip h on h.id = l.slip_id
                    
                where
                l.lote_id = """ + str(rel_obj.id)

            if rel_obj.diario_conta_id:
                sql += """
                        and l.conta = """ + str(rel_obj.diario_conta_id.id)

            sql += """
                group by 
                    l.data_lancamento,
                    f.codigo,
                    f.nome,                    
                    l.tipo                                    
            
                order by
                    l.data_lancamento,                                      
                    l.tipo desc,
                    f.nome;"""
                                
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            saldo = D(0)
            for data_lancamento, nome_conta, conta_debito, conta_crebito in dados:
                linha = DicionarioBrasil()
                linha['data_lancamento'] = formata_data(data_lancamento)
                linha['nome_conta'] =  nome_conta                                                            
                linha['conta_debito'] = D(conta_debito)
                linha['conta_crebito'] = D(conta_crebito)
                saldo += conta_debito - conta_crebito
                linha['saldo'] = saldo
                linhas.append(linha)


            rel = FinanRelatorioAutomaticoRetrato()
            rel.cpc_minimo_detalhe = 4.0
            rel.title = u'Conferência de Importação Folha Sintético'
            
            rel.colunas = [
                ['data_lancamento','D', 10, u'Data', False],
                ['nome_conta', 'C', 35, u'Conta Contábil', False],                                
                ['conta_debito', 'F', 15, u'Débito', True],
                ['conta_crebito', 'F', 15, u'Crédito', True],
                ['saldo', 'F', 10, u'Diferença', False],
            ]  
            
            rel.monta_detalhe_automatico(rel.colunas)            
                                    
            rel.band_page_header.elements[-1].text = rel_obj.company_id.name + u' - DATA ' + formata_data(rel_obj.data_inicial) + u' - ' + formata_data(rel_obj.data_final)
            rel.band_page_header.height += 10
            
            nome_rel = u''
            if rel_obj.diario_conta_id:
                rel.band_page_header.elements[-1].text += u'<br/>CONTA CONTÁBIL: ' '[' + str(rel_obj.diario_conta_id.codigo) + '] ' + rel_obj.diario_conta_id.codigo_completo + ' ' + rel_obj.diario_conta_id.nome
                nome_rel =  rel_obj.diario_conta_id.nome.replace(' ', '_').replace('/', '_')
            else:
                rel.band_page_header.elements[-1].text += u'<br/>TODAS AS CONTAS GERADAS'

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome_diario': 'conferencia_importacao_sintetico' + nome_rel + '_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo_diario': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True


    def gera_relatorio_inconsistencia(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        lote_obj = self.browse(cr, uid, id)

        rel = Report(u'Relatório de Inconsistência Partidad', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'sped_relatorio_conferencia_sempartida.jrxml')
        rel.parametros['LOTE_ID'] = lote_obj.id
        nome_rel = u'Inconsistencia_' + str(agora())[:10].replace(' ','_' ).replace('-','_') + '.pdf'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'lote.contabilidade'), ('res_id', '=', lote_obj.id), ('name', '=', nome_rel)])
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome_rel,
            'datas_fname': nome_rel,
            'res_model': 'lote.contabilidade',
            'res_id': lote_obj.id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True


lote_contabilidade()


class lote_contabilidade_item(osv.Model):
    _description = u'Lote Contabilidade Item'
    _name = 'lote.contabilidade.item'
    _rec_name = 'codigo'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            res[obj.id] = obj.id

        return res

    _columns = {
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=False, select=True),
        'lote_id': fields.many2one('lote.contabilidade', u' Nº Lote', ondelete='cascade'),
        'company_id': fields.many2one('res.company', u'Empresa', ondelete='restrict'),
        'cnpj_cpf': fields.char(u'CNPJ',size=18),
        'documento_id': fields.many2one('sped.documento', u'Documento fiscal', ondelete='restrict'),
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento financeiro', ondelete='restrict'),
        'slip_id': fields.many2one('hr.payslip', u'Holerite', ondelete='restrict'),
        'patrimonio_id': fields.many2one('account.asset.asset', u'Patrimônio', ondelete='restrict'),
        'data': fields.date(u'Data'),
        'conta_credito_id': fields.many2one('finan.conta', u'Conta creditada', ondelete='restrict'),
        'codigo_reduzido_credito': fields.related('conta_credito_id', 'codigo', type='char', string=u'Cód. Reduz. crédito'),
        'conta_debito_id': fields.many2one('finan.conta', u'Conta debitada', ondelete='restrict'),
        'codigo_reduzido_debito': fields.related('conta_debito_id', 'codigo', type='char', string=u'Cód. Reduz. débito'),
        'valor': fields.float(u'Valor'),
        'codigo_historico': fields.char(u'Cód. Histórico', size=2048),
        'historico': fields.char(u'Complemento', size=2048),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', ondelete='restrict'),
    }


lote_contabilidade_item()

class lote_holerite_sempartida(osv.Model):
    _description = u'Holerite não contabilizado'
    _name = 'lote.holerite.sempartida'

    _columns = {
        'lote_id': fields.many2one('lote.contabilidade', u' Nº Lote', ondelete='cascade'),
        'slip_id': fields.many2one('hr.payslip', u'Holerite', ondelete='restrict'),
        'tipo': fields.related('slip_id', 'tipo', type='char', string=u'Tipo'),
        'date_from': fields.related('slip_id', 'date_from', type='date', string=u'Do dia', store=True),
        'date_to': fields.related('slip_id', 'date_to', type='date', string=u'Para dia', store=True),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),
        'company_id': fields.related('slip_id', 'company_id',  type='many2one', relation='res.company', string=u'Empresa', store=True),
    }


lote_holerite_sempartida()
