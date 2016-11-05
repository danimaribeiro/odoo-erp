
select
    provdecimo.*,
    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.salario_decimo, 0) - coalesce(provdecimo.salario_decimo_anterior, 0)
        else coalesce(provdecimo.salario_decimo, 0)
    end as saldo_salario_decimo,
    case
        when coalesce(provdecimo.salario_decimo, 0) > coalesce(provdecimo.salario_decimo_anterior) then coalesce(provdecimo.salario_decimo, 0) - coalesce(provdecimo.salario_decimo_anterior, 0)
        else 0
    end provisao_salario_decimo,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.fgts, 0) - coalesce(provdecimo.fgts_anterior, 0)
        else coalesce(provdecimo.fgts, 0)
    end as saldo_fgts,
    case
        when coalesce(provdecimo.fgts, 0) > coalesce(provdecimo.fgts_anterior) then coalesce(provdecimo.fgts, 0) - coalesce(provdecimo.fgts_anterior, 0)
        else 0
    end provisao_fgts,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.inss, 0) - coalesce(provdecimo.inss_anterior, 0)
        else coalesce(provdecimo.inss, 0)
    end as saldo_inss,
    case
        when coalesce(provdecimo.inss, 0) > coalesce(provdecimo.inss_anterior) then coalesce(provdecimo.inss, 0) - coalesce(provdecimo.inss_anterior, 0)
        else 0
    end provisao_inss,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.base_inss, 0) - coalesce(provdecimo.base_inss_anterior, 0)
        else coalesce(provdecimo.base_inss, 0)
    end as saldo_base_inss,
    case
        when coalesce(provdecimo.base_inss, 0) > coalesce(provdecimo.base_inss_anterior) then coalesce(provdecimo.base_inss, 0) - coalesce(provdecimo.base_inss_anterior, 0)
        else 0
    end provisao_base_inss,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.inss_empresa, 0) - coalesce(provdecimo.inss_empresa_anterior, 0)
        else coalesce(provdecimo.inss_empresa, 0)
    end as saldo_inss_empresa,
    case
        when coalesce(provdecimo.inss_empresa, 0) > coalesce(provdecimo.inss_empresa_anterior) then coalesce(provdecimo.inss_empresa, 0) - coalesce(provdecimo.inss_empresa_anterior, 0)
        else 0
    end provisao_inss_empresa,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.inss_outras_entidades, 0) - coalesce(provdecimo.inss_outras_entidades_anterior, 0)
        else coalesce(provdecimo.inss_outras_entidades, 0)
    end as saldo_inss_outras_entidades,
    case
        when coalesce(provdecimo.inss_outras_entidades, 0) > coalesce(provdecimo.inss_outras_entidades_anterior) then coalesce(provdecimo.inss_outras_entidades, 0) - coalesce(provdecimo.inss_outras_entidades_anterior, 0)
        else 0
    end provisao_inss_outras_entidades,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.inss_rat, 0) - coalesce(provdecimo.inss_rat_anterior, 0)
        else coalesce(provdecimo.inss_rat, 0)
    end as saldo_inss_rat,
    case
        when coalesce(provdecimo.inss_rat, 0) > coalesce(provdecimo.inss_rat_anterior) then coalesce(provdecimo.inss_rat, 0) - coalesce(provdecimo.inss_rat_anterior, 0)
        else 0
    end provisao_inss_rat,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.inss_empresa_total, 0) - coalesce(provdecimo.inss_empresa_total_anterior, 0)
        else coalesce(provdecimo.inss_empresa_total, 0)
    end as saldo_inss_empresa_total,
    case
        when coalesce(provdecimo.inss_empresa_total, 0) > coalesce(provdecimo.inss_empresa_total_anterior) then coalesce(provdecimo.inss_empresa_total, 0) - coalesce(provdecimo.inss_empresa_total_anterior, 0)
        else 0
    end provisao_inss_empresa_total,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.liquido, 0) - coalesce(provdecimo.liquido_anterior, 0)
        else coalesce(provdecimo.liquido, 0)
    end as saldo_liquido,
    case
        when coalesce(provdecimo.liquido, 0) > coalesce(provdecimo.liquido_anterior) then coalesce(provdecimo.liquido, 0) - coalesce(provdecimo.liquido_anterior, 0)
        else 0
    end provisao_liquido,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.periculosidade, 0) - coalesce(provdecimo.periculosidade_anterior, 0)
        else coalesce(provdecimo.periculosidade, 0)
    end as saldo_periculosidade,
    case
        when coalesce(provdecimo.periculosidade, 0) > coalesce(provdecimo.periculosidade_anterior) then coalesce(provdecimo.periculosidade, 0) - coalesce(provdecimo.periculosidade_anterior, 0)
        else 0
    end provisao_periculosidade,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.bruto, 0) - coalesce(provdecimo.bruto_anterior, 0)
        else coalesce(provdecimo.bruto, 0)
    end as saldo_bruto,
    case
        when coalesce(provdecimo.bruto, 0) > coalesce(provdecimo.bruto_anterior) then coalesce(provdecimo.bruto, 0) - coalesce(provdecimo.bruto_anterior, 0)
        else 0
    end provisao_bruto,

    case
        when provdecimo.aviso_pagamento != '' then coalesce(provdecimo.valor_medias, 0) - coalesce(provdecimo.valor_medias_anterior, 0)
        else coalesce(provdecimo.valor_medias, 0)
    end as saldo_valor_medias,
    case
        when coalesce(provdecimo.valor_medias, 0) > coalesce(provdecimo.valor_medias_anterior) then coalesce(provdecimo.valor_medias, 0) - coalesce(provdecimo.valor_medias_anterior, 0)
        else 0
    end provisao_valor_medias


from (
    select
        cc.name as unidade,
        e.nome as funcionario,
        c.date_start as data_admissao,
        pf.competencia,
        pf.data_inicio_periodo_aquisitivo,
        h.data_fim_periodo_aquisitivo,
        h.meses_decimo_terceiro as avos,
        c.wage as salario_contratual,
        pf.provisao_id as holerite_id,

        case
            when coalesce(h.simulacao, False) = False and h.tipo = 'D' then 'Pago competência ' || to_char(h.date_from, 'mm/yyyy')
            when coalesce(h.simulacao, False) = False and h.tipo = 'R' then 'Rescisão - afastamento em ' || to_char(h.data_afastamento, 'dd/mm/yyyy')
            else ''
        end as aviso_pagamento,

        case
            when pf.provisao_id is not null then
                coalesce((select sum(coalesce(hl.total, 0))  from hr_payslip_line hl  where  hl.slip_id = pf.provisao_id           and hl.code  in ('SAL_13')), 0)
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('SAL_13')), 0) * 1
        end as salario_decimo,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('SAL_13')), 0)
        end as salario_decimo_anterior,


        case
            when pf.provisao_id is not null then
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'FGTS'), 0)
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'FGTS'), 0) * 1
        end as fgts,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'FGTS'), 0)
        end as fgts_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'BASE_INSS'), 0)
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'BASE_INSS'), 0) * 1
        end as base_inss,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'BASE_INSS'), 0)
        end as base_inss_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS'), 0)
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS'), 0) * 1
        end as inss,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS'), 0)
        end as inss_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select hl.rate   from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS'), 0)
            else
                coalesce((select hla.rate  from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS'), 0) * 1
        end as aliquota_inss,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select hla.rate  from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS'), 0)
        end as aliquota_inss_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS_EMPRESA'), 0)
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_EMPRESA'), 0) * 1
        end as inss_empresa,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_EMPRESA'), 0)
        end as inss_empresa_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS_OUTRAS_ENTIDADES'), 0)
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_OUTRAS_ENTIDADES'), 0) * 1
        end as inss_outras_entidades,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_OUTRAS_ENTIDADES'), 0)
        end as inss_outras_entidades_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS_RAT'), 0)
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_RAT'), 0) * 1
        end as inss_rat,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_RAT'), 0)
        end as inss_rat_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS_EMPRESA_TOTAL'), 0)
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_EMPRESA_TOTAL'), 0) * 1
        end as inss_empresa_total,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_EMPRESA_TOTAL'), 0)
        end as inss_empresa_total_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'LIQ_13'), 0)
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'LIQ_13'), 0) * 1
        end as liquido,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'LIQ_13'), 0)
        end as liquido_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select sum(coalesce(hl.total, 0))  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  in ('PERICULOSIDADE', 'DSR_PERICULOSIDADE')), 0)
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('PERICULOSIDADE', 'DSR_PERICULOSIDADE')), 0) * 1
        end as periculosidade,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('PERICULOSIDADE', 'DSR_PERICULOSIDADE')), 0)
        end as periculosidade_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select sum(coalesce(hl.total, 0))  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  in ('BRUTO')), 0)
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('BRUTO')), 0) * 1
        end as bruto,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('BRUTO')), 0)
        end as bruto_anterior,

        case
            when pf.provisao_id is not null then
                coalesce((select sum(coalesce(hl.total, 0))  from hr_payslip_line hl  join hr_salary_rule sr on sr.id = hl.salary_rule_id  where hl.slip_id = pf.provisao_id           and sr.tipo_media in ('valor', 'quantidade') and sr.sinal = '+'), 0)
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla join hr_salary_rule sr on sr.id = hla.salary_rule_id where hla.slip_id = pf.provisao_anterior_id and sr.tipo_media in ('valor', 'quantidade') and sr.sinal = '+'), 0) * 1
        end as valor_medias,
        case
            when pf.competencia like '%-01' then 0
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla join hr_salary_rule sr on sr.id = hla.salary_rule_id where hla.slip_id = pf.provisao_anterior_id and sr.tipo_media in ('valor', 'quantidade') and sr.sinal = '+'), 0)
        end as valor_medias_anterior

    from
        hr_provisao_decimo pf
        left join hr_payslip h on h.id = pf.provisao_id
        join hr_contract c on c.id = pf.contract_id
        join hr_employee e on e.id = c.employee_id
        join res_company cc on cc.id = c.company_id
        left join hr_payslip ha on ha.id = pf.provisao_anterior_id

    where
        (
	    pf.competencia = '{competencia}'
            or (pf.competencia = '{competencia_anterior}' and pf.decimo_id is null)
        )
        and (
            cc.id = {company_id}
            or cc.parent_id = {company_id}
        )
    ) as provdecimo

order by
    provdecimo.unidade,
    provdecimo.funcionario,
    provdecimo.competencia,
    provdecimo.data_fim_periodo_aquisitivo desc;
