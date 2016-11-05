

SQL_CONTRATOS_REGULARES = """
select
    fc.numero as numero_contrato,
    rp.name as cliente,
    coalesce(fl.valor_original_contrato, 0) as valor_contrato,
    coalesce(sd.vr_nf, 0) as valor_fatura,
    fl.data_vencimento as data_vencimento_contrato,
    sd.data_emissao_brasilia as data_emissao,
    sd.numero as nf_numero

from
    sped_documento sd
    join finan_contrato fc on fc.id = sd.finan_contrato_id
    join res_company c on c.id = sd.company_id
    join res_partner rp on rp.id = sd.partner_id
    left join finan_lancamento fl on fl.sped_documento_id = sd.id

where
    sd.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
    and c.id = {company_id}
    and fc.natureza = 'R'
    and (fc.data_distrato is null or fc.data_distrato not between '{data_inicial}' and '{data_final}')
    and fc.data_assinatura not between '{data_inicial}' and '{data_final}'
    {filtro_adicional}

order by
    rp.name;
"""


SQL_CONTRATOS_NOVOS = """
select
    fc.numero as numero_contrato,
    fc.data_assinatura as data_inicio,
    rp.name as cliente,
    coalesce(coalesce(fl.valor_original_contrato, fc.valor_mensal), 0) as valor_contrato,
    coalesce(sd.vr_nf, 0) as valor_fatura,
    coalesce(fl.data_vencimento, fc.data_inicio) as data_vencimento_contrato,
    sd.data_emissao_brasilia as data_emissao,
    coalesce(sd.numero, 0) as nf_numero

from
    finan_contrato fc
    join res_company c on c.id = fc.company_id
    join res_partner rp on rp.id = fc.partner_id
    left join finan_lancamento fl on fl.contrato_id = fc.id and to_char(fc.data_inicio, 'yyyy-mm') = to_char(fl.data_vencimento, 'yyyy-mm')
    left join sped_documento sd on sd.id = fl.sped_documento_id

where
    fc.data_assinatura between '{data_inicial}' and '{data_final}'
    and c.id = {company_id}
    and fc.natureza = 'R'
    {filtro_adicional}

order by
    rp.name;
"""

SQL_CONTRATOS_RESCINDIDOS = """
select
    fc.numero as numero_contrato,
    fc.data_distrato as data_distrato,
    rp.name as cliente,
    coalesce(coalesce(fl.valor_original_contrato, fc.valor_mensal), 0) as valor_contrato,
    coalesce(sd.vr_nf, 0) as valor_fatura,
    coalesce(fl.data_vencimento, fc.data_distrato) as data_vencimento_contrato,
    sd.data_emissao_brasilia as data_emissao,
    coalesce(sd.numero, 0) as nf_numero

from
    finan_contrato fc
    join res_company c on c.id = fc.company_id
    join res_partner rp on rp.id = fc.partner_id
    left join finan_lancamento fl on fl.contrato_id = fc.id and to_char(fc.data_distrato + interval '1 month', 'yyyy-mm') = to_char(fl.data_vencimento, 'yyyy-mm')
    left join sped_documento sd on sd.id = fl.sped_documento_id

where
    fc.data_distrato between '{data_inicial}' and '{data_final}'
    and c.id = {company_id}
    and fc.natureza = 'R'
    {filtro_adicional}

order by
    rp.name;
"""

SQL_FATURAMENTO_AVULSO = """
select
    rp.name as cliente,
    coalesce(sd.vr_nf, 0) as valor_fatura,
    sd.data_emissao_brasilia as data_emissao,
    sd.numero as nf_numero,
    sd.modelo

from
    sped_documento sd
    left join finan_contrato fc on fc.id = sd.finan_contrato_id
    join res_company c on c.id = sd.company_id
    join res_partner rp on rp.id = sd.partner_id

where
    fc.id is null
    and sd.modelo in ('SE','RL')
    and sd.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
    and c.id = {company_id}
    and sd.emissao = '0'
    and sd.situacao in ('00', '01')

order by
    rp.name;
"""

SQL_CONTRATOS_BAIXADOS = """
select
    mb.nome as motivo_baixa,
    fl.data_baixa as data_baixa,
    fc.numero as numero_contrato,
    rp.name as cliente,
    fl.valor_original_contrato as valor_contrato,
    fl.valor_documento as valor_baixado,
    fl.data_vencimento

from
    finan_lancamento fl
    join finan_contrato fc on fc.id = fl.contrato_id
    join finan_motivobaixa mb on mb.id = fl.motivo_baixa_id
    join res_company c on c.id = fl.company_id
    join res_partner rp on rp.id = fl.partner_id

where
    fl.data_baixa between '{data_inicial}' and '{data_final}'
    and c.id = {company_id}
    and fc.natureza = 'R'
    {filtro_adicional}

order by
    mb.nome,
    rp.name;
"""

SQL_CONTRATOS_PROVISIONADOS = """
select
    fl.numero_documento as numero_documento,
    fc.numero as numero_contrato,
    rp.name as cliente,
    fl.valor_original_contrato as valor_contrato,
    fl.valor_documento as valor_baixado,
    fl.data_vencimento

from
    finan_lancamento fl
    join finan_contrato fc on fc.id = fl.contrato_id
    join res_company c on c.id = fl.company_id
    join res_partner rp on rp.id = fl.partner_id

where
    c.id = {company_id}
    and fc.natureza = 'R'
    and cast(to_char(fl.data_vencimento, 'YYYY-MM-01') as date) - interval '1 month' between '{data_inicial}' and '{data_final}'
    and fl.sped_documento_id is null
    and fl.data_baixa is null
    {filtro_adicional}

order by
    rp.name;
"""

SQL_CONTRATOS_DIFERENCA_MESES = """
select
    fc.numero as numero_contrato,
    rp.name as cliente,
    fl.numero_documento_original,
    fl.numero_documento,
    fl.data_vencimento as data_vencimento_contrato,
    (select la.data_vencimento from finan_lancamento la where la.contrato_id = fc.id and la.data_vencimento < fl.data_vencimento order by la.data_vencimento desc limit 1) as data_vencimento_anterior,
    fl.valor_original_contrato as valor_contrato,
    coalesce((select la.valor_original_contrato from finan_lancamento la where la.contrato_id = fc.id and la.data_vencimento < fl.data_vencimento order by la.data_vencimento desc limit 1), 0) as valor_contrato_anterior,
    coalesce(fl.valor_original_contrato, 0) - coalesce((select la.valor_original_contrato from finan_lancamento la where la.contrato_id = fc.id and la.data_vencimento < fl.data_vencimento order by la.data_vencimento desc limit 1), 0) as diferenca

from
    finan_contrato fc
    join res_company c on c.id = fc.company_id
    join res_partner rp on rp.id = fc.partner_id
    join finan_lancamento fl on fl.contrato_id = fc.id

where
    c.id = {company_id}
    and fc.natureza = 'R'
    and fc.data_assinatura not between '{data_inicial}' and '{data_final}'
    and cast(to_char(fl.data_vencimento, 'YYYY-MM-01') as date) - interval '1 month' between '{data_inicial}' and '{data_final}'
    and coalesce(fl.valor_original_contrato, 0) - coalesce((select la.valor_original_contrato from finan_lancamento la where la.contrato_id = fc.id and la.data_vencimento < fl.data_vencimento order by la.data_vencimento desc limit 1), 0) != 0
    {filtro_adicional}

order by
    rp.name;
"""

