# -*- coding: utf-8 -*-


SQL_CONFERENCIA_ECONOMICA = """
drop table if exists finan_conferencia_economica cascade ;

create table finan_conferencia_economica as
select *

from (
select
    ec.id as econo_conta_id,
    ec.codigo_completo,
    ec.nome,
    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_documento * -1
        else pr.valor_documento
    end, 0.00) as valor_documento,
    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor * -1
        else pr.valor
    end, 0.00) as valor,
    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_desconto
        else pr.valor_desconto * -1
    end, 0.00) as valor_desconto,
    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_juros * -1
        else pr.valor_juros
    end, 0.00) as valor_juros,
    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_multa * -1
        else pr.valor_multa
    end, 0.00) as valor_multa,

    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then (coalesce(pr.valor_juros, 0) + coalesce(pr.valor_multa, 0)) * -1
        else (coalesce(pr.valor_juros, 0) + coalesce(pr.valor_multa, 0))
    end, 0.00) as valor_juros_multa,

    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_desconto
        else 0
    end, 0.00) as valor_desconto_recebido,
    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then 0
        else pr.valor_juros
    end, 0.00) as valor_juros_recebido,
    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then 0
        else pr.valor_multa
    end, 0.00) as valor_multa_recebido,

    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then 0
        else (coalesce(pr.valor_juros, 0) + coalesce(pr.valor_multa, 0))
    end, 0.00) as valor_juros_multa_recebido,

    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then 0
        else pr.valor_desconto * -1
    end, 0.00) as valor_desconto_pago,
    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_juros * -1
        else 0
    end, 0.00) as valor_juros_pago,
    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_multa * -1
        else 0
    end, 0.00) as valor_multa_pago,

    coalesce(case
        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00
        when pr.tipo in ('P', 'S', 'PP', 'LP') then (coalesce(pr.valor_juros, 0) + coalesce(pr.valor_multa, 0)) * -1
        else 0
    end, 0.00) as valor_juros_multa_pago,

    coalesce(case

        when ec.campo = 'valor_desconto_recebido' then case
            when pr.tipo in ('P', 'S', 'PP', 'LP') then coalesce(pr.valor_desconto, 0)
            else 0
        end
        when ec.campo = 'valor_juros_multa_recebido' then case
            when pr.tipo in ('P', 'S', 'PP', 'LP') then 0
            else (coalesce(pr.valor_juros, 0) + coalesce(pr.valor_multa, 0))
        end
        when ec.campo = 'valor_desconto_pago' then case
            when pr.tipo in ('P', 'S', 'PP', 'LP') then 0
            else coalesce(pr.valor_desconto, 0) * -1
        end
        when ec.campo = 'valor_juros_multa_pago' then case
            when pr.tipo in ('P', 'S', 'PP', 'LP') then (coalesce(pr.valor_juros, 0) + coalesce(pr.valor_multa, 0)) * -1
            else 0
        end

        when
                ec.filtro_company_ids = '|'
            and ec.filtro_conta_ids = '|'
            and ec.filtro_centrocusto_ids = '|'
            and ec.filtro_contract_ids = '|'
            and ec.filtro_contract_exclui_ids = '|' then 0.00

        else case
            when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_documento * -1
            else pr.valor_documento
        end
    end, 0.00) as valor_usado,

    case
        when pr.id > 0 then pr.id
        else null
    end as rateio_id,
    pr.lancamento_id,
    pr.tipo,
    pr.data_compensacao,
    pr.company_id,
    pr.conta_id,
    pr.centrocusto_id,
    pr.hr_contract_id,
    pr.porcentagem,
    c.parent_id as grupo_id,
    pr.id as pagamento_rateio_id,
    l.conta_id as conta_individual_id,
    pr.res_partner_bank_id as partner_bank_id

from finan_pagamento_rateio_folha pr
join res_company c on c.id = pr.company_id
left join res_company cc on cc.id = c.parent_id
left join finan_lancamento l on l.id = pr.lancamento_id

left join econo_conta ec on (
    ec.campo != 'valor_documento'
    or (
        ec.sintetica = False
    and (ec.filtro_company_ids = '|' or (pr.company_id is not null and ec.filtro_company_ids like '%|' || cast(pr.company_id as varchar) || '|%'))
    and (ec.filtro_conta_ids = '|' or (pr.conta_id is not null and ec.filtro_conta_ids like '%|' || cast(pr.conta_id as varchar) || '|%'))
    and (ec.filtro_centrocusto_ids = '|' or (pr.centrocusto_id is not null and ec.filtro_centrocusto_ids like '%|' || cast(pr.centrocusto_id as varchar) || '|%'))
    and (ec.filtro_contract_ids = '|' or (pr.hr_contract_id is not null and ec.filtro_contract_ids like '%|' || cast(pr.hr_contract_id as varchar) || '|%'))
    and (ec.filtro_contract_exclui_ids = '|' or pr.hr_contract_id is null or ec.filtro_contract_exclui_ids not like '%|' || cast(pr.hr_contract_id as varchar) || '|%')
    )
)

where
    pr.data_compensacao between '{data_inicial}' and '{data_final}'
    and c.id in {company_ids}
) as primeira_analise

where
    primeira_analise.valor_usado != 0;

create index finan_conferencia_economica_rateio_idx on finan_conferencia_economica (rateio_id asc nulls last);
create index finan_conferencia_economica_lancamento_idx on finan_conferencia_economica (lancamento_id asc nulls last);
create index finan_conferencia_economica_econo_conta_idx on finan_conferencia_economica (econo_conta_id asc nulls last);
create index finan_conferencia_economica_conta_idx on finan_conferencia_economica (conta_id asc nulls last);
create index finan_conferencia_economica_conta_individual_idx on finan_conferencia_economica (conta_individual_id asc nulls last);
create index finan_conferencia_economica_partner_bank_idx on finan_conferencia_economica (partner_bank_id asc nulls last);
"""

SQL_ANALISE_ECONOMICA = """
select
    ec.id,
    ec.codigo_completo,
    ec.nome,
    sum(
    coalesce(ecr.valor_documento, 0)
) as valor_documento,
    sum(
    coalesce(ecr.valor, 0)
) as valor,
    sum(
    coalesce(ecr.valor_desconto, 0)
) as valor_desconto,
    sum(
    coalesce(ecr.valor_juros, 0)
) as valor_juros,
    sum(
    coalesce(ecr.valor_multa, 0)
) as valor_multa,
    sum(
    coalesce(ecr.valor_juros_multa, 0)
) as valor_juros_multa,
    sum(
    coalesce(ecr.valor_desconto_recebido, 0)
) as valor_desconto_recebido,
    sum(
    coalesce(ecr.valor_juros_recebido, 0)
) as valor_juros_recebido,
    sum(
    coalesce(ecr.valor_multa_recebido, 0)
) as valor_multa_recebido,
    sum(
    coalesce(ecr.valor_juros_multa_recebido, 0)
) as valor_juros_multa_recebido,
    sum(
    coalesce(ecr.valor_desconto_pago, 0)
) as valor_desconto_pago,
    sum(
    coalesce(ecr.valor_juros_pago, 0)
) as valor_juros_pago,
    sum(
    coalesce(ecr.valor_multa_pago, 0)
) as valor_multa_pago,
    sum(
    coalesce(ecr.valor_juros_multa_pago, 0)
) as valor_juros_multa_pago,
    sum(
    coalesce(ecr.valor_usado, 0)
) as valor_usado,
ec.campo as campo

from """
#from ("""

#SQL_ANALISE_ECONOMICA += SQL_CONFERENCIA_ECONOMICA

#SQL_ANALISE_ECONOMICA += """
    #) as ecr
SQL_ANALISE_ECONOMICA += """
    finan_conferencia_economica as ecr
    join econo_conta_arvore eca on eca.conta_id = ecr.econo_conta_id
    join econo_conta ec on ec.id = eca.id

group by
    ec.id, ec.codigo_completo, ec.nome

order by
    ec.codigo_completo;
"""
            ##and (
                ##c.id = {company_id}
                ##or cc.id = {company_id}
                ##or cc.parent_id = {company_id}
            ##)


SQL_NAO_ALOCADOS = """
insert into finan_conferencia_economica
(econo_conta_id, codigo_completo, nome, valor_documento, valor,
valor_desconto, valor_juros, valor_multa, valor_juros_multa,
valor_desconto_recebido, valor_juros_recebido, valor_multa_recebido, valor_juros_multa_recebido,
valor_desconto_pago, valor_juros_pago, valor_multa_pago, valor_juros_multa_pago,
valor_usado, rateio_id, lancamento_id, tipo, data_compensacao, company_id, conta_id, centrocusto_id, hr_contract_id, porcentagem, grupo_id, pagamento_rateio_id, conta_individual_id, partner_bank_id)
(
select
    null as econo_conta_id,
    '' as codigo_completo,
    '' as nome,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_documento * -1
        else pr.valor_documento
    end, 0.00) as valor_documento,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor * -1
        else pr.valor
    end, 0.00) as valor,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_desconto
        else pr.valor_desconto * -1
    end, 0.00) as valor_desconto,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_juros * -1
        else pr.valor_juros
    end, 0.00) as valor_juros,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_multa * -1
        else pr.valor_multa
    end, 0.00) as valor_multa,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then (coalesce(pr.valor_juros, 0) + coalesce(pr.valor_multa, 0)) * -1
        else (coalesce(pr.valor_juros, 0) + coalesce(pr.valor_multa, 0))
    end, 0.00) as valor_juros_multa,

    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_desconto
        else 0
    end, 0.00) as valor_desconto_recebido,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then 0
        else pr.valor_juros
    end, 0.00) as valor_juros_recebido,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then 0
        else pr.valor_multa
    end, 0.00) as valor_multa_recebido,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then 0
        else (coalesce(pr.valor_juros, 0) + coalesce(pr.valor_multa, 0))
    end, 0.00) as valor_juros_multa_recebido,

    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then 0
        else pr.valor_desconto * -1
    end, 0.00) as valor_desconto_pago,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_juros * -1
        else 0
    end, 0.00) as valor_juros_pago,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_multa * -1
        else 0
    end, 0.00) as valor_multa_pago,
    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then (coalesce(pr.valor_juros, 0) + coalesce(pr.valor_multa, 0)) * -1
        else 0
    end, 0.00) as valor_juros_multa_pago,

    coalesce(case
        when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor_documento * -1
        else pr.valor_documento
    end, 0.00) as valor_usado,

    case
        when pr.id > 0 then pr.id
        else null
    end as rateio_id,
    pr.lancamento_id,
    pr.tipo,
    pr.data_compensacao,
    pr.company_id,
    pr.conta_id,
    pr.centrocusto_id,
    pr.hr_contract_id,
    pr.porcentagem,
    c.parent_id as grupo_id,
    pr.id,
    l.conta_id as conta_individual_id,
    pr.res_partner_bank_id as partner_bank_id

from finan_pagamento_rateio_folha pr
join res_company c on c.id = pr.company_id
left join finan_lancamento l on l.id = pr.lancamento_id
left join finan_conferencia_economica fce on (pr.id > 0 and fce.rateio_id = pr.id) or (pr.id < 0 and fce.lancamento_id = pr.lancamento_id)

where
    pr.data_compensacao between '{data_inicial}' and '{data_final}'
    and c.id in {company_ids}
    and fce.econo_conta_id is null
);

"""