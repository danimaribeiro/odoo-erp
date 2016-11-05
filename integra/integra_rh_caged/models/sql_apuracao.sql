sql_aliquotas = u'''select
max(a.aliquota_rat) as rat, max(a.aliquota_fap) as fap, max(a.aliquota_empresa) as empresa, max(a.aliquota_outras_entidades) as outras_entidades, sum(a.base_fgts) as base_fgts, sum(a.fgts) as fgts, sum(a.deducao_previdenciaria) as deducao_previdenciaria,
cast((
    select
    coalesce(sum(d.vr_previdencia), 0.00) as vr_previdencia

    from sped_documento d
    join res_company c on c.id = d.company_id
    join res_partner p on p.id = c.partner_id
    join res_partner f on f.id = d.partner_id

    where
    p.cnpj_cpf = '82.891.805/0001-37'
    and cast(d.data_emissao as date) >= cast('2014-08-01' as date)
    and cast(d.data_emissao as date) <= cast('2014-08-31' as date)
    and d.vr_previdencia > 0
    and d.emissao = '0'
    and (d.situacao = '00' or d.situacao is null)
) as numeric(18,2)) as retencoes,
cast((
    select
    coalesce(sum(d.vr_previdencia / 0.15), 0.00) as bc_previdencia

    from sped_documento d
    join res_company c on c.id = d.company_id
    join res_partner p on p.id = c.partner_id
    join res_partner f on f.id = d.partner_id

    where
    p.cnpj_cpf = '82.891.805/0001-37'
    and cast(d.data_emissao as date) >= cast('2014-08-01' as date)
    and cast(d.data_emissao as date) <= cast('2014-08-31' as date)
    and d.vr_previdencia > 0
    and d.emissao = '1'
    and d.situacao = '00'
    and f.eh_cooperativa = True
) as numeric(18,2)) as base_cooperativas,
cast((
    select
    coalesce(sum(d.vr_previdencia), 0.00) as vr_previdencia

    from sped_documento d
    join res_company c on c.id = d.company_id
    join res_partner p on p.id = c.partner_id
    join res_partner f on f.id = d.partner_id

    where
    p.cnpj_cpf = '82.891.805/0001-37'
    and cast(d.data_emissao as date) >= cast('2014-08-01' as date)
    and cast(d.data_emissao as date) <= cast('2014-08-31' as date)
    and d.vr_previdencia > 0
    and d.emissao = '1'
    and d.situacao = '00'
    and f.eh_cooperativa = True
) as numeric(18,2)) as valor_cooperativas

from

(
select
case
  when r.code = 'INSS_RAT' then cast(max(hl.rate) as numeric(18,4))
  else 0.00
end as aliquota_rat,
case
  when r.code = 'INSS_FAP_AJUSTADO' then cast(max(hl.rate / 100.00) as numeric(18,4))
  else 0.00
end as aliquota_fap,
case
  when r.code = 'INSS_EMPRESA' then cast(max(hl.rate) as numeric(18,2))
  else 0.00
end as aliquota_empresa,
case
  when r.code = 'INSS_OUTRAS_ENTIDADES' then cast(max(hl.rate) as numeric(18,2))
  else 0.00
end as aliquota_outras_entidades,
case
  when r.code = 'BASE_FGTS' and (h.tipo != 'R' or s.codigo_afastamento in ('J', 'L')) then sum(cast(hl.total as numeric(18,2)))
  else 0.00
end as base_fgts,
case
  when r.code = 'FGTS' and (h.tipo != 'R' or s.codigo_afastamento in ('J', 'L')) then sum(cast(hl.total as numeric(18,2)))
  else 0.00
end as fgts,
case
  when r.code = 'SALFAM' or r.code = 'LICENCA_MATERNIDADE' then sum(cast(hl.total as numeric(18,2)))
  else 0.00
end as deducao_previdenciaria

from hr_payslip_line hl
join hr_payslip h on h.id = hl.slip_id
join res_company c on c.id = h.company_id
join res_partner p on p.id = c.partner_id
join hr_contract ct on ct.id = h.contract_id
join hr_salary_rule r on r.id = hl.salary_rule_id
join hr_payroll_structure s on s.id = h.struct_id

where
 (
    (h.tipo = 'N' and h.date_from >= cast('2014-08-01' as date) and h.date_to <= cast('2014-08-31' as date))
     or (h.tipo = 'R' and h.data_afastamento between cast('2014-08-01' as date) and cast('2014-08-31' as date))
  )
  and r.code in ('INSS_RAT', 'INSS_FAP_AJUSTADO', 'INSS_EMPRESA', 'INSS_OUTRAS_ENTIDADES', 'BASE_FGTS', 'FGTS', 'SALFAM', 'LICENCA_MATERNIDADE')  and h.date_from >= cast('2014-08-01' as date)
  and h.date_to <= cast('2014-08-31' as date)
  and p.cnpj_cpf = '82.891.805/0001-37'

group by
r.code, h.tipo, s.codigo_afastamento) as a)'''


sql_2 = u'''
select
cast(coalesce(sum(
case
   when r.code like 'BASE%' then cast(hl.total as numeric(18,2))
   else 0
end), 0) as numeric(18,2)) as base,
cast(coalesce(max(
case
   when r.code not like 'BASE%' then cast(hl.rate as numeric(18,2))
   else 0
end), 0) as numeric(18,2)) as aliquota,
cast(coalesce(sum(
case
   when r.code not like 'BASE%' then cast(hl.total as numeric(18,2))
   else 0
end), 0) as numeric(18,2)) as valor


from hr_payslip_line hl
join hr_payslip h on h.id = hl.slip_id
join res_company c on c.id = h.company_id
join res_partner p on p.id = c.partner_id
join hr_contract ct on ct.id = h.contract_id
join hr_salary_rule r on r.id = hl.salary_rule_id

where
  h.tipo in ('N', 'R')
  and r.code in ('INSS', 'INSS_13', 'INSS_13_AP', 'BASE_INSS', 'BASE_INSS_13') and hl.code != 'BASE_INSS_anterior'
  and ct.categoria_trabalhador not between '700' and '799'
  -- and code in ('SALFAM', 'LICENCA_MATERNIDADE')
  -- and code in ('FGTS', 'FGTS_anterior')
  and (
    (h.tipo = 'N' and h.date_from >= cast('2014-08-01' as date) and h.date_to <= cast('2014-08-31' as date))
     or (h.tipo = 'R' and h.data_afastamento between cast('2014-08-01' as date) and cast('2014-08-31' as date))
  )
  and p.cnpj_cpf = '82.891.805/0001-37'
'''

sql_inss_funcionario = u'''
select
cast(coalesce(sum(
case
   when r.code like 'BASE%' then cast(hl.total as numeric(18,2))
   else 0
end), 0) as numeric(18,2)) as base,
cast(coalesce(max(
case
   when r.code not like 'BASE%' then cast(hl.rate as numeric(18,2))
   else 0
end), 0) as numeric(18,2)) as aliquota,
cast(coalesce(sum(
case
   when r.code not like 'BASE%' then cast(hl.total as numeric(18,2))
   else 0
end), 0) as numeric(18,2)) as valor


from hr_payslip_line hl
join hr_payslip h on h.id = hl.slip_id
join res_company c on c.id = h.company_id
join res_partner p on p.id = c.partner_id
join hr_contract ct on ct.id = h.contract_id
join hr_salary_rule r on r.id = hl.salary_rule_id

where
  h.tipo in ('N', 'R')
  and r.code in ('INSS', 'INSS_13', 'INSS_13_AP', 'BASE_INSS', 'BASE_INSS_13') and hl.code != 'BASE_INSS_anterior'
  and ct.categoria_trabalhador between '700' and '799'
  -- and code in ('SALFAM', 'LICENCA_MATERNIDADE')
  -- and code in ('FGTS', 'FGTS_anterior')
  and (
    (h.tipo = 'N' and h.date_from >= cast('2014-08-01' as date) and h.date_to <= cast('2014-08-31' as date))
     or (h.tipo = 'R' and h.data_afastamento between cast('2014-08-01' as date) and cast('2014-08-31' as date))
  )
  and p.cnpj_cpf = '82.891.805/0001-37'
'''