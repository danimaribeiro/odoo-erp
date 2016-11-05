# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from jasper_reports.JasperReports import *
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from relatorio import *
from pybrasil.valor.decimal import Decimal as D
from finan.wizard.finan_relatorio import Report

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class finan_relatorio(osv.osv_memory):
    _inherit = 'finan.relatorio'

    _columns = {

    }

    _defaults = {

    }

    def gera_relatorio_cheque(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):

            bancos_ids = []

            if len(rel_obj.res_partner_bank_ids):

                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)


            sql_relatorio = """
                select
                    rp.name as empresa,
                    to_char(fc.data,'MM/YYYY') as mes,
                    fc.data,
                    fc.numero_cheque,
                    b.descricao as banco,
                    fc.agencia || '-' || fc.conta_corrente,
                    fc.nome_titular,
                    fc.data_pre_datado,
                    fc.valor,
                    case
                        when fc.situacao = 'RB' then 'Recebido  '
                        when fc.situacao = 'DF' then 'Depositado'
                        else 'Devolvido'
                    end as situacao

                from finan_cheque fc
                    join res_partner_bank b on b.id = fc.res_partner_bank_id
                    join res_company c on c.id = fc.company_id
                    join res_partner rp on rp.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id"""

            if rel_obj.company_id:
                sql_relatorio += """
                where
                    (
                        c.id = """ + str(rel_obj.company_id.id) + """
                        or cc.id = """ + str(rel_obj.company_id.id) + """
                        or ccc.id = """ + str(rel_obj.company_id.id) + """
                    )"""
                if len(bancos_ids) > 0:

                    sql_relatorio += """
                        and fc.res_partner_bank_id in """  +  str(tuple(bancos_ids)).replace(',)', ')')
                else:
                    sql_relatorio += """
                        and b.state = 'Caixa'""" 
                        
            elif len(bancos_ids) > 0:
                    sql_relatorio += """
                    where
                        fc.res_partner_bank_id in """  +  str(tuple(bancos_ids)).replace(',)', ')')
            else:
                sql_relatorio += """
                    where b.state = 'Caixa'""" 

            sql_relatorio += """
                order by
                    rp.name,
                    b.descricao,
                    fc.data;
                """

            #print(sql_relatorio)
            cr.execute(sql_relatorio)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            for empresa, mes, data, numero_cheque, banco, conta_corrente, nome_titular, data_pre_datado, valor, situacao in dados:

                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['mes'] = mes
                linha['data'] = formata_data(data)
                linha['banco'] = banco
                linha['numero_cheque'] = numero_cheque
                linha['conta_corrente'] = conta_corrente
                linha['nome_titular'] = nome_titular
                linha['data_pre_datado'] = data_pre_datado
                linha['valor'] = valor
                linha['situacao'] = situacao

                linhas.append(linha)

            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Cheques'

            rel.colunas = [
                ['data_pre_datado', 'D', 10, u'Dt.Vencimento', False],
                ['numero_cheque','C',10, u'Nº Cheque', False],
                ['conta_corrente', 'C', 20, u'C.Corrente', False],
                ['nome_titular', 'C', 30, u'Titular', False],
                ['data', 'D', 10, u'Data', False],
                ['situacao', 'C', 10, u'Situação', False],
                ['valor', 'F', 10, u'Valor', True],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
                ['banco', u'Conta Bancária', False],
                ['mes', u'Cheques', False],
            ]
            rel.monta_grupos(rel.grupos)

            if rel_obj.company_id.partner_id:
                rel.band_page_header.elements[-1].text = u'Empresa: ' + rel_obj.company_id.partner_id.name
                nome = 'cheque_' + rel_obj.company_id.partner_id.name + '.pdf'
            else:
                rel.band_page_header.elements[-1].text = u'Empresa: TODAS'
                nome = 'cheques_todas_empresas.pdf'

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': nome,
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)


finan_relatorio()
