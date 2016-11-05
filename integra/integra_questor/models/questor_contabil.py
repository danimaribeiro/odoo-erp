# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.data import parse_datetime, formata_data, agora, hoje
from pybrasil.valor import formata_valor
from pybrasil.telefone.telefone import separa_fone
from integracao_questor import integracao_questor, integracao_questor_fiscal_A, integracao_questor_fiscal_B, integracao_questor_fiscal_C, integracao_questor_fiscal_D, integracao_questor_fiscal_E, integracao_questor_fiscal_F, integracao_questor_fiscal_G, integracao_questor_fiscal_H, integracao_questor_fiscal_J, integracao_questor_fiscal_K, integracao_questor_fiscal_KI, integracao_questor_fiscal_L, integracao_questor_fiscal_L, integracao_questor_fiscal_M, integracao_questor_fiscal_N, integracao_questor_fiscal_O, integracao_questor_fiscal_R
import base64
import os
from pybrasil.inscricao import limpa_formatacao
from sped.constante_tributaria import *
from pybrasil.base import DicionarioBrasil
from finan.wizard.relatorio import *
from pybrasil.valor.decimal import Decimal as D


class questor_contabilidade(osv.Model):
    _description = u'Exportação Contabilidade Questor'
    _name = 'questor.contabilidade'
    _rec_name = 'nome'
    _order = 'data_inicial desc, data_final desc'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for exp_obj in self.browse(cr, uid, ids):
            res[exp_obj.id] = exp_obj.id

        return res

    _columns = {
        'tipo': fields.selection([('D', u'Documentos fiscais'), ('F', u'Financeiro'), ('G', u'Geral'), ('FG', u'Folha Pagamento')], u'Tipo'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'arquivo_texto': fields.text(u'Arquivo'),
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=False, select=True),
        'item_ids': fields.one2many('questor.contabilidade.item', 'arquivo_id', string=u'Itens enviados'),
        'emissao': fields.selection(TIPO_EMISSAO_TODAS, u'Tipo de emissão'),
        'diario_conta_id': fields.many2one('finan.conta', u'Conta para o razão'),
        'nome_diario': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo_diario': fields.binary(u'Arquivo', readonly=True),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio', context=c),
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        'emissao': '%',
    }

    def _exporta_documentos_fiscais(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('questor.contabilidade.item')

        arquivo_texto = u''
        for export_obj in self.browse(cr, uid, ids):
            cnpj = export_obj.company_id.partner_id.cnpj_cpf
            cnpj = cnpj[:10]
            print(cnpj)

            sql = """
            select
                sd.id

            from
                sped_documento sd
                join res_company c on c.id = sd.company_id
                join res_partner p on p.id = c.partner_id

            where
                    p.cnpj_cpf like '{cnpj}%'
                and sd.situacao in ('00','01')
                and sd.emissao like '{emissao}'
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


            order by
                sd.data_emissao_brasilia,
                sd.emissao,
                sd.serie,
                sd.numero;
            """.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,
                cnpj=cnpj, emissao=export_obj.emissao or '%')

            cr.execute(sql)

            dados = cr.fetchall()

            if not dados:
                return arquivo_texto

            documento_ids = []
            for ret in dados:
                documento_ids.append(ret[0])

            documento_objs = self.pool.get('sped.documento').browse(cr, 1, documento_ids)

            for documento_obj in documento_objs:
                partida_objs = documento_obj.get_partidas_dobradas()

                for partida_obj in partida_objs:
                    export = integracao_questor()
                    export.cnpj_cpf = limpa_formatacao(documento_obj.company_id.partner_id.cnpj_cpf)
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

                    if partida_obj.codigo_historico:
                        export.codigo_historico = partida_obj.codigo_historico

                    historico = u''
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
                        'arquivo_id': export_obj.id,
                        'documento_id': documento_obj.id,
                        'data': str(export.data_lancamento),
                        'valor': partida_obj.valor,
                        'historico': export.complemento_historico,
                        'codigo_historico': str(export.codigo_historico),
                    }

                    if partida_obj.conta_debito_id:
                        dados_item['conta_debito_id'] = partida_obj.conta_debito_id.id

                    if partida_obj.conta_credito_id:
                        dados_item['conta_credito_id'] = partida_obj.conta_credito_id.id

                    item_pool.create(cr, uid, dados_item)

        return arquivo_texto

    def _exporta_folha_pagamento(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('questor.contabilidade.item')

        arquivo_texto = u''
        for export_obj in self.browse(cr, uid, ids):
            cnpj = export_obj.company_id.partner_id.cnpj_cpf
            cnpj = cnpj[:10]
            print(cnpj)

            sql = """
                select
                    h.id

                from
                    hr_payslip h
                    join res_company c on c.id = h.company_id
                    join res_partner rp on rp.id = c.partner_id

                where
                    rp.cnpj_cpf like '{cnpj}%'
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

            """.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,
                cnpj=cnpj)

            print(sql)

            cr.execute(sql)

            dados = cr.fetchall()

            if not dados:
                return arquivo_texto

            documento_ids = []
            for ret in dados:
                documento_ids.append(ret[0])

            documento_objs = self.pool.get('hr.payslip').browse(cr, uid, documento_ids)

            partidas_acumuladas = {}
            for holerite_obj in documento_objs:
                partida_objs = holerite_obj.get_partidas_dobradas_folha()

                for partida_obj in partida_objs:
                    chave_acumulada = str(holerite_obj.company_id.partner_id.cnpj_cpf)
                    chave_acumulada += '|' + str(partida_obj.data)
                    chave_acumulada += '|' + str(partida_obj.conta_debito_id.codigo or partida_obj.conta_debito_id.id)
                    chave_acumulada += '|' + str(partida_obj.conta_credito_id.codigo or partida_obj.conta_credito_id.id)
                    print(chave_acumulada)
                    if chave_acumulada in partidas_acumuladas:
                        partidas_acumuladas[chave_acumulada].valor += partida_obj.valor
                    else:
                        partidas_acumuladas[chave_acumulada] = partida_obj


            for chave_acumulada in partidas_acumuladas:
                partida_obj = partidas_acumuladas[chave_acumulada]

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
                    'arquivo_id': export_obj.id,
                    'data': str(export.data_lancamento),
                    'valor': partida_obj.valor,
                    'historico': export.complemento_historico,
                    'codigo_historico': str(export.codigo_historico),
                }

                if partida_obj.conta_debito_id:
                    dados_item['conta_debito_id'] = partida_obj.conta_debito_id.id

                if partida_obj.conta_credito_id:
                    dados_item['conta_credito_id'] = partida_obj.conta_credito_id.id

                item_pool.create(cr, uid, dados_item)




        return arquivo_texto


    def _exporta_financeiro(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('questor.contabilidade.item')

        arquivo_texto = u''
        for export_obj in self.browse(cr, uid, ids):
            cnpj = export_obj.company_id.partner_id.cnpj_cpf
            cnpj = cnpj[:10]

            sql = """
            select
                fl.id

            from
                finan_lancamento fl
                --join res_company c on c.id = fl.company_id
                --join res_partner p on p.id = c.partner_id
                join res_partner_bank b on fl.res_partner_bank_id = b.id
                join res_partner p on p.id = b.partner_id

            where
                (
                    (fl.data is not null and fl.data between '{data_inicial}' and '{data_final}')
                 or
                    (fl.data is null and fl.data_quitacao is not null and fl.data_quitacao between '{data_inicial}' and '{data_final}')
                )
                and p.cnpj_cpf like '{cnpj}%'
                and fl.tipo in ('E', 'S', 'T')

            order by
                fl.data_quitacao, fl.tipo;
            """.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)
            #print(sql)
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
                --join res_company c on c.id = l.company_id
                --join res_partner p on p.id = c.partner_id
                join res_partner_bank b on fl.res_partner_bank_id = b.id
                join res_partner p on p.id = b.partner_id

            where
                (
                    (fl.data is not null and fl.data between '{data_inicial}' and '{data_final}')
                 or
                    (fl.data is null and fl.data_quitacao is not null and fl.data_quitacao between '{data_inicial}' and '{data_final}')
                )
                and p.cnpj_cpf like '{cnpj}%'
                and fl.tipo in ('PP', 'PR')
                and l.tipo not in ('LR', 'LP')

            order by
                fl.data_quitacao, fl.tipo;
            """.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)

            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()

            for ret in dados:
                lancamento_ids.append(ret[0])

            #
            # Contratos a contabilizar
            #
            sql = """
            select
                fl.id

            from
                finan_lancamento fl
                join res_company c on c.id = fl.company_id
                join finan_contrato fc on fc.id = fl.contrato_id and fc.modelo_partida_dobrada_id is not null

            where
                (
                    (fl.data is not null and fl.data_documento between '{data_inicial}' and '{data_final}')
                 or
                    (fl.data is null and fl.data_quitacao is not null and fl.data_quitacao between '{data_inicial}' and '{data_final}')
                )
                and c.cnpj_cpf like '{cnpj}%'
                and fl.tipo in ('P', 'R')

            order by
                fl.data_documento, fl.tipo;
            """.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)

            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()

            for ret in dados:
                lancamento_ids.append(ret[0])

            #
            # Duplicatas e provisões a receber
            #
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
                and c.cnpj_cpf like '{cnpj}%'
                and fl.tipo = 'R'
                and (fl.provisionado = false or fl.provisionado = null)
                and so.modelo_partida_dobrada_id is null;
            """.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)

            print(sql)
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
                join sped_modelo_partida_dobrada mpd on mpd.id = d.modelo_partida_dobrada_receber_id
                left join sped_documento sd on sd.id = fl.sped_documento_id
                left join sped_operacao so on so.id = sd.operacao_id
                left join finan_contrato fc on fc.id = fl.contrato_id

            where
                fl.data_documento between '{data_inicial}' and '{data_final}'
                and c.cnpj_cpf like '{cnpj}%'
                and fl.tipo = 'P'
                and (fl.provisionado = false or fl.provisionado = null)
                and so.modelo_partida_dobrada_id is null;
            """.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)

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
                and c.cnpj_cpf like '{cnpj}%'
                and fl.tipo in ('P', 'R')
                and (
                    (fl.tipo = 'R' and mb.modelo_partida_dobrada_receber_id is not null)
                    or
                    (fl.tipo = 'P' and mb.modelo_partida_dobrada_pagar_id is not null)
                )

            order by
                fl.data_quitacao, fl.tipo;
            """.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)

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
                --join res_partner_bank b on fl.res_partner_bank_id = b.id
                --join res_partner p on p.id = b.partner_id

            where
                (
                    (fl.data is not null and fl.data between '{data_inicial}' and '{data_final}')
                 or
                    (fl.data is null and fl.data_quitacao is not null and fl.data_quitacao between '{data_inicial}' and '{data_final}')
                )
                and p.cnpj_cpf like '{cnpj}%'
                and fl.tipo in ('PP', 'PR')
                and l.tipo in ('LR', 'LP')
                and fl.lote_id is null
                and (l.provisionado = false or l.provisionado = null)

            order by
                l.data_quitacao, l.tipo;
            """
            sql = sql.format(data_inicial=export_obj.data_inicial, data_final=export_obj.data_final,cnpj=cnpj)

            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()

            for ret in dados:
                lancamento_ids.append(ret[0])


            if len(lancamento_ids) == 0:
                return arquivo_texto

            lancamento_objs = self.pool.get('finan.lancamento').browse(cr, uid, lancamento_ids)

            for lancamento_obj in lancamento_objs:
                if lancamento_obj.lancamento_id.id == 15089074:
                    print(lancamento_obj.id)
                partida_objs = lancamento_obj.get_partidas_dobradas()

                #print(partida_objs)

                for partida_obj in partida_objs:
                    export = integracao_questor()
                    #export.cnpj_cpf = limpa_formatacao(lancamento_obj.company_id.partner_id.cnpj_cpf)

                    if lancamento_obj.data_baixa:
                        export.data_lancamento = parse_datetime(lancamento_obj.data_baixa).date()
                        export.cnpj_cpf = limpa_formatacao(lancamento_obj.company_id.partner_id.cnpj_cpf)
                    elif lancamento_obj.data:
                        export.data_lancamento = parse_datetime(lancamento_obj.data).date()
                        export.cnpj_cpf = limpa_formatacao(lancamento_obj.res_partner_bank_id.partner_id.cnpj_cpf)
                    elif lancamento_obj.data_quitacao:
                        export.data_lancamento = parse_datetime(lancamento_obj.data_quitacao).date()
                        export.cnpj_cpf = limpa_formatacao(lancamento_obj.res_partner_bank_id.partner_id.cnpj_cpf)
                    else:
                        export.data_lancamento = parse_datetime(lancamento_obj.data_documento).date()
                        export.cnpj_cpf = limpa_formatacao(lancamento_obj.company_id.partner_id.cnpj_cpf)

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

                    if lancamento_obj.tipo in ['S', 'E', 'T', 'R', 'P']:
                        historico += lancamento_obj.numero_documento or u's/nº'
                    else:
                        historico += lancamento_obj.lancamento_id.numero_documento or u's/nº'
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
                        'arquivo_id': export_obj.id,
                        'data': str(export.data_lancamento),
                        'lancamento_id': lancamento_obj.id,
                        'conta_debito_id': partida_obj.conta_debito_id.id,
                        'conta_credito_id': partida_obj.conta_credito_id.id,
                        'valor': partida_obj.valor,
                        'historico': export.complemento_historico,
                        'codigo_historico': str(export.codigo_historico),
                    }
                    item_pool.create(cr, uid, dados_item)

        return arquivo_texto

    def gera_exportacao(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        arquivo_texto = u''
        for export_obj in self.browse(cr, uid, ids):
            cr.execute('delete from questor_contabilidade_item where arquivo_id = {id}'.format(id=export_obj.id))

            if export_obj.tipo in ['D', 'G']:
                arquivo_texto += self._exporta_documentos_fiscais(cr, uid, ids, context)

            if export_obj.tipo in ['F', 'G']:
                arquivo_texto += self._exporta_financeiro(cr, uid, ids, context)

            if export_obj.tipo == 'FG':
                arquivo_texto += self._exporta_folha_pagamento(cr, uid, ids, context)

            cnpj = limpa_formatacao(export_obj.company_id.partner_id.cnpj_cpf)
            nome_arquivo =  cnpj + '_' + str(hoje()) + u'.txt'

            dados = {
                'nome': nome_arquivo,
                'arquivo_texto': arquivo_texto,
                'arquivo': base64.encodestring(arquivo_texto),
            }
            export_obj.write(dados)


    def gera_relatorio_diario(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        item_pool = self.pool.get('questor.contabilidade.item')
        historico_pool = self.pool.get('finan.historico')

        for rel_obj in self.browse(cr, uid, ids):
            if not rel_obj.diario_conta_id:
                continue

            item_ids = item_pool.search(cr, uid, [('arquivo_id', '=', rel_obj.id), '|', ('conta_credito_id', '=', rel_obj.diario_conta_id.id), ('conta_debito_id', '=', rel_obj.diario_conta_id.id)], order='data')

            if len(item_ids) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Diário - ' + rel_obj.diario_conta_id.nome

            linhas = []
            for item_obj in item_pool.browse(cr, uid, item_ids):
                if 'CLIE' in rel_obj.diario_conta_id.nome.upper():
                    if item_obj.conta_credito_id.id == rel_obj.diario_conta_id.id:
                        if item_obj.documento_id.id:
                            continue

                if 'FORN' in rel_obj.diario_conta_id.nome.upper():
                    if item_obj.conta_debito_id.id == rel_obj.diario_conta_id.id:
                        if item_obj.documento_id.id:
                            continue

                linha = DicionarioBrasil()

                linha['data'] = formata_data(item_obj.data)
                linha['numero_documento'] = ''
                linha['clifor'] = ''
                partner_obj = None

                if item_obj.documento_id:
                    linha['clifor'] = item_obj.documento_id.partner_id.name
                    linha['numero_documento'] = formata_valor(item_obj.documento_id.numero, casas_decimais=0)

                elif item_obj.lancamento_id:
                    if item_obj.lancamento_id.tipo in ['P', 'R', 'E', 'S', 'T']:
                        partner_obj = item_obj.lancamento_id.partner_id
                        linha['numero_documento'] = item_obj.lancamento_id.numero_documento
                        if item_obj.lancamento_id.partner_id:
                            linha['clifor'] = item_obj.lancamento_id.partner_id.name

                    elif item_obj.lancamento_id.lancamento_id.tipo in ['P', 'R']:
                            linha['numero_documento'] = item_obj.lancamento_id.lancamento_id.numero_documento
                            if item_obj.lancamento_id.lancamento_id.partner_id:
                                linha['clifor'] = item_obj.lancamento_id.lancamento_id.partner_id.name

                    elif item_obj.lancamento_id.tipo in ['LP', 'LR']:
                            linha['numero_documento'] = item_obj.lancamento_id.numero_documento
                            if item_obj.lancamento_id.partner_id:
                                linha['clifor'] = item_obj.lancamento_id.partner_id.name

                linha['historico'] = item_obj.codigo_historico or ''
                linha['complemento'] = item_obj.historico or ''

                if item_obj.conta_debito_id.id == rel_obj.diario_conta_id.id:
                    contrapartida = ''
                    if item_obj.conta_credito_id:
                        contrapartida = item_obj.conta_credito_id.codigo_completo or ''
                        contrapartida += ' - '
                        contrapartida += item_obj.conta_credito_id.nome or ''
                    linha['contrapartida'] = contrapartida
                    linha['debito'] = D(item_obj.valor)
                    linha['credito'] = D(0)
                else:
                    contrapartida = ''
                    if item_obj.conta_debito_id:
                        contrapartida = item_obj.conta_debito_id.codigo_completo or ''
                        contrapartida += ' - '
                        contrapartida += item_obj.conta_debito_id.nome or ''
                    linha['contrapartida'] = contrapartida
                    linha['debito'] = D(0)
                    linha['credito'] = D(item_obj.valor)
                linhas.append(linha)

            rel.colunas = [
                ['clifor', 'C', 60, 'Cliente/Fornecedor', False],
                ['numero_documento', 'C', 25, u'Nº doc.', False],
                #['contrapartida', 'C', 40, u'Contrapartida', False],
                ['historico', 'C', 5, u'Hist.', False],
                ['complemento', 'C', 30, u'Histórico', False],
                ['debito', 'F', 10, u'Débito', True],
                ['credito', 'F', 10, u'Crédito', True],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['data', u'Data', False],
            ]
            rel.monta_grupos(rel.grupos)

            rel.band_page_header.elements[-1].text = rel_obj.company_id.name + u' - DATA ' + formata_data(rel_obj.data_inicial) + u' - ' + formata_data(rel_obj.data_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome_diario': 'Diario_' + rel_obj.diario_conta_id.nome.replace(' ', '_').replace('/', '_') + '_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo_diario': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True


questor_contabilidade()


class questor_contabilidade_item(osv.Model):
    _description = u'Item de Exportação Contabilidade Questor'
    _name = 'questor.contabilidade.item'

    _columns = {
        'arquivo_id': fields.many2one('questor.contabilidade', u'Arquivo'),
        'documento_id': fields.many2one('sped.documento', u'Documento fiscal'),
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento financeiro'),
        'data': fields.date(u'Data'),
        'conta_credito_id': fields.many2one('finan.conta', u'Conta creditada'),
        'codigo_reduzido_credito': fields.related('conta_credito_id', 'codigo', type='char', string=u'Cód. Reduz. crédito'),
        'conta_debito_id': fields.many2one('finan.conta', u'Conta debitada'),
        'codigo_reduzido_debito': fields.related('conta_debito_id', 'codigo', type='char', string=u'Cód. Reduz. débito'),
        'valor': fields.float(u'Valor'),
        'codigo_historico': fields.char(u'Cód. Histórico', size=2048),
        'historico': fields.char(u'Complemento', size=2048),
    }


questor_contabilidade_item()
