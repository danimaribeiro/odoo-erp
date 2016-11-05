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



class sped_ecd_relatorio(osv.osv_memory):
    _name = 'sped.ecd.relatorio'
    _inherit = 'sped.ecd.relatorio'
        
    _columns = {
        'departmento_ids': fields.many2many('hr.department','ecd_departmento_rateio','ecd_relatorio_id','department_id', u'Departamentos/Postos'),
        'centrocusto_ids': fields.many2many('finan.centrocusto','ecd_centrocusto_rateio', 'ecd_relatorio_id','centrocusto_id', u'Centro de custo'),        
        'contract_ids': fields.many2many('hr.contract','ecd_contrato_rateio', 'ecd_relatorio_id','contract_id', u'Funcionário'),
        'veiculo_ids': fields.many2many('frota.veiculo', 'ecd_frota_rateio', 'ecd_relatorio_id','veiculo_id', u'Veículo'),                     
    }

    _defaults = {
        
    }  
   
    def gera_relatorio_razao_financeiro(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        
        descricao = u''
        
        conta_ids = []
        if len(rel_obj.ecd_conta_ids) > 0:    
                        
            for conta_obj in rel_obj.ecd_conta_ids:
                conta_ids.append(conta_obj.id)
                contas_nome = u'[' + str(conta_obj.codigo) + u'] ' + conta_obj.codigo_completo  + u' ' + conta_obj.nome + u', '
                        
        departmento_ids = []
        if len(rel_obj.departmento_ids) > 0:    
    
            descricao += u'Departamentos/postos: ' 
            for departmento_obj in rel_obj.departmento_ids:
                departmento_ids.append(departmento_obj.id)
                descricao += departmento_obj.name
                        
        centrocusto_ids = []
        if len(rel_obj.centrocusto_ids) > 0:    
    
            descricao += u' | Centro de Custos: ' 
            for centrocusto_obj in rel_obj.centrocusto_ids:
                centrocusto_ids.append(centrocusto_obj.id)
                descricao += centrocusto_obj.nome
                        
        contract_ids = []
        if len(rel_obj.contract_ids) > 0:    
    
            descricao += u' | Contratos: ' 
            for contract_obj in rel_obj.contract_ids:
                contract_ids.append(contract_obj.id)
                descricao += contract_obj.descricao
                        
        veiculo_ids = []
        if len(rel_obj.veiculo_ids) > 0:    
    
            descricao += u' | Veiculos: ' 
            for veiculo_obj in rel_obj.veiculo_ids:
                veiculo_ids.append(veiculo_obj.id)
                descricao += veiculo_obj.nome
                        

        sql = """
        select 
        a.empresa,                
        a.cnpj_cpf,
        a.data_lancamento,
        a.codigo_lancamento,
        a.conta_id,
        a.partida_id,
        a.data_criacao,
        a.conta_contabil,
        a.codigo_completo,
        a.conta_reduzida,
        a.conta_nome,
        a.historico,
        a.centro_custo,
        a.contra_partidada,        
        sum(a.vr_debito) as vr_debito,
        sum(a.vr_credito) as vr_credito 
        
        from (
            select
                coalesce((select r.razao_social from res_partner r where r.cnpj_cpf = l.cnpj_cpf limit 1),'') as empresa,                
                l.cnpj_cpf,
                l.data_lancamento,
                l.codigo_lancamento,
                l.conta_id,
                l.partida_id,
                l.data_criacao,
                l.conta_contabil,
                l.codigo_completo,
                l.conta_reduzida,
                'Conta Contábil: [' || coalesce(l.conta_reduzida, 0) || '] ' || coalesce(l.codigo_completo,'') || ' ' || coalesce(l.conta_contabil, '') as conta_nome,
                coalesce(l.vr_debito, 0) * coalesce(lcr.porcentagem, 100) / 100.00 as vr_debito,
                coalesce(l.vr_credito, 0) * coalesce(lcr.porcentagem, 100) / 100.00 as vr_credito,
                l.historico,
                l.centro_custo,
                (select
                fcs.codigo as contra_partida
                from ecd_lancamento_contabil lcs
                join ecd_partida_lancamento pts on pts.lancamento_id = lcs.id
                join finan_conta fcs on fcs.id = pts.conta_id
                where
                lcs.id = l.codigo_lancamento
                and pts.id != l.partida_id
                and pts.tipo != l.tipo
                limit 1
                ) as contra_partidada
                
            from ecd_razao_view l                                    
            left join ecd_lancamento_contabil_rateio lcr on lcr.lancamento_contabil_id = l.codigo_lancamento
            left join hr_department dpr on dpr.id = lcr.hr_department_id
            left join finan_centrocusto ccr on ccr.id = lcr.centrocusto_id        
            left join hr_contract hcr on hcr.id = lcr.hr_contract_id
            left join frota_veiculo fvr on fvr.id = lcr.veiculo_id                           

            where
                l.data_lancamento between '{data_inicial}' and '{data_final}'"""

        if rel_obj.somente_cnpj:
            sql += """
                and l.cnpj_cpf = '{cnpj_cpf}' """
            company_cnpj = 'rp.cnpj_cpf = ' +  "'" + str(rel_obj.company_id.partner_id.cnpj_cpf) + "'"
        else:
            sql += """
                and l.company_id = """ + str(rel_obj.company_id.id)
            company_cnpj = 'cs.id = ' + str(rel_obj.company_id.id)

        if len(conta_ids) > 0:  
            sql += """
                and l.conta_id in """ +  str(tuple(conta_ids)).replace(',)', ')')
            
        if len(departmento_ids) > 0:  
            sql += """
                and lcr.hr_department_id in """ +  str(tuple(departmento_ids)).replace(',)', ')')
       
        if len(centrocusto_ids) > 0:  
            sql += """
                and coalesce(lcr.centrocusto_id, l.centrocusto_id)  in """ +  str(tuple(centrocusto_ids)).replace(',)', ')')
            
        if len(contract_ids) > 0:  
            sql += """
                and lcr.hr_contract_id in """ +  str(tuple(contract_ids)).replace(',)', ')')
            
        if len(veiculo_ids) > 0:  
            sql += """
                and lcr.veiculo_id in """ +  str(tuple(veiculo_ids)).replace(',)', ')')
       
        sql += """
            order by
                l.codigo_completo,
                l.data_lancamento,
                l.partida_id
        ) as a 
   
        group by        
            a.empresa,                
            a.cnpj_cpf,
            a.data_lancamento,
            a.codigo_lancamento,
            a.conta_id,
            a.partida_id,
            a.data_criacao,
            a.conta_contabil,
            a.codigo_completo,
            a.conta_reduzida,
            a.conta_nome,
            a.historico,
            a.centro_custo,
            a.contra_partidada
            
        order by
            a.codigo_completo,
            a.data_lancamento,
            a.partida_id    
        ;"""

        filtro = {
            'cnpj_cpf': str(rel_obj.company_id.partner_id.cnpj_cpf),
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
        }

        sql = sql.format(**filtro)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report(u'Razão Financeiro Gerencial', cr, uid)
        rel.outputFormat = rel_obj.formato
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'sped_ecd_razao_financeiro.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql
        rel.parametros['COMPANY_CNPJ'] = company_cnpj
        rel.parametros['DESCRICAO'] = descricao

        if len(conta_ids) == 1:
            rel.parametros['CONTA_ID'] = conta_ids[0]
            rel.parametros['CONTA_NOME'] = contas_nome

        pdf, formato = rel.execute()
        

        dados = {
            'nome': u'RAZAO_FINANCEIRO_GERENCIAL' + str(agora())[:16].replace(' ','_' ).replace('-','_') + ('.') + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True    
    
    def gera_relatorio_balancete_financeiro(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)        
        
        descricao = u''
        
        departmento_ids = []
        if len(rel_obj.departmento_ids) > 0:    
    
            descricao += u'Departamentos/postos: ' 
            for departmento_obj in rel_obj.departmento_ids:
                departmento_ids.append(departmento_obj.id)
                descricao += departmento_obj.name
                        
        centrocusto_ids = []
        if len(rel_obj.centrocusto_ids) > 0:    
    
            descricao += u' | Centro de Custos: ' 
            for centrocusto_obj in rel_obj.centrocusto_ids:
                centrocusto_ids.append(centrocusto_obj.id)
                descricao += centrocusto_obj.nome
                        
        contract_ids = []
        if len(rel_obj.contract_ids) > 0:    
    
            descricao += u' | Contratos: ' 
            for contract_obj in rel_obj.contract_ids:
                contract_ids.append(contract_obj.id)
                descricao += contract_obj.descricao
                        
        veiculo_ids = []
        if len(rel_obj.veiculo_ids) > 0:    
    
            descricao += u' | Veiculos: ' 
            for veiculo_obj in rel_obj.veiculo_ids:
                veiculo_ids.append(veiculo_obj.id)
                descricao += veiculo_obj.nome
                        

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
                and rps.cnpj_cpf = rp.cnpj_cpf
                and css.id = c.id            
                ), 0) as saldo_anterior, 
                               
                coalesce(
                    (select sum(total_debito)
                    from (
                        select
                            coalesce(sum(cast(l.vr_debito as numeric(18,2))), 0) * coalesce(lcr.porcentagem, 100) / 100.00 as total_debito
                        from ecd_razao_view l        
                            left join ecd_lancamento_contabil_rateio lcr on lcr.lancamento_contabil_id = l.codigo_lancamento
                            left join hr_department dpr on dpr.id = lcr.hr_department_id
                            left join finan_centrocusto ccr on ccr.id = lcr.centrocusto_id        
                            left join hr_contract hcr on hcr.id = lcr.hr_contract_id
                            left join frota_veiculo fvr on fvr.id = lcr.veiculo_id
                        where
                            l.codigo_completo like fc.codigo_completo || '%'
                            and l.data_lancamento between '{data_inicial}' and '{data_final}'
                            and l.company_id = c.id
                            and l.cnpj_cpf = rp.cnpj_cpf
                            {departmento_ids}                            
                            {centrocusto_ids}                            
                            {contract_ids}                            
                            {veiculo_ids}                    
                        group by
                            lcr.porcentagem
                    ) as a       
                ), 0) as total_debito,                                            
                
                coalesce(
                    (select 
                        sum(total_debito)
                    from (
                        select
                            coalesce(sum(cast(l.vr_credito as numeric(18,2))), 0) * coalesce(lcr.porcentagem, 100) / 100.00 as total_debito
                        from ecd_razao_view l
                            left join ecd_lancamento_contabil_rateio lcr on lcr.lancamento_contabil_id = l.codigo_lancamento
                            left join hr_department dpr on dpr.id = lcr.hr_department_id
                            left join finan_centrocusto ccr on ccr.id = lcr.centrocusto_id        
                            left join hr_contract hcr on hcr.id = lcr.hr_contract_id
                            left join frota_veiculo fvr on fvr.id = lcr.veiculo_id        
                        where
                            l.codigo_completo like fc.codigo_completo || '%'
                            and l.data_lancamento between '{data_inicial}' and '{data_final}'
                            and l.company_id = c.id
                            and l.cnpj_cpf = rp.cnpj_cpf
                            {departmento_ids}                            
                            {centrocusto_ids}                            
                            {contract_ids}                            
                            {veiculo_ids}                            
                        group by
                            lcr.porcentagem
                    ) as a                                                 
                ), 0) as total_credito
                    
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
                c.id,                
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
            'departmento_ids': '',
            'centrocusto_ids': '',
            'contract_ids': '',
            'veiculo_ids': '',            
        }
        if len(departmento_ids) > 0:                 
            filtro['departmento_ids'] = """ and lcr.hr_department_id in """ +  str(tuple(departmento_ids)).replace(',)', ')')
       
        if len(centrocusto_ids) > 0:  
            filtro['centrocusto_ids'] = """ and coalesce(lcr.centrocusto_id, l.centrocusto_id)  in """ +  str(tuple(centrocusto_ids)).replace(',)', ')')
            
        if len(contract_ids) > 0:  
            filtro['contract_ids'] = """ and lcr.hr_contract_id in """ +  str(tuple(contract_ids)).replace(',)', ')')
            
        if len(veiculo_ids) > 0:  
            filtro['veiculo_ids'] = """ and lcr.veiculo_id in """ +  str(tuple(veiculo_ids)).replace(',)', ')')
                

        sql = sql_novo.format(**filtro)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report(u'Balancete Financeiro Gerencial', cr, uid)
        rel.outputFormat = rel_obj.formato
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'sped_ecd_balancete_financeiro.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql
        rel.parametros['SOMENTE_SALDO'] = rel_obj.somente_saldo
        rel.parametros['DESCRICAO'] = descricao

        pdf, formato = rel.execute()

        dados = {
            'nome': u'BALANCETE_FINACEIRO_GERENCIAL_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True



sped_ecd_relatorio()
