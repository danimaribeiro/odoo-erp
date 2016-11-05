# -*- encoding: utf-8 -*-

import os
import base64
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora
from finan.wizard.relatorio import *
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta
from relatorio import *
from finan.wizard.finan_relatorio import Report
from integra_rh.models.hr_jornada import float_time

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)

class assistencia_relatorio(osv.osv_memory):
    _name = 'assistencia.relatorio'
    _description = u'Relatórios Assistência Técnica'
    _rec_name = 'nome'

    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'data': fields.date(u'Data do Arquivo'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),        
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),        
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'assistencia.relatorio', context=c),
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
        'formato': 'pdf',
    }

    def gera_ordem_servico(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            sql = """
            select  
                rp.name as empresa,
                tec.name || ' ' || et.nome as tecnico_etapa,
                os.numero,
                cli.name as cliente,
                
                sum(coalesce((select sum(vr_total)
                from ordem_servico_produto osp
                join product_product pp on pp.id = osp.product_id
                join product_template pt on pt.id = pp.product_tmpl_id
                where osp.os_id = os.id
                and pt.type = 'service'
                ), 0)) as valor_servico,
                
                sum(coalesce((select sum(vr_total)
                from ordem_servico_produto osp
                join product_product pp on pp.id = osp.product_id
                join product_template pt on pt.id = pp.product_tmpl_id
                where osp.os_id = os.id
                and pt.type != 'service'
                ), 0)) as valor_produto
                
                
            from ordem_servico os
                join res_users tec on tec.id = os.tecnico_id
                join res_partner cli on cli.id = os.partner_id
                join ordem_servico_etapa et on et.id = os.etapa_id
                join res_company c on c.id = os.company_id
                join res_partner rp on rp.id = c.partner_id
                
            where
                os.company_id = {company_id}
                and os.data between '{data_inicial}' and '{data_final}'
                
            group by 
                rp.name,
                2,
                os.numero,
                cli.name
                
            order by 
                rp.name, 2, cli.name"""
                
            filtro = {
                'data_inicial': rel_obj.data_inicial,
                'data_final': rel_obj.data_final,
                'company_id': rel_obj.company_id.id
            }
            
            cr.execute(sql.format(**filtro))
            dados = cr.fetchall()
            
            linhas = []
            for empresa, tecnico_etapa, numero, cliente, valor_servico, valor_produto in dados:                
                linha = DicionarioBrasil()
                linha['empresa'] = empresa                
                linha['tecnico_etapa'] = tecnico_etapa                                
                linha['numero'] = numero
                linha['cliente'] = cliente
                linha['valor_servico'] = D(valor_servico)
                linha['valor_produto'] = D(valor_produto)                
                linhas.append(linha)

            if not linhas:
                raise osv.except_osv(u'Aviso!', u'Não há dados para impressão!')

            rel = FinanRelatorioAutomaticoRetrato()
            rel.cpc_minimo_detalhe = 3.0

            rel.title = u'Relatório Ordem de Serviço'

            rel.colunas = [
                ['numero', 'I', 10, u'Número', False],
                ['cliente', 'C', 40, u'Cliente', False],                
                ['valor_servico', 'F', 10, u'Vlr. Serviços', True],
                ['valor_produto', 'F', 10, u'Vlr. Produtos', True],                
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['tecnico_etapa', u'Técnico/Etapa:', False],                
            ]
            rel.monta_grupos(rel.grupos)

            rel.band_page_header.elements[-1].text = u'Empresa ' + rel_obj.company_id.name + ' - ' 
            rel.band_page_header.elements[-1].text += formata_data(rel_obj.data_inicial) + u' a ' + formata_data(rel_obj.data_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'Assistencia_Ordem_Servico.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)
            
    def gera_tempo_trabalhado(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            sql = """
            select  
                rp.name as empresa,
                tec.name tecnico,
                os.numero,
                cli.name as cliente,                
                float_time(sum(coalesce((select sum(cast(EXTRACT(EPOCH FROM hora_final-hora_inicial)/3600 as numeric))
                from ordem_servico_cronometro osc                
                where osc.os_id = os.id 
                and osc.tecnico_id = os.tecnico_id                  
                ), 0))) as valor_tempo    
                                
            from ordem_servico os
                join res_users tec on tec.id = os.tecnico_id
                join res_partner cli on cli.id = os.partner_id
                join ordem_servico_etapa et on et.id = os.etapa_id
                join res_company c on c.id = os.company_id
                join res_partner rp on rp.id = c.partner_id
                
            where
                os.company_id = {company_id}
                and os.data between '{data_inicial}' and '{data_final}'
                
            group by 
                rp.name,
                2,
                os.numero,
                cli.name
                
            order by 
                rp.name, 2, cli.name"""
                
            filtro = {
                'data_inicial': rel_obj.data_inicial,
                'data_final': rel_obj.data_final,
                'company_id': rel_obj.company_id.id
            }
            
            cr.execute(sql.format(**filtro))
            dados = cr.fetchall()
            
            linhas = []
            for empresa, tecnico, numero, cliente, valor_tempo in dados:                
                linha = DicionarioBrasil()
                linha['empresa'] = empresa                
                linha['tecnico'] = tecnico                                
                linha['numero'] = numero
                linha['cliente'] = cliente
                linha['valor_tempo'] = str(valor_tempo)                                
                linhas.append(linha)

            if not linhas:
                raise osv.except_osv(u'Aviso!', u'Não há dados para impressão!')

            rel = FinanRelatorioAutomaticoRetrato()
            rel.cpc_minimo_detalhe = 3.0

            rel.title = u'Relatório Tempo Trabalhado'

            rel.colunas = [
                ['numero', 'I', 10, u'Nº OS', False],
                ['cliente', 'C', 40, u'Cliente', False],                
                ['valor_tempo', 'C', 20, u'Tempo Gasto', False],                                
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['tecnico', u'Técnico:', False],                
            ]
            rel.monta_grupos(rel.grupos)

            rel.band_page_header.elements[-1].text = u'Empresa ' + rel_obj.company_id.name + ' - ' 
            rel.band_page_header.elements[-1].text += formata_data(rel_obj.data_inicial) + u' a ' + formata_data(rel_obj.data_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'Assistencia_Tempo_gasto.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)
    

assistencia_relatorio()


