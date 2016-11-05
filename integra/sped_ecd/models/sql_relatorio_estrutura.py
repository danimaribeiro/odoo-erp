# -*- coding: utf-8 -*-


SQL_ESTRUTURA_DEMONSTRATIVO = """
SELECT 
ed.id as estrutura_id,
ed.codigo_completo,
ed.nome,
case
   when ed.resumida or ed.sintetica then null
   else p.conta_id
end as conta_id,
ed.resumida,
sum(coalesce(p.vr_debito,0)) as vr_debito,
sum(coalesce(p.vr_credito,0)) as vr_credito

FROM ecd_estrutura_demonstrativo_arvore a
join ecd_estrutura_demonstrativo_partida p on p.conta_demonstrativo_id = a.conta_id
join ecd_estrutura_demonstrativo ed on ed.id = a.conta_pai_id

where 
ed.tipo_demonstrativo = '{tipo_demonstrativo}'
and p.data between '{data_inicial}' and '{data_final}'
and p.company_id = {company_id}

group by
ed.id, 
ed.codigo_completo,
ed.nome,
4,
ed.resumida

ORDER BY 
ed.codigo_completo"""

SQL_ESTRUTURA_DEMONSTRATIVO_GERENCIAL = """
SELECT 
ed.id as estrutura_id,
ed.codigo_completo,
ed.nome,
case
   when ed.resumida or ed.sintetica then null
   else p.conta_id
end as conta_id,
ed.resumida,
sum(coalesce(p.vr_debito,0) * coalesce(lcr.porcentagem, 100) / 100.00) as vr_debito,
sum(coalesce(p.vr_credito,0) * coalesce(lcr.porcentagem, 100) / 100.00) as vr_credito

FROM ecd_estrutura_demonstrativo_arvore a
join ecd_estrutura_demonstrativo_partida p on p.conta_demonstrativo_id = a.conta_id
join ecd_estrutura_demonstrativo ed on ed.id = a.conta_pai_id
  
left join ecd_lancamento_contabil_rateio lcr on lcr.lancamento_contabil_id = p.lancamento_id
left join hr_department dpr on dpr.id = lcr.hr_department_id
left join finan_centrocusto ccr on ccr.id = lcr.centrocusto_id        
left join hr_contract hcr on hcr.id = lcr.hr_contract_id
left join frota_veiculo fvr on fvr.id = lcr.veiculo_id 
left join project_project ppr on ppr.id = lcr.veiculo_id 


where 
ed.tipo_demonstrativo = '{tipo_demonstrativo}'
and p.data between '{data_inicial}' and '{data_final}'
and p.company_id = {company_id}
{departmento_ids}
{centrocusto_ids}
{contract_ids}
{veiculo_ids}
{project_ids}           

group by
ed.id, 
ed.codigo_completo,
ed.nome,
4,
ed.resumida

ORDER BY 
ed.codigo_completo"""