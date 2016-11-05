# -*- encoding: utf-8 -*-

import os, csv
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora, hoje, mes_passado, primeiro_dia_mes, ultimo_dia_mes
import base64
from finan.wizard.relatorio import *
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta
from relatorio import *
from finan.wizard.finan_relatorio import Report



DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

MESES = (
    ('1', u'janeiro'),
    ('2', u'fevereiro'),
    ('3', u'março'),
    ('4', u'abril'),
    ('5', u'maio'),
    ('6', u'junho'),
    ('7', u'julho'),
    ('8', u'agosto'),
    ('9', u'setembro'),
    ('10', u'outubro'),
    ('11', u'novembro'),
    ('12', u'dezembro'),
)

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('csv', u'XLS'),
)



class sped_ecd_relatorio(osv.osv_memory):
    _name = 'sped.ecd.relatorio'
    _description = u'Relatórios Contábeis'
    _rec_name = 'nome'

    _columns = {
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'data': fields.date(u'Data'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'conta_id': fields.many2one('finan.conta', u'Conta Contábil'),
        'ecd_conta_ids': fields.many2many('finan.conta','ecd_finan_conta', 'ecd_relatorio_id', 'conta_id', string=u'Contas Contábeis'),        
        'ecd_centrocusto_ids': fields.many2many('finan.centrocusto','ecd_finan_centrocusto', 'ecd_relatorio_id', 'centrocusto_id', string=u'Centro de Custos'),        
        'somente_cnpj': fields.boolean(u'Somente CNPJ?'),
        'somente_saldo': fields.boolean(u'Somente Contas com Saldo?'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio', context=c),
        'data_inicial': fields.date.today,
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        #'ano': lambda *args, **kwargs: mes_passado()[0],
        #'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'formato': 'pdf',
    }


    def gera_relatorio_razao(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        
        conta_ids = []
        if len(rel_obj.ecd_conta_ids):    
    
            for conta_obj in rel_obj.ecd_conta_ids:
                conta_ids.append(conta_obj.id)
                contas_nome = u'Conta Contábil: [' + str(conta_obj.codigo) + u'] ' + conta_obj.codigo_completo  + u' ' + conta_obj.nome
     
        sql_novo = """
            select
                coalesce((select r.razao_social from res_partner r where r.cnpj_cpf = l.cnpj_cpf limit 1),'') as empresa,                
                l.cnpj_cpf,
                l.data_lancamento,
                l.codigo_lancamento,
                l.conta_id,
                l.data_criacao,
                l.conta_contabil,
                l.codigo_completo,
                l.conta_reduzida,
                'Conta Contábil: [' || coalesce(l.conta_reduzida, 0) || '] ' || coalesce(l.codigo_completo,'') || ' ' || coalesce(l.conta_contabil, '') as conta_nome,
                l.vr_debito,
                l.vr_credito,
                l.historico,
                l.centro_custo,
                lt.tipo as tipo_lote,
                l.contra_partida as contra_partidada
            
            from ecd_razao_view l
            left join ecd_lancamento_contabil lc on lc.id =codigo_lancamento
            left join lote_contabilidade lt on lt.id = lc.lote_id
                        
            where
                l.data_lancamento between '{data_inicial}' and '{data_final}'"""
            
        if rel_obj.somente_cnpj:
            sql_novo += """
            and l.cnpj_cpf = '{cnpj_cpf}' """
            company_cnpj = 'es.cnpj_cpf = ' +  "'" + str(rel_obj.company_id.partner_id.cnpj_cpf) + "'"
        else:
            sql_novo += """
            and l.company_id = """ + str(rel_obj.company_id.id)
            company_cnpj = 'es.company_id = ' + str(rel_obj.company_id.id)

        if len(conta_ids) > 0:  
            sql_novo += """
            and l.conta_id in """ +  str(tuple(conta_ids)).replace(',)', ')')

        sql_novo += """
        order by
            l.codigo_completo,
            l.data_lancamento,
            l.partida_id,
            l.conta_reduzida;"""

        filtro = {
            'cnpj_cpf': str(rel_obj.company_id.partner_id.cnpj_cpf),
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
        }

        sql = sql_novo.format(**filtro)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report(u'Razão Contábil', cr, uid)
        rel.outputFormat = rel_obj.formato
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'sped_ecd_razao.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql
        rel.parametros['COMPANY_CNPJ'] = company_cnpj

        if len(conta_ids) == 1:
            rel.parametros['CONTA_ID'] = conta_ids[0]
            rel.parametros['CONTA_NOME'] = contas_nome

        pdf, formato = rel.execute()
        

        dados = {
            'nome': u'RAZAO_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + ('.') + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True
    
    def gera_relatorio_razao_centrocusto(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        
        centrocusto_ids = []
        if len(rel_obj.ecd_centrocusto_ids):    
    
            for centrocusto_obj in rel_obj.ecd_centrocusto_ids:
                centrocusto_ids.append(centrocusto_obj.id)
                centrocusto_nome = u'Centro Custo: [' + str(centrocusto_obj.codigo) + u'] ' + centrocusto_obj.nome
        
        conta_ids = []
        if len(rel_obj.ecd_conta_ids):    
    
            for conta_obj in rel_obj.ecd_conta_ids:
                conta_ids.append(conta_obj.id)
                contas_nome = u'Conta Contábil: [' + str(conta_obj.codigo) + u'] ' + conta_obj.codigo_completo  + u' ' + conta_obj.nome
     
     
        sql_novo = """
            select
                coalesce((select r.razao_social from res_partner r where r.cnpj_cpf = l.cnpj_cpf limit 1),'') as empresa,
                l.cnpj_cpf,
                l.data_lancamento,
                '[' || coalesce(cc.codigo,0) || ']' || coalesce(cc.nome,'') as nome_centrocusto,
                l.codigo_lancamento,
                l.conta_id,
                l.data_criacao,
                l.conta_contabil,
                l.codigo_completo,
                l.conta_reduzida,
                'Conta Contábil: [' || coalesce(l.conta_reduzida, 0) || '] ' || coalesce(l.codigo_completo,'') || ' ' || coalesce(l.conta_contabil, '') as  conta_nome,
                l.vr_debito,
                l.vr_credito,
                l.historico,
                l.centro_custo,
                lt.tipo as tipo_lote,
                l.contra_partida as contra_partidada

            from ecd_razao_view l
            join finan_centrocusto cc on cc.id = l.centrocusto_id
            left join ecd_lancamento_contabil lc on lc.id =codigo_lancamento
            left join lote_contabilidade lt on lt.id = lc.lote_id
                        
            where
                l.data_lancamento between '{data_inicial}' and '{data_final}'"""
            
        if rel_obj.somente_cnpj:
            sql_novo += """
            and l.cnpj_cpf = '{cnpj_cpf}' """
            company_cnpj = 'es.cnpj_cpf = ' +  "'" + str(rel_obj.company_id.partner_id.cnpj_cpf) + "'"
        else:
            sql_novo += """
            and l.company_id = """ + str(rel_obj.company_id.id)
            company_cnpj = 'es.company_id = ' + str(rel_obj.company_id.id)

        if len(centrocusto_ids) > 0:  
            sql_novo += """
            and l.centrocusto_id in """ +  str(tuple(centrocusto_ids)).replace(',)', ')')
            
        if len(conta_ids) > 0:  
            sql_novo += """
            and l.conta_id in """ +  str(tuple(conta_ids)).replace(',)', ')')

        sql_novo += """
        order by
            l.centrocusto_id,
            l.codigo_completo,
            l.data_lancamento,
            l.partida_id,
            l.conta_reduzida;"""

        filtro = {
            'cnpj_cpf': str(rel_obj.company_id.partner_id.cnpj_cpf),
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
        }

        sql = sql_novo.format(**filtro)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report(u'Razão Contábil por Centro de Custo', cr, uid)
        rel.outputFormat = rel_obj.formato
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'sped_ecd_razao_centrocusto.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql
        rel.parametros['COMPANY_CNPJ'] = company_cnpj

        if len(centrocusto_ids) == 1:
            rel.parametros['CONTA_ID'] = centrocusto_ids[0]
            rel.parametros['CONTA_NOME'] = centrocusto_nome

        pdf, formato = rel.execute()
        

        dados = {
            'nome': u'RAZAO_CENTROCUSTO_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + ('.') + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_diario(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        sql = """
        select
            coalesce((select r.razao_social from res_partner r where r.cnpj_cpf = rp.cnpj_cpf limit 1),'') as empresa,
            rp.cnpj_cpf,
            lc.data as data_lancamento,
            lc.codigo as codigo_lancamento,
            fc.id as conta_id,
            fc.data as data_criacao,
            coalesce(fc.nome, '') as conta_contabil,
            coalesce(fc.codigo_completo,'') as codigo_completo,
            coalesce(fc.codigo, 0) as conta_reduzida,
            coalesce(pt.vr_debito, 0) as vr_debito,
            coalesce(pt.vr_credito, 0) as vr_credito,
            pt.historico,
            cc.codigo as centro_custo,
            to_char(lc.data, 'MM-YYYY') as mes

        from ecd_lancamento_contabil lc
            join ecd_partida_lancamento pt on pt.lancamento_id = lc.id
            left join finan_centrocusto cc on cc.id = pt.centrocusto_id
            join finan_conta fc on fc.id = pt.conta_id
            join ecd_plano_conta ep on ep.id = fc.plano_id
            join res_company c on c.plano_id = ep.id and c.id = lc.company_id
            join res_partner rp on rp.id = c.partner_id

        where
            lc.data between '{data_inicial}' and '{data_final}'"""

        if rel_obj.somente_cnpj:
            sql += """
            and rp.cnpj_cpf = '{cnpj_cpf}' """
        else:
            sql += """
            and c.id = """ + str(rel_obj.company_id.id)

        if rel_obj.conta_id:
            sql += """
            and pt.conta_id = """ + str(rel_obj.conta_id.id)

        sql += """
        order by
            lc.data,
            lc.codigo,
            fc.codigo_completo;"""

        filtro = {
            'cnpj_cpf': str(rel_obj.company_id.partner_id.cnpj_cpf),
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
        }

        sql = sql.format(**filtro)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report(u'Diário Contábil', cr, uid)
        rel.outputFormat = rel_obj.formato
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'sped_ecd_diario.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql

        pdf, formato = rel.execute()

        dados = {
            'nome': u'DIARIO_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_balancete(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        sql_novo ="""
            select
                coalesce((select r.razao_social from res_partner r where r.cnpj_cpf = rp.cnpj_cpf limit 1),'') as empresa,
                rp.cnpj_cpf,
                fc.codigo as codigo,
                fc.codigo_completo,
                fc.nome as nome,
                case
                when fc.tipo = 'A' then
                'Ativo'
                when fc.tipo = 'P' then
                'Passivo'
                when fc.tipo = 'R' then
                'Receita'
                when fc.tipo = 'C' then
                'Custo'
                when fc.tipo = 'D' then
                'Despesa'
                when fc.tipo = 'T' then
                'Transferência'
                when fc.tipo = 'O' then
                'Outras' end as tipo,
                fc.sintetica,
                            
                coalesce((select
                coalesce(sum(es.saldo),0)  as saldo_anterior    
                from ecd_saldo es
                join finan_conta fcs on fcs.id = es.conta_id
                join res_company css on css.id = es.company_id
                join res_partner rps on rps.id = css.partner_id    
                where
                fcs.codigo_completo like fc.codigo_completo || '%'
                and es.data = cast('{data_inicial}' as date) + interval '-1 day'                        
                and rps.cnpj_cpf = rp.cnpj_cpf"""
                
        if not rel_obj.somente_cnpj:
            sql_novo += """
                and css.id =  """ + str(rel_obj.company_id.id)
                            
        sql_novo += """
                ), 0) as saldo_anterior, 
                               
                (select
                coalesce(sum(cast(l.vr_debito as numeric(18,2))), 0) as total_debito
                from ecd_razao_view l        
                where
                l.codigo_completo like fc.codigo_completo || '%'
                and l.data_lancamento between '{data_inicial}' and '{data_final}'                
                and l.cnpj_cpf = rp.cnpj_cpf"""
        
        if not rel_obj.somente_cnpj:
            sql_novo += """
                and l.company_id = """ + str(rel_obj.company_id.id)
                            
        sql_novo += """        
                ) as total_debito,
                
                (select
                coalesce(sum(cast(l.vr_credito as numeric(18,2))), 0) as total_debito
                from ecd_razao_view l        
                where
                l.codigo_completo like fc.codigo_completo || '%'
                and l.data_lancamento between '{data_inicial}' and '{data_final}'                
                and l.cnpj_cpf = rp.cnpj_cpf"""
                
        if not rel_obj.somente_cnpj:
            sql_novo += """
                and l.company_id = """ + str(rel_obj.company_id.id)
                            
        sql_novo += """

                ) as total_credito
                    
            from finan_conta fc 
                join ecd_plano_conta ep on ep.id = fc.plano_id
                join res_company c on c.plano_id = ep.id
                join res_partner rp on rp.id = c.partner_id
            where"""
                       
        if rel_obj.somente_cnpj:
            sql_novo += """
                rp.cnpj_cpf = '{cnpj_cpf}' """
        else:
            sql_novo += """
                c.id = """ + str(rel_obj.company_id.id)

        sql_novo += """
           group by                
                rp.cnpj_cpf,                            
                fc.codigo,
                fc.codigo_completo,                
                fc.nome,
                fc.tipo,
                fc.sintetica
            
            order by
                fc.codigo_completo;"""

        filtro = {
            'cnpj_cpf': str(rel_obj.company_id.partner_id.cnpj_cpf),
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
        }

        sql = sql_novo.format(**filtro)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report(u'Balancete Contábil', cr, uid)
        rel.outputFormat = rel_obj.formato
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'sped_ecd_balancete.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql
        rel.parametros['SOMENTE_SALDO'] = rel_obj.somente_saldo

        pdf, formato = rel.execute()

        dados = {
            'nome': u'BALANCETE_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_balanco_patrimonial(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        sql = """
        select
            coalesce((select r.razao_social from res_partner r where r.cnpj_cpf = rp.cnpj_cpf limit 1),'') as empresa,
            rp.cnpj_cpf,
            coalesce(fc.codigo, 0) as codigo,
            coalesce(fc.codigo_completo,'') as codigo_completo,
            coalesce(fc.nome, '') as nome,
            case
            when fc.tipo = 'A' then
            'Ativo'
            when fc.tipo = 'P' then
            'Passivo'
            end as tipo,
            fc.sintetica,
            
            coalesce((select
            coalesce(sum(es.saldo),0)  as saldo_anterior    
            from ecd_saldo es
            join finan_conta fcs on fcs.id = es.conta_id
            join res_company css on css.id = es.company_id
            join res_partner rps on rps.id = css.partner_id    
            where
            fcs.codigo_completo like fc.codigo_completo || '%'
            and es.data = cast('{data_inicial}' as date) + interval '-1 day'                        
            and rps.cnpj_cpf = rp.cnpj_cpf"""
            
        if not rel_obj.somente_cnpj:
            sql += """
            and css.id = """ + str(rel_obj.company_id.id)
                            
        sql += """                  
            ), 0) as saldo_anterior, 

            (select
            coalesce(sum(cast(l.vr_debito as numeric(18,2))) - sum(cast(l.vr_credito as numeric(18,2))), 0) as saldo_anterior
            from ecd_razao_view l            
            where
            l.codigo_completo like fc.codigo_completo || '%'
            and l.data_lancamento between '{data_inicial}' and '{data_final}'
            and l.cnpj_cpf = rp.cnpj_cpf"""
            
        if not rel_obj.somente_cnpj:
            sql += """
            and l.company_id = """ + str(rel_obj.company_id.id)
                            
        sql += """                              
            ) as saldo_atual

        from finan_conta fc
            join ecd_plano_conta ep on ep.id = fc.plano_id
            join res_company c on c.plano_id = ep.id
            join res_partner rp on rp.id = c.partner_id      
            
        where
            fc.tipo in ('A','P')"""

        if rel_obj.somente_cnpj:
            sql += """
            and rp.cnpj_cpf = '{cnpj_cpf}' """
        else:
            sql += """
            and c.id = """ + str(rel_obj.company_id.id)

        sql += """
        group by
            empresa,
            rp.cnpj_cpf,            
            fc.codigo_completo,
            fc.tipo,
            fc.sintetica,
            fc.codigo,
            fc.nome

        order by
            fc.codigo_completo;"""

        filtro = {
            'cnpj_cpf': str(rel_obj.company_id.partner_id.cnpj_cpf),
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
        }

        sql = sql.format(**filtro)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report(u'Balanço Patrimônial', cr, uid)
        rel.outputFormat = rel_obj.formato
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'sped_ecd_balanco_contabil.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql
        rel.parametros['SOMENTE_SALDO'] = rel_obj.somente_saldo

        pdf, formato = rel.execute()

        dados = {
            'nome': u'BALANCO_PATRIMONIAL_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True


sped_ecd_relatorio()
