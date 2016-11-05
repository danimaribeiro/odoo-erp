
select
    provferias.*,
    case
        when provferias.aviso_gozo != '' then coalesce(provferias.salario_ferias, 0) - coalesce(provferias.salario_ferias_anterior, 0)
        else coalesce(provferias.salario_ferias, 0) 
    end as saldo_salario_ferias,
    case
        when coalesce(provferias.salario_ferias, 0) > coalesce(provferias.salario_ferias_anterior) then coalesce(provferias.salario_ferias, 0) - coalesce(provferias.salario_ferias_anterior, 0)
        else 0
    end provisao_salario_ferias,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.salario_ferias_1_3, 0) - coalesce(provferias.salario_ferias_1_3_anterior, 0)
        else coalesce(provferias.salario_ferias_1_3, 0) 
    end as saldo_salario_ferias_1_3,
    case
        when coalesce(provferias.salario_ferias_1_3, 0) > coalesce(provferias.salario_ferias_1_3_anterior) then coalesce(provferias.salario_ferias_1_3, 0) - coalesce(provferias.salario_ferias_1_3_anterior, 0)
        else 0
    end provisao_salario_ferias_1_3,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.fgts, 0) - coalesce(provferias.fgts_anterior, 0)
        else coalesce(provferias.fgts, 0) 
    end as saldo_fgts,
    case
        when coalesce(provferias.fgts, 0) > coalesce(provferias.fgts_anterior) then coalesce(provferias.fgts, 0) - coalesce(provferias.fgts_anterior, 0)
        else 0
    end provisao_fgts,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.inss, 0) - coalesce(provferias.inss_anterior, 0)
        else coalesce(provferias.inss, 0) 
    end as saldo_inss,
    case
        when coalesce(provferias.inss, 0) > coalesce(provferias.inss_anterior) then coalesce(provferias.inss, 0) - coalesce(provferias.inss_anterior, 0)
        else 0
    end provisao_inss,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.base_inss, 0) - coalesce(provferias.base_inss_anterior, 0)
        else coalesce(provferias.base_inss, 0) 
    end as saldo_base_inss,
    case
        when coalesce(provferias.base_inss, 0) > coalesce(provferias.base_inss_anterior) then coalesce(provferias.base_inss, 0) - coalesce(provferias.base_inss_anterior, 0)
        else 0
    end provisao_base_inss,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.inss_empresa, 0) - coalesce(provferias.inss_empresa_anterior, 0)
        else coalesce(provferias.inss_empresa, 0) 
    end as saldo_inss_empresa,
    case
        when coalesce(provferias.inss_empresa, 0) > coalesce(provferias.inss_empresa_anterior) then coalesce(provferias.inss_empresa, 0) - coalesce(provferias.inss_empresa_anterior, 0)
        else 0
    end provisao_inss_empresa,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.inss_outras_entidades, 0) - coalesce(provferias.inss_outras_entidades_anterior, 0)
        else coalesce(provferias.inss_outras_entidades, 0) 
    end as saldo_inss_outras_entidades,
    case
        when coalesce(provferias.inss_outras_entidades, 0) > coalesce(provferias.inss_outras_entidades_anterior) then coalesce(provferias.inss_outras_entidades, 0) - coalesce(provferias.inss_outras_entidades_anterior, 0)
        else 0
    end provisao_inss_outras_entidades,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.inss_rat, 0) - coalesce(provferias.inss_rat_anterior, 0)
        else coalesce(provferias.inss_rat, 0) 
    end as saldo_inss_rat,
    case
        when coalesce(provferias.inss_rat, 0) > coalesce(provferias.inss_rat_anterior) then coalesce(provferias.inss_rat, 0) - coalesce(provferias.inss_rat_anterior, 0)
        else 0
    end provisao_inss_rat,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.inss_empresa_total, 0) - coalesce(provferias.inss_empresa_total_anterior, 0)
        else coalesce(provferias.inss_empresa_total, 0) 
    end as saldo_inss_empresa_total,
    case
        when coalesce(provferias.inss_empresa_total, 0) > coalesce(provferias.inss_empresa_total_anterior) then coalesce(provferias.inss_empresa_total, 0) - coalesce(provferias.inss_empresa_total_anterior, 0)
        else 0
    end provisao_inss_empresa_total,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.liquido, 0) - coalesce(provferias.liquido_anterior, 0)
        else coalesce(provferias.liquido, 0) 
    end as saldo_liquido,
    case
        when coalesce(provferias.liquido, 0) > coalesce(provferias.liquido_anterior) then coalesce(provferias.liquido, 0) - coalesce(provferias.liquido_anterior, 0)
        else 0
    end provisao_liquido,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.periculosidade, 0) - coalesce(provferias.periculosidade_anterior, 0)
        else coalesce(provferias.periculosidade, 0) 
    end as saldo_periculosidade,
    case
        when coalesce(provferias.periculosidade, 0) > coalesce(provferias.periculosidade_anterior) then coalesce(provferias.periculosidade, 0) - coalesce(provferias.periculosidade_anterior, 0)
        else 0
    end provisao_periculosidade,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.bruto, 0) - coalesce(provferias.bruto_anterior, 0)
        else coalesce(provferias.bruto, 0) 
    end as saldo_bruto,
    case
        when coalesce(provferias.bruto, 0) > coalesce(provferias.bruto_anterior) then coalesce(provferias.bruto, 0) - coalesce(provferias.bruto_anterior, 0)
        else 0
    end provisao_bruto,

    case
        when provferias.aviso_gozo != '' then coalesce(provferias.valor_medias, 0) - coalesce(provferias.valor_medias_anterior, 0)
        else coalesce(provferias.valor_medias, 0) 
    end as saldo_valor_medias,
    case
        when coalesce(provferias.valor_medias, 0) > coalesce(provferias.valor_medias_anterior) then coalesce(provferias.valor_medias, 0) - coalesce(provferias.valor_medias_anterior, 0)
        else 0
    end provisao_valor_medias


from (
    select
        coalesce(h.vencida, False) as vencida,
        cc.name as unidade,
        e.nome as funcionario,
        c.date_start as data_admissao,
        pf.data_inicio_periodo_aquisitivo,
        h.data_fim_periodo_aquisitivo,
        coalesce(h.dias_ferias, 0) as dias_ferias,
        coalesce(h.dias_ferias, 0) / 2.5 as avos,
        c.wage as salario_contratual,
        pf.provisao_id as holerite_id,
        
        (select coalesce(ha.dias_ferias, 0) from hr_payslip ha where ha.id = pf.provisao_anterior_id) as dias_ferias_anterior,
        (select coalesce(ha.dias_ferias, 0) / 2.5 from hr_payslip ha where ha.id = pf.provisao_anterior_id) as avos_anterior,
        
        
        case
            when coalesce(h.simulacao, False) = False and h.tipo = 'F' then 'Período gozado de ' || to_char(h.date_from, 'dd/mm/yyyy') || ' a ' || to_char(h.date_to, 'dd/mm/yyyy')
            when coalesce(h.simulacao, False) = False and h.tipo = 'R' then 'Rescisão - afastamento em ' || to_char(h.data_afastamento, 'dd/mm/yyyy')
            else ''
        end as aviso_gozo,

        case
            when pf.provisao_id is not null then 
                coalesce((select sum(coalesce(hl.total, 0))  from hr_payslip_line hl  where  hl.slip_id = pf.provisao_id           and hl.code  in ('FERIAS', 'ABONO')), 0)
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('FERIAS', 'ABONO')), 0) * 1
        end as salario_ferias,
        coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('FERIAS', 'ABONO')), 0) as salario_ferias_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select sum(coalesce(hl.total, 0))  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  in ('FERIAS_1_3', 'ABONO_1_3')), 0)
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('FERIAS_1_3', 'ABONO_1_3')), 0) * 1
        end as salario_ferias_1_3,
        coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('FERIAS_1_3', 'ABONO_1_3')), 0) as salario_ferias_1_3_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'FGTS'), 0)
            else 
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'FGTS'), 0) * 1
        end as fgts,
        coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'FGTS'), 0) as fgts_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'BASE_INSS'), 0)
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'BASE_INSS'), 0) * 1
        end as base_inss,
        coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'BASE_INSS'), 0) as base_inss_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS'), 0) 
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS'), 0) * 1
        end as inss,
        coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS'), 0) as inss_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select hl.rate   from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS'), 0) 
            else
                coalesce((select hla.rate  from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS'), 0) * 1
        end as aliquota_inss,
        coalesce((select hla.rate  from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS'), 0) as aliquota_inss_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS_EMPRESA'), 0) 
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_EMPRESA'), 0) * 1
        end as inss_empresa,
        coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_EMPRESA'), 0) as inss_empresa_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS_OUTRAS_ENTIDADES'), 0) 
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_OUTRAS_ENTIDADES'), 0) * 1
        end as inss_outras_entidades,
        coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_OUTRAS_ENTIDADES'), 0) as inss_outras_entidades_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS_RAT'), 0) 
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_RAT'), 0) * 1
        end as inss_rat,
        coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_RAT'), 0) as inss_rat_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'INSS_EMPRESA_TOTAL'), 0) 
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_EMPRESA_TOTAL'), 0) * 1
        end as inss_empresa_total,
        coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'INSS_EMPRESA_TOTAL'), 0) as inss_empresa_total_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select hl.total  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  = 'LIQ_FERIAS'), 0) 
            else
                coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'LIQ_FERIAS'), 0) * 1
        end as liquido,
        coalesce((select hla.total from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code = 'LIQ_FERIAS'), 0) as liquido_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select sum(coalesce(hl.total, 0))  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  in ('PERICULOSIDADE', 'DSR_PERICULOSIDADE', 'PERICULOSIDADE_ABONO', 'DSR_PERICULOSIDADE_ABONO')), 0)
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('PERICULOSIDADE', 'DSR_PERICULOSIDADE', 'PERICULOSIDADE_ABONO', 'DSR_PERICULOSIDADE_ABONO')), 0) * 1
        end as periculosidade,
        coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('PERICULOSIDADE', 'DSR_PERICULOSIDADE', 'PERICULOSIDADE_ABONO', 'DSR_PERICULOSIDADE_ABONO')), 0) as periculosidade_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select sum(coalesce(hl.total, 0))  from hr_payslip_line hl  where hl.slip_id = pf.provisao_id           and hl.code  in ('BRUTO', 'FERIAS_1_3', 'ABONO_1_3')), 0) 
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('BRUTO', 'FERIAS_1_3', 'ABONO_1_3')), 0) * 1
        end as bruto,
        coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla where hla.slip_id = pf.provisao_anterior_id and hla.code in ('BRUTO', 'FERIAS_1_3', 'ABONO_1_3')), 0) as bruto_anterior,

        case
            when pf.provisao_id is not null then 
                coalesce((select sum(coalesce(hl.total, 0))  from hr_payslip_line hl  join hr_salary_rule sr on sr.id = hl.salary_rule_id  where hl.slip_id = pf.provisao_id           and sr.tipo_media in ('valor', 'quantidade') and sr.sinal = '+'), 0) 
            else
                coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla join hr_salary_rule sr on sr.id = hla.salary_rule_id where hla.slip_id = pf.provisao_anterior_id and sr.tipo_media in ('valor', 'quantidade') and sr.sinal = '+'), 0) * 1
        end as valor_medias,
        coalesce((select sum(coalesce(hla.total, 0)) from hr_payslip_line hla join hr_salary_rule sr on sr.id = hla.salary_rule_id where hla.slip_id = pf.provisao_anterior_id and sr.tipo_media in ('valor', 'quantidade') and sr.sinal = '+'), 0) as valor_medias_anterior

    from
        hr_provisao_ferias pf
        left join hr_payslip h on h.id = pf.provisao_id
        join hr_contract c on c.id = pf.contract_id
        join hr_employee e on e.id = c.employee_id
        join res_company cc on cc.id = c.company_id

    where
        pf.competencia = '{competencia}'
        and (
            cc.id = {company_id}
            or cc.parent_id = {company_id}
        )
    ) as provferias

order by
    provferias.unidade,
    -- provferias.vencida desc,
    provferias.funcionario;
