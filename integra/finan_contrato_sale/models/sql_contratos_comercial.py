# -*- coding: utf-8 -*-


SQL_CONTRATOS_REGULARES_COMERCIAL = """
select
    fc.numero as numero_contrato,
    rp.name as cliente,
    sum(coalesce(fl.valor_original_contrato, 0)) as valor_contrato

from
    finan_lancamento fl
    join finan_contrato fc on fc.id = fl.contrato_id
    join res_partner rp on rp.id = fl.partner_id
    join res_company c on c.id = fl.company_id

where
    fl.{campo_data_vencimento} between '{data_inicial_competencia}' and '{data_final_competencia}'
    and (fc.data_distrato is null or fc.data_distrato > '{data_final}' or fc.data_distrato between '{data_inicial}' and '{data_final}')
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    and (
        to_char(cast(to_char(fc.data_assinatura, 'yyyy-mm-01') as date) + interval '1 month', 'yyyy-mm') != to_char(fl.{campo_data_vencimento}, 'yyyy-mm')
        or exists((select fca.contrato_id from finan_contrato_antigo fca where fca.contrato_id = fc.id))
    )
    {filtro_adicional}

group by
    fc.numero,
    rp.name

order by
    rp.name, fc.numero;
"""

SQL_CONTRATOS_REGULARES_ANTERIOR_COMERCIAL = """
select
    coalesce(sum(coalesce(fl.valor_original_contrato, 0)), 0) as valor_contrato,
    count(distinct(fc.id)) as quantidade

from
    finan_lancamento fl
    join finan_contrato fc on fc.id = fl.contrato_id
    join res_company c on c.id = fl.company_id
    join res_partner rp on rp.id = fl.partner_id


where
    fl.{campo_data_vencimento} between '{data_inicial_competencia_anterior}' and '{data_final_competencia_anterior}'
    and c.id in ({company_ids})
    and (fc.data_distrato is null or fc.data_distrato > '{data_final_anterior}' or fc.data_distrato between '{data_inicial_anterior}' and '{data_final_anterior}')
    and fc.natureza = 'R'
    and (
        to_char(cast(to_char(fc.data_assinatura, 'yyyy-mm-01') as date) + interval '1 month', 'yyyy-mm') != to_char(fl.{campo_data_vencimento}, 'yyyy-mm')
        or exists((select fca.contrato_id from finan_contrato_antigo fca where fca.contrato_id = fc.id))
    )
    {filtro_adicional};
"""


SQL_CONTRATOS_NOVOS_COMERCIAL = """
select
    fc.numero as numero_contrato,
    fc.data_assinatura as data_inicio,
    rp.name as cliente,
    rp.cnpj_cpf,
    coalesce(coalesce(fl.valor_original_contrato, fc.valor_mensal), 0) as valor_contrato

from
    finan_contrato fc
    join res_company c on c.id = fc.company_id
    join res_partner rp on rp.id = fc.partner_id
    left join finan_lancamento fl on fl.contrato_id = fc.id and to_char(fc.data_inicio, 'yyyy-mm') = to_char(fl.{campo_data_vencimento}, 'yyyy-mm')

where
    (
        fc.data_assinatura between '{data_inicial}' and '{data_final}'
        and (not exists((select fca.contrato_id from finan_contrato_antigo fca where fca.contrato_id = fc.id)))
    )
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    {filtro_adicional}

order by
    rp.name, fc.numero;
"""

SQL_CONTRATOS_NOVOS_ANTERIOR_COMERCIAL = """
select
    coalesce(sum(coalesce(fl.valor_original_contrato, 0)), 0) as valor_contrato,
    count(fc.id) as quantidade

from
    finan_contrato fc
    join res_company c on c.id = fc.company_id
    join res_partner rp on rp.id = fc.partner_id
    left join finan_lancamento fl on fl.contrato_id = fc.id and to_char(fc.data_inicio, 'yyyy-mm') = to_char(fl.{campo_data_vencimento}, 'yyyy-mm')

where
    (
        fc.data_assinatura between '{data_inicial_anterior}' and '{data_final_anterior}'
        and (not exists((select fca.contrato_id from finan_contrato_antigo fca where fca.contrato_id = fc.id)))
    )
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    {filtro_adicional_anterior};
"""


SQL_CONTRATOS_RESCINDIDOS_COMERCIAL = """
select
    fc.numero as numero_contrato,
    fc.data_distrato as data_distrato,
    rp.name as cliente,
    rp.cnpj_cpf,
    coalesce(coalesce(fl.valor_original_contrato, fc.valor_mensal), 0) as valor_contrato

from
    finan_contrato fc
    join res_company c on c.id = fc.company_id
    join res_partner rp on rp.id = fc.partner_id
    left join finan_lancamento fl on fl.contrato_id = fc.id and to_char(fc.data_distrato + interval '1 month', 'yyyy-mm') = to_char(fl.{campo_data_vencimento}, 'yyyy-mm')

where
    (
        fc.data_distrato between '{data_inicial}' and '{data_final}'
        and (not exists((select fca.antigo_id from finan_contrato_antigo fca where fca.antigo_id = fc.id)))
    )
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    {filtro_adicional}

order by
    rp.name, fc.numero;
"""


SQL_CONTRATOS_RESCINDIDOS_ANTERIOR_COMERCIAL = """
select
    sum(coalesce(coalesce(fl.valor_original_contrato, fc.valor_mensal), 0)) as valor_contrato,
    count(fc.id) as quantidade

from
    finan_contrato fc
    join res_company c on c.id = fc.company_id
    join res_partner rp on rp.id = fc.partner_id
    left join finan_lancamento fl on fl.contrato_id = fc.id and to_char(fc.data_distrato + interval '1 month', 'yyyy-mm') = to_char(fl.{campo_data_vencimento}, 'yyyy-mm')

where
    (
        fc.data_distrato between '{data_inicial_anterior}' and '{data_final_anterior}'
        and (not exists((select fca.antigo_id from finan_contrato_antigo fca where fca.antigo_id = fc.id)))
    )
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    {filtro_adicional_anterior};
"""


SQL_CONTRATOS_BAIXADOS_COMERCIAL = """
select
    mb.nome as motivo_baixa,
    fl.data_baixa as data_baixa,
    fc.numero as numero_contrato,
    rp.name as cliente,
    fl.valor_original_contrato as valor_contrato,
    fl.valor_documento as valor_baixado,
    fl.{campo_data_vencimento}

from
    finan_lancamento fl
    join finan_contrato fc on fc.id = fl.contrato_id
    join finan_motivobaixa mb on mb.id = fl.motivo_baixa_id
    join res_company c on c.id = fl.company_id
    join res_partner rp on rp.id = fl.partner_id

where
    fl.data_baixa between '{data_inicial}' and '{data_final}'
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    {filtro_adicional}

order by
    mb.nome,
    rp.name,
    fc.numero;
"""


SQL_CONTRATOS_BAIXADOS_ANTERIOR_COMERCIAL = """
select
    coalesce(sum(coalesce(fl.valor_original_contrato, 0)), 0) as valor_contrato,
    count(fc.id) as quantidade

from
    finan_lancamento fl
    join finan_contrato fc on fc.id = fl.contrato_id
    join finan_motivobaixa mb on mb.id = fl.motivo_baixa_id
    join res_company c on c.id = fl.company_id
    join res_partner rp on rp.id = fl.partner_id

where
    fl.data_baixa between '{data_inicial_anterior}' and '{data_final_anterior}'
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    {filtro_adicional_anterior};
"""


SQL_FATURAMENTO_PRODUTO = """
select
    uni.name as unidade,
    cli.name as cliente,
    cli.cnpj_cpf,
    nf.modelo,
    nf.data_emissao_brasilia,
    nf.serie,
    nf.numero,
    nf.vr_nf,
    coalesce(vendedor.name, '') as vendedor,
    coalesce(ped.name, '') as pedido,
    ped.date_order as data_pedido,
    coalesce(posto.name, 'Indefinido') as posto

from
    sped_documento nf
    join res_partner cli on cli.id = nf.partner_id
    join res_company uni on uni.id = nf.company_id
    left join sped_naturezaoperacao natop on natop.id = nf.naturezaoperacao_id
    left join sale_order_sped_documento pednota on pednota.sped_documento_id = nf.id
    left join sale_order ped on ped.id = pednota.sale_order_id
    left join res_users vendedor on vendedor.id = ped.user_id
    left join hr_department posto on posto.id = ped.hr_department_id

where
    nf.emissao = '0'
    and nf.situacao in ('00','01')
    and nf.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
    and nf.company_id in ({company_ids})
    and (natop.considera_venda = True or nf.modelo = '2D')
    {filtro_adicional}

order by
    uni.name,
    posto.name,
    vendedor.name,
    nf.modelo,
    nf.data_entrada_saida_brasilia,
    nf.serie,
    nf.numero;
"""


SQL_DEVOLUCAO_PRODUTO = """
select
    uni.name as unidade,
    cli.name as cliente,
    cli.cnpj_cpf,
    case
        when nf.emissao = '0' then 'Própria  '
        else 'Terceiros'
    end as emissao,
    nf.modelo,
    nf.data_entrada_saida_brasilia,
    nf.serie,
    nf.numero,
    nf.vr_nf,
    nfdev.data_emissao_brasilia as data_nf_devolvida,
    nfdev.serie as serie_nf_devolvida,
    nfdev.numero as numero_nf_devolvida,
    coalesce(vendedor.name, '') as vendedor,
    coalesce(ped.name, '') as pedido,
    ped.date_order as data_pedido,
    coalesce(posto.name, 'Indefinido') as posto


from
    sped_documento nf
    join res_partner cli on cli.id = nf.partner_id
    join res_company uni on uni.id = nf.company_id
    join sped_naturezaoperacao natop on natop.id = nf.naturezaoperacao_id
    left join sped_documentoreferenciado docref on docref.documento_id = nf.id
    left join sped_documento nfdev on nfdev.id = docref.documentoreferenciado_id
    left join sale_order_sped_documento pednota on pednota.sped_documento_id = nfdev.id
    left join sale_order ped on ped.id = pednota.sale_order_id
    left join res_users vendedor on vendedor.id = ped.user_id
    left join hr_department posto on posto.id = ped.hr_department_id

where
    nf.situacao in ('00','01')
    and nf.data_entrada_saida_brasilia between '{data_inicial}' and '{data_final}'
    and nf.company_id in ({company_ids})
    and natop.considera_devolucao_venda = True
    {filtro_adicional}

order by
    uni.name,
    posto.name,
    vendedor.name,
    nf.modelo,
    nf.data_entrada_saida_brasilia,
    nf.serie,
    nf.numero;
"""


SQL_RESUMO_FATURAMENTO = """
select
    'VENDAS' as tipo,
    uni.name as unidade,
    coalesce(posto.name, 'Indefinido') as posto,
    coalesce(vendedor.name, '') as vendedor,
    sum(coalesce(nf.vr_nf, 0)) as vr_nf

from
    sped_documento nf
    join res_partner cli on cli.id = nf.partner_id
    join res_company uni on uni.id = nf.company_id
    left join sped_naturezaoperacao natop on natop.id = nf.naturezaoperacao_id
    left join sale_order_sped_documento pednota on pednota.sped_documento_id = nf.id
    left join sale_order ped on ped.id = pednota.sale_order_id
    left join res_users vendedor on vendedor.id = ped.user_id
    left join hr_department posto on posto.id = ped.hr_department_id

where
    nf.emissao = '0'
    and nf.situacao in ('00','01')
    and nf.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
    and nf.company_id in ({company_ids})
    and (natop.considera_venda = True or nf.modelo = '2D')
    {filtro_adicional}

group by
    uni.name,
    posto.name,
    vendedor.name

UNION

select
    'DEVOLUÇÕES',
    uni.name as unidade,
    coalesce(posto.name, 'Indefinido') as posto,
    coalesce(vendedor.name, '') as vendedor,
    sum(coalesce(nf.vr_nf, 0) * -1) as vr_nf

from
    sped_documento nf
    join res_partner cli on cli.id = nf.partner_id
    join res_company uni on uni.id = nf.company_id
    join sped_naturezaoperacao natop on natop.id = nf.naturezaoperacao_id
    left join sped_documentoreferenciado docref on docref.documento_id = nf.id
    left join sped_documento nfdev on nfdev.id = docref.documentoreferenciado_id
    left join sale_order_sped_documento pednota on pednota.sped_documento_id = nfdev.id
    left join sale_order ped on ped.id = pednota.sale_order_id
    left join res_users vendedor on vendedor.id = ped.user_id
    left join hr_department posto on posto.id = ped.hr_department_id

where
    nf.situacao in ('00','01')
    and nf.data_entrada_saida_brasilia between '{data_inicial}' and '{data_final}'
    and nf.company_id in ({company_ids})
    and natop.considera_devolucao_venda = True
    {filtro_adicional}

group by
    uni.name,
    posto.name,
    vendedor.name

order by
    2,
    3,
    4,
    1 desc;
"""


SQL_CONTRATOS_ALTERADOS_COMERCIAL = """
select
    fc.id as contrato_novo_id,
    fc.numero as numero_contrato,
    rp.name as cliente,
    coalesce(fc.valor_mensal, 0) as valor_contrato,
    fa.numero as numero_contrato_antigo,
    coalesce(fa.valor_mensal, 0) as valor_contrato_antigo

from
    finan_contrato fc
    join res_partner rp on rp.id = fc.partner_id
    join res_company c on c.id = fc.company_id
    join finan_contrato_antigo fca on fca.contrato_id = fc.id
    join finan_contrato fa on fa.id = fca.antigo_id

where
    fc.data_assinatura between '{data_inicial}' and '{data_final}'
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    {filtro_adicional}

order by
    rp.name,
    fc.id,
    fc.numero,
    fa.numero;
"""


SQL_CONTRATOS_DIFERENCA_MESES_COMERCIAL = """
select
    diferente.*,
    diferente.valor_contrato - diferente.valor_contrato_anterior as diferenca,
    rp.name as cliente,
    fc.numero as numero_contrato

from
    (select
        fl.numero_documento_original,
        fl.numero_documento,
        fl.{campo_data_vencimento} as data_vencimento_contrato,
        cast(fl.valor_original_contrato as numeric(18, 2)) as valor_contrato,

        cast(coalesce(
            (select
                sum(coalesce(la.valor_original_contrato, 0))
            from
                finan_lancamento la
            where
                (la.contrato_id = contrato.id or la.contrato_id = any(contrato.antigo_ids))
                and to_char(la.{campo_data_vencimento}, 'YYYY-MM') = to_char(cast(to_char(fl.{campo_data_vencimento}, 'YYYY-MM-01') as date) - interval '1 month', 'YYYY-MM')
        ), 0) as numeric(18, 2)) as valor_contrato_anterior,

        (
            select
                la.{campo_data_vencimento}
            from
                finan_lancamento la
            where
                (la.contrato_id = contrato.id or la.contrato_id = any(contrato.antigo_ids))
                and to_char(la.{campo_data_vencimento}, 'YYYY-MM') = to_char(cast(to_char(fl.{campo_data_vencimento}, 'YYYY-MM-01') as date) - interval '1 month', 'YYYY-MM')
            order by
                la.{campo_data_vencimento} desc
            limit 1
        ) as data_vencimento_anterior,

        contrato.id,
        contrato.antigo_ids,
        array(select
            fcr.id

        from
            finan_contrato_reajuste_contrato fcrc
            join finan_contrato_reajuste fcr on fcr.id = fcrc.reajuste_id

        where
            fcrc.contrato_id = fl.contrato_id
            and cast(cast(to_char(fcr.data_confirmacao, 'YYYY-MM-01') as date) + interval '1 month' as date) between '{data_inicial_competencia}' and '{data_final_competencia}'
        ) as reajuste_ids


    from
        (select
            fcv.id,
            fcv.data_assinatura,
            array(select fca.antigo_id from finan_contrato_antigo fca where fca.contrato_id = fcv.id) as antigo_ids

        from
            finan_contrato fcv

        where
            fcv.company_id in ({company_ids})
            and fcv.natureza = 'R'
        ) as contrato
        join finan_lancamento fl on fl.contrato_id = contrato.id

    where
        (
            to_char(contrato.data_assinatura, 'yyyy-mm') != to_char(fl.{campo_data_vencimento}, 'yyyy-mm')
            or exists((select fca.contrato_id from finan_contrato_antigo fca where fca.contrato_id = contrato.id))
        )
        and cast(to_char(fl.{campo_data_vencimento}, 'YYYY-MM-01') as date) between '{data_inicial_competencia}' and '{data_final_competencia}'
    ) as diferente
    join finan_contrato fc on fc.id = diferente.id
    join res_partner rp on rp.id = fc.partner_id

where
    diferente.valor_contrato != diferente.valor_contrato_anterior
    and diferente.valor_contrato_anterior > 0
    {filtro_adicional}

order by
    rp.name, fc.numero;
"""


SQL_CONTRATOS_DIFERENCA_MESES_ANTERIOR_COMERCIAL = """
select
    diferente.*,
    diferente.valor_contrato - diferente.valor_contrato_anterior as diferenca,
    rp.name as cliente,
    fc.numero as numero_contrato

from
    (select
        fl.numero_documento_original,
        fl.numero_documento,
        fl.{campo_data_vencimento} as data_vencimento_contrato,
        fl.valor_original_contrato as valor_contrato,

        coalesce(
            (select
                sum(coalesce(la.valor_original_contrato, 0))
            from
                finan_lancamento la
            where
                (la.contrato_id = contrato.id or la.contrato_id = any(contrato.antigo_ids))
                and to_char(la.{campo_data_vencimento}, 'YYYY-MM') = to_char(cast(to_char(fl.{campo_data_vencimento}, 'YYYY-MM-01') as date) - interval '1 month', 'YYYY-MM')
        ), 0) as valor_contrato_anterior,

        (
            select
                la.{campo_data_vencimento}
            from
                finan_lancamento la
            where
                (la.contrato_id = contrato.id or la.contrato_id = any(contrato.antigo_ids))
                and to_char(la.{campo_data_vencimento}, 'YYYY-MM') = to_char(cast(to_char(fl.{campo_data_vencimento}, 'YYYY-MM-01') as date) - interval '1 month', 'YYYY-MM')
            order by
                la.{campo_data_vencimento} desc
            limit 1
        ) as data_vencimento_anterior,

        contrato.id, contrato.antigo_ids


    from
        (select
            fcv.id,
            fcv.data_assinatura,
            array(select fca.antigo_id from finan_contrato_antigo fca where fca.contrato_id = fcv.id) as antigo_ids

        from
            finan_contrato fcv

        where
            fcv.company_id in ({company_ids})
            and fcv.natureza = 'R'
        ) as contrato
        join finan_lancamento fl on fl.contrato_id = contrato.id

    where
        (
            to_char(contrato.data_assinatura, 'yyyy-mm') != to_char(fl.{campo_data_vencimento}, 'yyyy-mm')
            or exists((select fca.contrato_id from finan_contrato_antigo fca where fca.contrato_id = contrato.id))
        )
        and cast(to_char(fl.{campo_data_vencimento}, 'YYYY-MM-01') as date) between '{data_inicial_competencia_anterior}' and '{data_final_competencia_anterior}'
    ) as diferente
    join finan_contrato fc on fc.id = diferente.id
    join res_partner rp on rp.id = fc.partner_id

where
    diferente.valor_contrato != diferente.valor_contrato_anterior
    and diferente.valor_contrato_anterior > 0
    {filtro_adicional_anterior}

order by
    rp.name, fc.numero;
"""


SQL_CONTRATOS_ABC_GERAL = """
select
    abc.cliente,
    abc.cnpj_cpf,
    abc.valor_contrato,
    case
        when abc.valor_contrato >= 500 then 'Classe A'
        when abc.valor_contrato >= 250 then 'Classe B'
        when abc.valor_contrato >= 100 then 'Classe C'
        else 'Classe D'
    end as classe

from (
select
    rp.name as cliente,
    rp.cnpj_cpf,
    sum(coalesce(fl.valor_original_contrato, 0)) as valor_contrato

from
    finan_lancamento fl
    join finan_contrato fc on fc.id = fl.contrato_id
    join res_partner rp on rp.id = fl.partner_id
    join res_company c on c.id = fl.company_id

where
    fl.{campo_data_vencimento} between '{data_inicial_competencia}' and '{data_final_competencia}'
    and (fc.data_distrato is null or fc.data_distrato > '{data_final}' or fc.data_distrato between '{data_inicial}' and '{data_final}')
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    and (
        to_char(cast(to_char(fc.data_assinatura, 'yyyy-mm-01') as date) + interval '1 month', 'yyyy-mm') != to_char(fl.{campo_data_vencimento}, 'yyyy-mm')
        or exists((select fca.contrato_id from finan_contrato_antigo fca where fca.contrato_id = fc.id))
    )
    {filtro_adicional}

group by
    rp.name,
    rp.cnpj_cpf
    ) as abc

order by
    classe,
    abc.valor_contrato desc,
    abc.cliente;
"""


SQL_CONTRATOS_TRANSFERIDOS_COMERCIAL = """
select
    fc.numero as numero_contrato,
    v.data_inicial,
    rp.name as cliente,
    rp.cnpj_cpf,
    max(coalesce(fl.valor_original_contrato, 0)) as valor_contrato

from
    finan_lancamento fl
    join finan_contrato fc on fc.id = fl.contrato_id
    join res_partner rp on rp.id = fl.partner_id
    join res_company c on c.id = fl.company_id
    join finan_contrato_vendedor v on v.contrato_id = fc.id

where
    fl.{campo_data_vencimento} between '{data_inicial_competencia}' and '{data_final_competencia}'
    and (fc.data_distrato is null or fc.data_distrato > '{data_final}' or fc.data_distrato between '{data_inicial}' and '{data_final}')
    and (
        v.data_inicial between '{data_inicial}' and '{data_final}'
    )
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    and (
        to_char(cast(to_char(fc.data_assinatura, 'yyyy-mm-01') as date) + interval '1 month', 'yyyy-mm') != to_char(fl.{campo_data_vencimento}, 'yyyy-mm')
        or exists((select fca.contrato_id from finan_contrato_antigo fca where fca.contrato_id = fc.id))
    )
    {filtro_adicional}

group by
    fc.numero,
    v.data_inicial,
    rp.name,
    rp.cnpj_cpf

UNION ALL

select
    fc.numero as numero_contrato,
    v.data_final,
    rp.name as cliente,
    rp.cnpj_cpf,
    max(coalesce(fl.valor_original_contrato, 0)) * -1 as valor_contrato

from
    finan_lancamento fl
    join finan_contrato fc on fc.id = fl.contrato_id
    join res_partner rp on rp.id = fl.partner_id
    join res_company c on c.id = fl.company_id
    join finan_contrato_vendedor v on v.contrato_id = fc.id

where
    fl.{campo_data_vencimento} between '{data_inicial_competencia}' and '{data_final_competencia}'
    and (fc.data_distrato is null or fc.data_distrato > '{data_final}' or fc.data_distrato between '{data_inicial}' and '{data_final}')
    and (
        v.data_final between '{data_inicial}' and '{data_final}'
    )
    and c.id in ({company_ids})
    and fc.natureza = 'R'
    and (
        to_char(cast(to_char(fc.data_assinatura, 'yyyy-mm-01') as date) + interval '1 month', 'yyyy-mm') != to_char(fl.{campo_data_vencimento}, 'yyyy-mm')
        or exists((select fca.contrato_id from finan_contrato_antigo fca where fca.contrato_id = fc.id))
    )
    {filtro_adicional}

group by
    fc.numero,
    v.data_final,
    rp.name,
    rp.cnpj_cpf

"""
