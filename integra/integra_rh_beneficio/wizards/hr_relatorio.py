# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora
import base64
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado
from relatorio import *
from finan.wizard.finan_relatorio import Report
import csv
from pybrasil.base import DicionarioBrasil


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')



class hr_relatorio(osv.osv_memory):
    _name = 'hr.relatorio'
    _inherit = 'hr.relatorio'

    _columns = {        
        'partner_id': fields.many2one('res.partner', u'Fornecedor'),
    }
    
    _defaults = {              
    }
    
    def gera_relatorio_linhas_ativa_inativa(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for rel_obj in self.browse(cr, uid, ids):
            
            dados_filtro = {
                'data_agora': str(agora()),
            }

            if rel_obj.tipo == 'T':
                dados_filtro['tipo'] = '%'

            elif rel_obj.tipo == 'D':
                dados_filtro['tipo'] = 'D'

            elif rel_obj.tipo == 'F':
                dados_filtro['tipo'] = 'F'

            sql = """
                select 
                    lt.nome as nome,
                    rp.name as fornecedor,
                    sr.name as rubrica,
                    sm.nome as municipio,
                    lt.valor,
                    lt.data_validade,
                    case
                    when lt.data_validade < '{data_agora}' then
                    'Inativa'
                    else
                    'Ativa'
                    end as situacao 
                from hr_linha_transporte lt
                left join res_partner rp on rp.id = lt.partner_id
                left join hr_salary_rule sr on sr.id = lt.rule_id
                left join sped_municipio sm on sm.id = lt.municipio_id"""
                    
            if rel_obj.partner_id:
                sql += """
                    where lt.partner_id = """ + str(rel_obj.partner_id.id)

            sql += """
                order by 
                    rp.name,
                    lt.data_validade,
                    lt.nome; """
                    
            cr.execute(sql.format(**dados_filtro))

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for nome, fornecedor, rubrica, municipio, valor, data_validade, situacao in dados:
                linha = DicionarioBrasil()
                linha['nome'] = nome
                linha['fornecedor'] = fornecedor
                linha['rubrica'] = rubrica
                linha['municipio'] = municipio                
                linha['data_inicial'] = data_validade
                linha['valor'] = valor
                linha['situacao'] = situacao
                linhas.append(linha)


            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relatório Linha de Transporte'
            rel.colunas = [
                ['nome', 'C', 30, u'Nome', False],                
                ['rubrica', 'C', 30, u'Rúbrica', False],
                ['municipio', 'C', 30, u'Município', False],
                ['data_validade', 'D', 10, u'Data Validade ', False],
                ['valor', 'F', 10, u'Valor', False],
                ['situacao', 'C', 10, u'Situação', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['fornecedor', u'Fornecedor', False],
            ]
            rel.monta_grupos(rel.grupos)

            #company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            #rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': u'linhas_transporte_ativa_inativa.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

hr_relatorio()