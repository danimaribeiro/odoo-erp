# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from finan_conta import SQL_CRIA_ARVORE


SQL_VIEW_FINAN_ADIANTAMENTO_DEVOLUCAO = """
    create or replace view finan_adiantamento_devolucao as

    select
        'C' as tipo,
        e.res_partner_bank_id || to_char(e.data_quitacao::timestamp with time zone, 'YYYYmmdd') as id,
        e.res_partner_bank_id,
        e.data_quitacao,
        e.partner_id,
        e.company_id,
        coalesce((
            select
                sum(ee.valor_compensado_credito - ee.valor_compensado_debito) as sum
            from
                finan_extrato ee
            where
                ee.res_partner_bank_id = e.res_partner_bank_id
                and ee.partner_id = e.partner_id
                and ee.company_id = e.company_id
                and ee.data_quitacao < e.data_quitacao), 0) as saldo_anterior,
        sum(e.valor_compensado_credito) as credito,
        sum(e.valor_compensado_debito) as debito,
        coalesce((
            select
                sum(ee.valor_compensado_credito - ee.valor_compensado_debito) as saldo
            from
                finan_extrato ee
            where
                ee.res_partner_bank_id = e.res_partner_bank_id
                and ee.partner_id = e.partner_id
                and ee.company_id = e.company_id
                and ee.data_quitacao <= e.data_quitacao), 0) as saldo

    from
        finan_extrato e
        join res_partner_bank rpb on rpb.id = e.res_partner_bank_id

    where
        e.data_quitacao is not null
        and upper(rpb.state) in ('ADIANTAMENTO', 'DEVOLUCAO')
        and e.valor_compensado_credito > 0

    group by
        e.res_partner_bank_id,
        e.data_quitacao,
        e.partner_id,
        e.company_id

    UNION ALL

    select
        'F' as tipo,
        e.res_partner_bank_id || to_char(e.data_quitacao::timestamp with time zone, 'YYYYmmdd') as id,
        e.res_partner_bank_id,
        e.data_quitacao,
        e.partner_id,
        e.company_id,
        coalesce((
            select
                sum(ee.valor_compensado_credito - ee.valor_compensado_debito) as saldo
            from
                finan_extrato ee
            where
                ee.res_partner_bank_id = e.res_partner_bank_id
                and ee.partner_id = e.partner_id
                and ee.company_id = e.company_id
                and ee.data_quitacao < e.data_quitacao), 0) as saldo_anterior,
        sum(e.valor_compensado_credito) as credito,
        sum(e.valor_compensado_debito) as debito,
        coalesce((
            select
                sum(ee.valor_compensado_credito - ee.valor_compensado_debito) as sum
            from
                finan_extrato ee
            where
                ee.res_partner_bank_id = e.res_partner_bank_id
                and ee.partner_id = e.partner_id
                and ee.company_id = e.company_id
                and ee.data_quitacao <= e.data_quitacao), 0) as saldo

    from
        finan_extrato e
        join res_partner_bank rpb on rpb.id = e.res_partner_bank_id

    where
        e.data_quitacao is not null
        and upper(rpb.state) in ('ADIANTAMENTO', 'DEVOLUCAO')
        and e.valor_compensado_debito > 0

    group by
        e.res_partner_bank_id,
        e.data_quitacao,
        e.partner_id,
        e.company_id

    order by 3, 4, 5, 6;
"""


SQL_VIEW_FINAN_CONFERENCIA_FLUXO = """
    CREATE OR REPLACE VIEW finan_conferencia_fluxo AS
    SELECT row_number() OVER () AS id,
        f.data,
        fl.company_id,
        c.parent_id AS grupo_id,
        fl.partner_id,
            CASE
                WHEN fl.tipo::text = 'T'::text THEN f.conta_id
                ELSE fl.conta_id
            END AS conta_id,
        fl.centrocusto_id,
        f.res_partner_bank_id,
        fl.tipo,
        fl.numero_documento,
        fl.documento_id,
        COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) AS valor_entrada,
        COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) AS valor_saida,
        COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) AS diferenca
    FROM finan_fluxo_mensal_diario f
        LEFT JOIN finan_lancamento_lote_divida_pagamento ldp ON ldp.pagamento_id = f.id
        JOIN finan_lancamento fl ON ldp.divida_id IS NOT NULL AND fl.id = ldp.divida_id OR ldp.divida_id IS NULL AND fl.id = f.lancamento_id
        JOIN res_company c ON c.id = fl.company_id
    WHERE f.tipo = 'Q'::text;
"""


#SQL_VIEW_FINAN_CONTACORRENTE = """
    #CREATE OR REPLACE VIEW finan_contacorrente AS
    #SELECT l.id,
        #l.tipo,
        #l.company_id,
        #l.partner_id,
        #l.data_vencimento AS data,
            #CASE
                #WHEN l.tipo::text = 'R'::text THEN l.valor_documento
                #ELSE 0.00
            #END AS debito,
            #CASE
                #WHEN l.tipo::text = 'P'::text THEN l.valor_documento
                #ELSE 0.00
            #END AS credito,
            #CASE
                #WHEN l.tipo::text = 'R'::text THEN l.valor_documento * (-1)::numeric
                #ELSE l.valor_documento
            #END AS saldo
    #FROM finan_lancamento l
    #WHERE (l.tipo::text = ANY (ARRAY['R'::character varying::text, 'P'::character varying::text])) AND l.provisionado = false
    #UNION
    #SELECT l.id,
        #l.tipo,
            #CASE
                #WHEN l.tipo::text = ANY (ARRAY['E'::character varying::text, 'S'::character varying::text, 'T'::character varying::text]) THEN l.company_id
                #ELSE ( SELECT ll.company_id
                #FROM finan_lancamento ll
                #WHERE ll.id = l.lancamento_id)
            #END AS company_id,
            #CASE
                #WHEN l.tipo::text = ANY (ARRAY['E'::character varying::text, 'S'::character varying::text, 'T'::character varying::text]) THEN l.partner_id
                #ELSE ( SELECT ll.partner_id
                #FROM finan_lancamento ll
                #WHERE ll.id = l.lancamento_id)
            #END AS partner_id,
        #l.data_quitacao AS data,
            #CASE
                #WHEN l.tipo::text = ANY (ARRAY['PP'::character varying::text, 'S'::character varying::text, 'T'::character varying::text]) THEN l.valor
                #ELSE 0.00
            #END AS debito,
            #CASE
                #WHEN l.tipo::text = ANY (ARRAY['PR'::character varying::text, 'E'::character varying::text, 'T'::character varying::text]) THEN l.valor
                #ELSE 0.00
            #END AS credito,
            #CASE
                #WHEN l.tipo::text = ANY (ARRAY['PP'::character varying::text, 'S'::character varying::text, 'T'::character varying::text]) THEN l.valor * (-1)::numeric
                #ELSE l.valor
            #END AS saldo
    #FROM finan_lancamento l
    #WHERE (l.tipo::text = ANY (ARRAY['PR'::character varying::text, 'PP'::character varying::text, 'E'::character varying::text, 'S'::character varying::text, 'T'::character varying::text])) AND l.provisionado = false
    #ORDER BY 3, 4, 5, 6 DESC, 7 DESC, 1;
#"""

SQL_VIEW_FINAN_CONTACORRENTE = """
    CREATE OR REPLACE VIEW finan_contacorrente AS

    select
        e.id as id,
        cast(e.tipo as varchar) as tipo,
        e.company_id,
        e.partner_id,
        e.data_compensacao as data,
        cast(0 as numeric) as debito,
        cast(coalesce(e.valor_compensado, 0) as numeric) as credito,
        cast(coalesce(e.valor_compensado, 0) as numeric) as saldo,
        cast(0 as numeric) as debito_documento,
        cast(coalesce(e.valor_documento, 0) as numeric) as credito_documento,
        cast(coalesce(e.valor_documento, 0) as numeric) as saldo_documento,
        e.res_partner_bank_id

    from
        finan_entrada_lote e

    UNION ALL

    select
        s.id as id,
        s.tipo,
        s.company_id,
        s.partner_id,
        s.data_compensacao as data,
        cast(coalesce(s.valor_compensado, 0) as numeric) as debito,
        cast(0 as numeric) as credito,
        cast(coalesce(s.valor_compensado, 0) * -1 as numeric) as saldo,
        cast(coalesce(s.valor_documento, 0) as numeric) as debito_documento,
        cast(0 as numeric) as credito_documento,
        cast(coalesce(s.valor_documento, 0) * -1 as numeric) as saldo_documento,
        s.res_partner_bank_id

    from
        finan_saida_lote s

    UNION ALL

    select
        l.id,
        l.tipo,
        l.company_id,
        l.partner_id,
        l.data_vencimento as data,
        case
            when l.tipo = 'R' then cast(coalesce(l.valor_documento, 0) as numeric)
            else 0
        end as debito,
        case
            when l.tipo = 'P' then cast(coalesce(l.valor_documento, 0) as numeric)
            else 0
        end as credito,
        cast(coalesce(l.valor_documento, 0) as numeric) *
        case
            when l.tipo = 'R' then -1
            else 1
        end as saldo,
        case
            when l.tipo = 'R' then cast(coalesce(l.valor_documento, 0) as numeric)
            else 0
        end as debito_documento,
        case
            when l.tipo = 'P' then cast(coalesce(l.valor_documento, 0) as numeric)
            else 0
        end as credito_documento,
        cast(coalesce(l.valor_documento, 0) as numeric) *
        case
            when l.tipo = 'R' then -1
            else 1
        end as saldo_documento,
        null as res_partner_bank_id

    from
        finan_lancamento l

    where
        l.tipo in ('R', 'P');
"""


SQL_VIEW_FINAN_CONTACORRENTE_RATEIO = """
    CREATE OR REPLACE VIEW finan_contacorrente_rateio AS

    select
        coalesce(rateio.lancamento_id, e.id) as id,
        case
            when e.tipo = 'P' then 'PP'
            else cast(e.tipo as varchar)
        end as tipo,
        coalesce(rateio.company_id, e.company_id) as company_id,
        e.partner_id,
        e.data_compensacao as data,
        cast(0 as numeric) as debito,
        cast(coalesce(e.valor_compensado, 0) * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as numeric) as credito,
        cast(coalesce(e.valor_compensado, 0) * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as numeric) as saldo,
        cast(0 as numeric) as debito_documento,
        cast(coalesce(e.valor_documento, 0) * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as numeric) as credito_documento,
        cast(coalesce(e.valor_documento, 0) * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as numeric) as saldo_documento,
        e.res_partner_bank_id,
        coalesce(rateio.conta_id, e.conta_id) as conta_id,
        rateio.centrocusto_id,
        rateio.hr_contract_id,
        rateio.hr_department_id,

        rateio.veiculo_id,
        rateio.project_id

    from
        finan_entrada_lote e
        left join finan_pagamento_rateio_folha rateio on rateio.lancamento_id = e.lancamento_id

    UNION ALL

    select
        coalesce(rateio.lancamento_id, s.id) as id,
        case
            when s.tipo = 'R' then 'PR'
            else s.tipo
        end as tipo,
        coalesce(rateio.company_id, s.company_id) as company_id,
        s.partner_id,
        s.data_compensacao as data,
        cast(coalesce(s.valor_compensado, 0) * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as numeric) as debito,
        cast(0 as numeric) as credito,
        cast(coalesce(s.valor_compensado, 0) * -1 * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as numeric) as saldo,
        cast(coalesce(s.valor_documento, 0) * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as numeric) as debito_documento,
        cast(0 as numeric) as credito_documento,
        cast(coalesce(s.valor_documento, 0) * -1 * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as numeric) as saldo_documento,
        s.res_partner_bank_id,
        coalesce(rateio.conta_id, s.conta_id) as conta_id,
        rateio.centrocusto_id,
        rateio.hr_contract_id,
        rateio.hr_department_id,

        rateio.veiculo_id,
        rateio.project_id

    from
        finan_saida_lote s
        left join finan_pagamento_rateio_folha rateio on rateio.lancamento_id = s.lancamento_id

    UNION ALL

    select
        l.id,
        l.tipo,
        coalesce(rateio.company_id, l.company_id) as company_id,
        l.partner_id,
        l.data_vencimento as data,
        case
            when l.tipo = 'R' then cast(coalesce(l.valor_documento, 0) as numeric)
            else 0
        end * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as debito,
        case
            when l.tipo = 'P' then cast(coalesce(l.valor_documento, 0) as numeric)
            else 0
        end * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as credito,
        cast(coalesce(l.valor_documento, 0) as numeric) *
        case
            when l.tipo = 'R' then -1
            else 1
        end * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as saldo,
        case
            when l.tipo = 'R' then cast(coalesce(l.valor_documento, 0) as numeric)
            else 0
        end * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as debito_documento,
        case
            when l.tipo = 'P' then cast(coalesce(l.valor_documento, 0) as numeric)
            else 0
        end * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as credito_documento,
        cast(coalesce(l.valor_documento, 0) as numeric) *
        case
            when l.tipo = 'R' then -1
            else 1
        end * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) as saldo_documento,
        null as res_partner_bank_id,
        coalesce(rateio.conta_id, l.conta_id) as conta_id,
        rateio.centrocusto_id,
        rateio.hr_contract_id,
        rateio.hr_department_id,

        rateio.veiculo_id,
        rateio.project_id

    from
        finan_lancamento l
        left join finan_lancamento_rateio_geral_folha rateio on rateio.lancamento_id = l.id

    where
        l.tipo in ('R', 'P');
"""


SQL_VIEW_FINAN_ENTRADA = """
    CREATE OR REPLACE VIEW finan_entrada AS
    SELECT 'I'::text AS tipo,
        b.id * (-1) AS id,
        b.data_saldo_inicial AS data_documento,
        'SALDO INICIAL'::character varying(30) AS numero_documento,
        b.data_saldo_inicial AS data_vencimento,
        b.data_saldo_inicial AS data_quitacao,
        b.data_saldo_inicial AS data_compensacao,
        b.saldo_inicial::numeric AS valor_documento,
        b.saldo_inicial::numeric AS valor_compensado,
        0 AS valor_multa,
        0 AS valor_juros,
        0 AS valor_desconto,
        NULL::integer AS partner_id,
        b.conta_id,
        b.id AS res_partner_bank_id,
        true AS conciliado,
        NULL::integer AS lancamento_id,
        b.company_id
    FROM res_partner_bank b
    UNION
    SELECT 'E'::text AS tipo,
        e.id,
        e.data_documento,
        e.numero_documento,
        e.data_quitacao AS data_vencimento,
        e.data_quitacao,
        e.data AS data_compensacao,
        e.valor_documento,
        e.valor AS valor_compensado,
        e.valor_multa,
        e.valor_juros,
        e.valor_desconto,
        e.partner_id,
        e.conta_id,
        e.res_partner_bank_id,
        e.conciliado,
        e.id AS lancamento_id,
        e.company_id
    FROM finan_lancamento e
    WHERE e.tipo::text = 'E'::text
    UNION
    SELECT 'T'::text AS tipo,
        te.id,
        te.data_documento,
        te.numero_documento,
        te.data AS data_vencimento,
        te.data AS data_quitacao,
        te.data AS data_compensacao,
        te.valor AS valor_documento,
        te.valor AS valor_compensado,
        COALESCE(te.valor_multa, 0::numeric) AS valor_multa,
        COALESCE(te.valor_juros, 0::numeric) AS valor_juros,
        COALESCE(te.valor_desconto, 0::numeric) AS valor_desconto,
        te.partner_id,
        COALESCE(te.conta_id, b.conta_id) AS conta_id,
        te.res_partner_bank_creditar_id AS res_partner_bank_id,
        te.conciliado,
        te.id AS lancamento_id,
        te.company_id
    FROM finan_lancamento te
        JOIN res_partner_bank b ON b.id = te.res_partner_bank_creditar_id
    WHERE te.tipo::text = 'T'::text
    UNION
    SELECT 'R'::text AS tipo,
        pr.id,
        r.data_documento,
        r.numero_documento,
        r.data_vencimento,
        pr.data_quitacao,
        COALESCE(pr.data, pr.data_quitacao) AS data_compensacao,
        pr.valor_documento,
        pr.valor AS valor_compensado,
        pr.valor_multa,
        pr.valor_juros,
        pr.valor_desconto,
        r.partner_id,
        r.conta_id,
        pr.res_partner_bank_id,
        pr.conciliado,
        pr.lancamento_id,
        r.company_id
    FROM finan_lancamento pr
        JOIN finan_lancamento r ON r.id = pr.lancamento_id
    WHERE pr.tipo::text = 'PR'::text;
"""


SQL_VIEW_FINAN_ENTRADA_LOTE = """
    CREATE OR REPLACE VIEW finan_entrada_lote AS
    SELECT
        e.tipo,
        e.id,
        e.data_documento,
        coalesce(fl.numero_documento, e.numero_documento) as numero_documento,
        e.data_vencimento,
        e.data_quitacao,
        e.data_compensacao,
        cast(cast(coalesce(e.valor_documento, 0) as numeric) * cast(coalesce(ldp.porcentagem, 1) as numeric) as numeric) as valor_documento,
        cast(cast(coalesce(e.valor_compensado, 0) as numeric) * cast(coalesce(ldp.porcentagem, 1) as numeric) as numeric) as valor_compensado,
        cast(cast(coalesce(e.valor_multa, 0) as numeric) * cast(coalesce(ldp.porcentagem, 1) as numeric) as numeric) as valor_multa,
        cast(cast(coalesce(e.valor_juros, 0) as numeric) * cast(coalesce(ldp.porcentagem, 1) as numeric) as numeric) as valor_juros,
        cast(cast(coalesce(e.valor_desconto, 0) as numeric) * cast(coalesce(ldp.porcentagem, 1) as numeric) as numeric) as valor_desconto,
        coalesce(fl.partner_id, e.partner_id) as partner_id,
        coalesce(fl.conta_id, e.conta_id) as conta_id,
        e.res_partner_bank_id,
        e.conciliado,
        coalesce(fl.id, e.lancamento_id) as lancamento_id,
        coalesce(fl.company_id, e.company_id) as company_id,
        coalesce(ldp.porcentagem, 1) as porcentagem

    FROM
        finan_entrada e
        left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = e.id and ldp.lote_id = e.lancamento_id
        left join finan_lancamento fl on (ldp.divida_id is not null and fl.id = ldp.divida_id) or (ldp.divida_id is null and fl.id = e.lancamento_id);
"""


#SQL_VIEW_FINAN_ESTRUTURA_DEMONSTRATIVO_PARTIDA = """
    #CREATE OR REPLACE VIEW public.finan_estrutura_demonstrativo_partida AS
    #SELECT
        #ed.id AS conta_demonstrativo_id,
        #l.id AS lancamento_id,
        #c.id AS conta_id,
        #p.valor_entrada AS vr_debito,
        #p.valor_saida AS vr_credito,
        #l.centrocusto_id,
        #l.company_id,
        #p.data
    #FROM finan_fluxo_mensal_diario p
        #JOIN finan_lancamento l ON l.id = p.lancamento_id
        #JOIN finan_conta c ON c.id = l.conta_id
        #JOIN finan_estrutura_demonstrativo ed ON ed.sintetica = false AND ed.filtro_conta_ids <> '|'::text AND l.conta_id IS NOT NULL AND ed.filtro_conta_ids ~~ (('%|'::text || l.conta_id::character varying::text) || '|%'::text);
#"""


SQL_VIEW_FINAN_EXTRATO = """
    CREATE OR REPLACE VIEW finan_extrato AS
    SELECT e.tipo,
        e.id,
        e.data_documento,
        e.numero_documento,
        e.data_vencimento,
        e.data_quitacao,
        e.data_compensacao,
        e.valor_documento AS valor_documento_credito,
        e.valor_compensado AS valor_compensado_credito,
        e.valor_multa AS valor_multa_credito,
        e.valor_juros AS valor_juros_credito,
        e.valor_desconto AS valor_desconto_credito,
        e.partner_id,
        e.conta_id,
        e.res_partner_bank_id,
        0 AS valor_documento_debito,
        0 AS valor_compensado_debito,
        0 AS valor_multa_debito,
        0 AS valor_juros_debito,
        0 AS valor_desconto_debito,
        e.conciliado,
        e.lancamento_id,
        e.company_id
    FROM finan_entrada e
    UNION
    SELECT s.tipo,
        s.id,
        s.data_documento,
        s.numero_documento,
        s.data_vencimento,
        s.data_quitacao,
        s.data_compensacao,
        0 AS valor_documento_credito,
        0 AS valor_compensado_credito,
        0 AS valor_multa_credito,
        0 AS valor_juros_credito,
        0 AS valor_desconto_credito,
        s.partner_id,
        s.conta_id,
        s.res_partner_bank_id,
        s.valor_documento AS valor_documento_debito,
        s.valor_compensado AS valor_compensado_debito,
        s.valor_multa AS valor_multa_debito,
        s.valor_juros AS valor_juros_debito,
        s.valor_desconto AS valor_desconto_debito,
        s.conciliado,
        s.lancamento_id,
        s.company_id
    FROM finan_saida s;
"""


SQL_VIEW_FINAN_EXTRATO_FLUXO = """
    CREATE OR REPLACE VIEW public.finan_extrato_fluxo AS
    SELECT e.tipo,
        e.id,
        e.data_documento,
        e.numero_documento,
        e.data_vencimento,
        e.data_quitacao,
        e.data_compensacao,
        e.valor_documento AS valor_documento_credito,
        e.valor_compensado AS valor_compensado_credito,
        e.valor_multa AS valor_multa_credito,
        e.valor_juros AS valor_juros_credito,
        e.valor_desconto AS valor_desconto_credito,
        e.partner_id,
        e.conta_id,
        e.res_partner_bank_id,
        0 AS valor_documento_debito,
        0 AS valor_compensado_debito,
        0 AS valor_multa_debito,
        0 AS valor_juros_debito,
        0 AS valor_desconto_debito,
        e.conciliado,
        e.lancamento_id,
        e.company_id,
        c.parent_id
    FROM finan_entrada e
        LEFT JOIN res_company c ON c.id = e.company_id
    UNION
    SELECT s.tipo,
        s.id,
        s.data_documento,
        s.numero_documento,
        s.data_vencimento,
        s.data_quitacao,
        s.data_compensacao,
        0 AS valor_documento_credito,
        0 AS valor_compensado_credito,
        0 AS valor_multa_credito,
        0 AS valor_juros_credito,
        0 AS valor_desconto_credito,
        s.partner_id,
        s.conta_id,
        s.res_partner_bank_id,
        s.valor_documento AS valor_documento_debito,
        s.valor_compensado AS valor_compensado_debito,
        s.valor_multa AS valor_multa_debito,
        s.valor_juros AS valor_juros_debito,
        s.valor_desconto AS valor_desconto_debito,
        s.conciliado,
        s.lancamento_id,
        s.company_id,
        c.parent_id
    FROM finan_saida s
        LEFT JOIN res_company c ON c.id = s.company_id;
"""


SQL_VIEW_FINAN_FLUXO_CAIXA_SINTETICO = """
    CREATE OR REPLACE VIEW finan_fluxo_caixa_sintetico AS
    SELECT fl.company_id,
        f.data,
        f.provisionado,
        c.id,
        c.codigo_completo,
        COALESCE(c.sintetica, false) AS sintetica,
        f.tipo,
        fc.tipo AS tipo_conta,
        c.nome,
        f.res_partner_bank_id,
        fc.hr_department_id,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '01' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_01,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '02' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_02,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '03' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_03,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '04' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_04,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '05' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_05,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '06' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_06,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '07' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_07,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '08' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_08,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '09' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_09,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '10' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_10,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '11' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_11,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '12' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_12,
        0 AS vencido_01,
        0 AS vencido_02,
        0 AS vencido_03,
        0 AS vencido_04,
        0 AS vencido_05,
        0 AS vencido_06,
        0 AS vencido_07,
        0 AS vencido_08,
        0 AS vencido_09,
        0 AS vencido_10,
        0 AS vencido_11,
        0 AS vencido_12
    FROM finan_fluxo_mensal_diario f
        JOIN finan_lancamento fl ON fl.id = f.lancamento_id
        JOIN finan_conta fc ON fl.tipo = 'T' AND fc.id = f.conta_id OR fl.tipo <> 'T' AND fc.id = fl.conta_id
        JOIN finan_conta_arvore ca ON fl.tipo = 'T' AND ca.conta_id = f.conta_id OR fl.tipo <> 'T' AND ca.conta_id = fl.conta_id
        JOIN finan_conta c ON c.id = ca.conta_pai_id
    WHERE f.tipo = 'Q'
    UNION ALL
    SELECT l.company_id,
        f.data,
        f.provisionado,
        c.id,
        c.codigo_completo,
        COALESCE(c.sintetica, false) AS sintetica,
        f.tipo,
        fc.tipo AS tipo_conta,
        c.nome,
        f.res_partner_bank_id,
        fc.hr_department_id,
        0 AS quitado_01,
        0 AS quitado_02,
        0 AS quitado_03,
        0 AS quitado_04,
        0 AS quitado_05,
        0 AS quitado_06,
        0 AS quitado_07,
        0 AS quitado_08,
        0 AS quitado_09,
        0 AS quitado_10,
        0 AS quitado_11,
        0 AS quitado_12,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '01' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_01,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '02' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_02,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '03' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_03,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '04' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_04,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '05' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_05,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '06' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_06,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '07' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_07,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '08' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_08,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '09' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_09,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '10' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_10,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '11' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_11,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '12' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_12
    FROM finan_fluxo_mensal_diario f
        JOIN finan_lancamento l ON l.id = f.lancamento_id
        JOIN finan_conta fc ON fc.id = l.conta_id
        JOIN finan_conta_arvore ca ON ca.conta_id = l.conta_id
        JOIN finan_conta c ON c.id = ca.conta_pai_id
    WHERE f.tipo = 'V';
"""

SQL_VIEW_FINAN_FLUXO_CAIXA_SINTETICO_DEPARTAMENTO = """
    CREATE OR REPLACE VIEW finan_fluxo_caixa_sintetico_departamento AS
    SELECT fl.company_id,
        f.data,
        f.provisionado,
        c.id,
        c.codigo_completo,
        COALESCE(c.sintetica, false) AS sintetica,
        f.tipo,
        fc.tipo AS tipo_conta,
        c.nome,
        f.res_partner_bank_id,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '01' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_01,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '02' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_02,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '03' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_03,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '04' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_04,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '05' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_05,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '06' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_06,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '07' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_07,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '08' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_08,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '09' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_09,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '10' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_10,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '11' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_11,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '12' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_12,
        0 AS vencido_01,
        0 AS vencido_02,
        0 AS vencido_03,
        0 AS vencido_04,
        0 AS vencido_05,
        0 AS vencido_06,
        0 AS vencido_07,
        0 AS vencido_08,
        0 AS vencido_09,
        0 AS vencido_10,
        0 AS vencido_11,
        0 AS vencido_12
    FROM finan_fluxo_mensal_diario f
        JOIN finan_lancamento fl ON fl.id = f.lancamento_id
        JOIN finan_conta fc ON fl.tipo = 'T' AND fc.id = f.conta_id OR fl.tipo <> 'T' AND fc.id = fl.conta_id
        JOIN finan_conta_arvore ca ON fl.tipo = 'T' AND ca.conta_id = f.conta_id OR fl.tipo <> 'T' AND ca.conta_id = fl.conta_id
        JOIN finan_conta c ON c.id = ca.conta_pai_id
    WHERE f.tipo = 'Q'
    UNION ALL
    SELECT l.company_id,
        f.data,
        f.provisionado,
        c.id,
        c.codigo_completo,
        COALESCE(c.sintetica, false) AS sintetica,
        f.tipo,
        fc.tipo AS tipo_conta,
        c.nome,
        f.res_partner_bank_id,
        0 AS quitado_01,
        0 AS quitado_02,
        0 AS quitado_03,
        0 AS quitado_04,
        0 AS quitado_05,
        0 AS quitado_06,
        0 AS quitado_07,
        0 AS quitado_08,
        0 AS quitado_09,
        0 AS quitado_10,
        0 AS quitado_11,
        0 AS quitado_12,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '01' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_01,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '02' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_02,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '03' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_03,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '04' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_04,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '05' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_05,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '06' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_06,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '07' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_07,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '08' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_08,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '09' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_09,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '10' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_10,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '11' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_11,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '12' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_12
    FROM finan_fluxo_mensal_diario f
        JOIN finan_lancamento l ON l.id = f.lancamento_id
        JOIN finan_conta fc ON fc.id = l.conta_id
        JOIN finan_conta_arvore ca ON ca.conta_id = l.conta_id
        JOIN finan_conta c ON c.id = ca.conta_pai_id
    WHERE f.tipo = 'V';
"""


SQL_VIEW_FINAN_FLUXO_CAIXA_SINTETICO_RATEIO = """
    CREATE OR REPLACE VIEW finan_fluxo_caixa_sintetico_rateio AS
    SELECT fl.company_id,
        f.data,
        f.provisionado,
        c.id,
        c.codigo_completo,
        COALESCE(c.sintetica, false) AS sintetica,
        f.tipo,
        fc.tipo AS tipo_conta,
        c.nome,
        f.res_partner_bank_id,
        f.conta_id,
        f.centrocusto_id,
        f.hr_contract_id,
        f.hr_department_id,

        f.veiculo_id,
        f.project_id,

        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '01' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_01,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '02' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_02,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '03' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_03,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '04' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_04,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '05' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_05,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '06' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_06,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '07' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_07,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '08' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_08,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '09' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_09,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '10' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_10,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '11' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_11,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '12' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS quitado_12,
        0 AS vencido_01,
        0 AS vencido_02,
        0 AS vencido_03,
        0 AS vencido_04,
        0 AS vencido_05,
        0 AS vencido_06,
        0 AS vencido_07,
        0 AS vencido_08,
        0 AS vencido_09,
        0 AS vencido_10,
        0 AS vencido_11,
        0 AS vencido_12
    FROM finan_fluxo_mensal_diario_rateio f
        JOIN finan_lancamento fl ON fl.id = f.lancamento_id
        JOIN finan_conta fc ON fc.id = f.conta_id
        JOIN finan_conta_arvore ca ON ca.conta_id = f.conta_id
        JOIN finan_conta c ON c.id = ca.conta_pai_id
    WHERE f.tipo = 'Q'
    UNION ALL
    SELECT l.company_id,
        f.data,
        f.provisionado,
        c.id,
        c.codigo_completo,
        COALESCE(c.sintetica, false) AS sintetica,
        f.tipo,
        fc.tipo AS tipo_conta,
        c.nome,
        f.res_partner_bank_id,
        f.conta_id,
        f.centrocusto_id,
        f.hr_contract_id,
        f.hr_department_id,

        f.veiculo_id,
        f.project_id,

        0 AS quitado_01,
        0 AS quitado_02,
        0 AS quitado_03,
        0 AS quitado_04,
        0 AS quitado_05,
        0 AS quitado_06,
        0 AS quitado_07,
        0 AS quitado_08,
        0 AS quitado_09,
        0 AS quitado_10,
        0 AS quitado_11,
        0 AS quitado_12,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '01' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_01,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '02' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_02,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '03' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_03,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '04' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_04,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '05' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_05,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '06' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_06,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '07' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_07,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '08' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_08,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '09' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_09,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '10' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_10,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '11' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_11,
        COALESCE(
            CASE
                WHEN to_char(f.data, 'MM') = '12' THEN COALESCE(f.valor_entrada, 0) - COALESCE(f.valor_saida, 0)
                ELSE 0.00
            END, 0.00) AS vencido_12
    FROM finan_fluxo_mensal_diario_rateio f
        JOIN finan_lancamento l ON l.id = f.lancamento_id
        JOIN finan_conta fc ON fc.id = l.conta_id
        JOIN finan_conta_arvore ca ON ca.conta_id = l.conta_id
        JOIN finan_conta c ON c.id = ca.conta_pai_id
    WHERE f.tipo = 'V';
"""


SQL_VIEW_FINAN_FLUXO_MENSAL_DIARIO = """
    CREATE OR REPLACE VIEW finan_fluxo_mensal_diario AS
    SELECT e.id,
        to_char(e.data_compensacao::timestamp with time zone, 'yyyy/mm'::text) AS mes,
        e.data_compensacao AS data,
        e.valor_compensado AS valor_entrada,
        0 AS valor_saida,
        false AS provisionado,
        e.company_id,
        'Q'::text AS tipo,
        e.lancamento_id,
        e.res_partner_bank_id,
        e.conta_id
    FROM finan_entrada_lote e
    WHERE e.data_quitacao IS NOT NULL
    UNION
    SELECT s.id,
        to_char(s.data_compensacao::timestamp with time zone, 'yyyy/mm'::text) AS mes,
        s.data_compensacao AS data,
        0 AS valor_entrada,
        s.valor_compensado AS valor_saida,
        false AS provisionado,
        s.company_id,
        'Q'::text AS tipo,
        s.lancamento_id,
        s.res_partner_bank_id,
        s.conta_id
    FROM finan_saida_lote s
    WHERE s.data_quitacao IS NOT NULL
    UNION
    SELECT l.id,
        to_char(l.data_vencimento::timestamp with time zone, 'yyyy/mm'::text) AS mes,
        l.data_vencimento AS data,
            CASE
                WHEN l.tipo::text = 'R'::text THEN COALESCE(l.valor_saldo, 0::numeric)
                ELSE 0::numeric
            END AS valor_entrada,
            CASE
                WHEN l.tipo::text = 'P'::text THEN COALESCE(l.valor_saldo, 0::numeric)
                ELSE 0::numeric
            END AS valor_saida,
        l.provisionado,
        l.company_id,
        'V'::text AS tipo,
        l.id AS lancamento_id,
        NULL::integer AS res_partner_bank_id,
        l.conta_id
    FROM finan_lancamento l
    WHERE (l.tipo::text = ANY (ARRAY['R'::character varying::text, 'P'::character varying::text])) AND (l.situacao::text = ANY (ARRAY['Vencido'::character varying::text, 'A vencer'::character varying::text, 'Vence hoje'::character varying::text]));
"""


SQL_VIEW_FINAN_FLUXO_MENSAL_DIARIO_RATEIO = """
    CREATE OR REPLACE VIEW finan_fluxo_mensal_diario_rateio AS
    SELECT e.id,
        to_char(e.data_compensacao, 'yyyy/mm') AS mes,
        e.data_compensacao AS data,
        cast((cast(coalesce(e.valor_compensado, 0) as numeric) * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric)) as numeric) AS valor_entrada,
        0 AS valor_saida,
        false AS provisionado,
        coalesce(rateio.company_id, e.company_id) as company_id,
        'Q' AS tipo,
        e.lancamento_id,
        e.res_partner_bank_id,
        coalesce(rateio.conta_id, e.conta_id) as conta_id,
        rateio.centrocusto_id,
        rateio.hr_contract_id,
        rateio.hr_department_id,

        rateio.veiculo_id,
        rateio.project_id

    FROM
        finan_entrada_lote e
        left join finan_pagamento_rateio_folha rateio on rateio.lancamento_id = e.lancamento_id

    WHERE
        e.data_quitacao IS NOT NULL

    UNION

    SELECT s.id,
        to_char(s.data_compensacao, 'yyyy/mm') AS mes,
        s.data_compensacao AS data,
        0 AS valor_entrada,
        cast((cast(coalesce(s.valor_compensado, 0) as numeric) * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric)) as numeric) AS valor_saida,
        false AS provisionado,
        coalesce(rateio.company_id, s.company_id) as company_id,
        'Q' AS tipo,
        s.lancamento_id,
        s.res_partner_bank_id,
        coalesce(rateio.conta_id, s.conta_id) as conta_id,
        rateio.centrocusto_id,
        rateio.hr_contract_id,
        rateio.hr_department_id,

        rateio.veiculo_id,
        rateio.project_id

    FROM
        finan_saida_lote s
        left join finan_pagamento_rateio_folha rateio on rateio.lancamento_id = s.lancamento_id

    WHERE
        s.data_quitacao IS NOT NULL

    UNION

    SELECT l.id,
        to_char(l.data_vencimento, 'yyyy/mm') AS mes,
        l.data_vencimento AS data,
            CASE
                WHEN l.tipo = 'R' THEN COALESCE(l.valor_saldo, 0)
                ELSE 0
            END * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) AS valor_entrada,
            CASE
                WHEN l.tipo = 'P' THEN COALESCE(l.valor_saldo, 0)
                ELSE 0
            END * cast(coalesce(rateio.porcentagem, 100) as numeric) / cast(100 as numeric) AS valor_saida,
        l.provisionado,
        coalesce(rateio.company_id, l.company_id) as company_id,
        'V' AS tipo,
        l.id AS lancamento_id,
        NULL::integer AS res_partner_bank_id,
        coalesce(rateio.conta_id, l.conta_id) as conta_id,
        rateio.centrocusto_id,
        rateio.hr_contract_id,
        rateio.hr_department_id,

        rateio.veiculo_id,
        rateio.project_id

    FROM
        finan_lancamento l
        LEFT JOIN finan_lancamento_rateio_geral_folha rateio on rateio.lancamento_id = l.id
    WHERE
        (l.tipo = 'R' or l.tipo = 'P')
        and (l.situacao = 'Vencido' or l.situacao = 'A vencer' or l.situacao = 'Vence hoje');
"""


SQL_VIEW_FINAN_LANCAMENTO_LOTE_DIVIDA_PAGAMENTO = """
    CREATE OR REPLACE VIEW finan_lancamento_lote_divida_pagamento AS
    SELECT lote.id AS lote_id,
        divida.id AS divida_id,
        pagamento.id AS pagamento_id,
        (COALESCE(divida.valor_documento, 0::numeric) - (( SELECT COALESCE(sum(COALESCE(p.valor_documento, 0::numeric)), 0::numeric) AS "coalesce"
            FROM finan_lancamento p
            WHERE (p.tipo::text = ANY (ARRAY['PP'::character varying::text, 'PR'::character varying::text])) AND p.lancamento_id = divida.id))) /
            CASE
                WHEN lote.valor_documento > 0::numeric THEN COALESCE(lote.valor_documento, 1::numeric)
                ELSE 1::numeric
            END AS porcentagem
    FROM finan_lancamento lote
        JOIN finan_lancamento divida ON divida.lancamento_id = lote.id AND (divida.tipo::text = ANY (ARRAY['R'::character varying::text, 'P'::character varying::text]))
        JOIN finan_lancamento pagamento ON pagamento.lancamento_id = lote.id AND (pagamento.tipo::text = ANY (ARRAY['PR'::character varying::text, 'PP'::character varying::text]))
    WHERE lote.tipo::text = ANY (ARRAY['LP'::character varying::text, 'LR'::character varying::text]);
"""


SQL_VIEW_FINAN_LANCAMENTO_RATEIO_GERAL = """
    CREATE OR REPLACE VIEW finan_lancamento_rateio_geral AS
    SELECT l.id AS lancamento_id,
        l.company_id,
        l.conta_id,
        l.centrocusto_id,
        100.00 AS porcentagem
    FROM finan_lancamento l
    WHERE NOT (EXISTS ( SELECT r.id
            FROM finan_lancamento_rateio r
            WHERE r.lancamento_id = l.id))
    UNION ALL
    SELECT r.lancamento_id,
        r.company_id,
        r.conta_id,
        r.centrocusto_id,
        sum(COALESCE(r.porcentagem, 0::numeric)) AS porcentagem
    FROM finan_lancamento_rateio r
    GROUP BY r.lancamento_id, r.company_id, r.conta_id, r.centrocusto_id
    ORDER BY 1, 2, 3, 4;
"""


SQL_VIEW_FINAN_LANCAMENTO_RATEIO_GERAL_FOLHA = """
    CREATE OR REPLACE VIEW finan_lancamento_rateio_geral_folha AS
    SELECT l.id * (-1) AS id,
        l.id AS lancamento_id,
        l.company_id,
        l.conta_id,
        l.centrocusto_id,
        NULL AS hr_contract_id,
        NULL AS hr_department_id,
        NULL AS veiculo_id,
        NULL AS project_id,
        cast(100.00 as numeric) AS porcentagem
    FROM finan_lancamento l
    WHERE NOT (EXISTS ( SELECT r.id
            FROM finan_lancamento_rateio r
            WHERE r.lancamento_id = l.id))
    UNION ALL
    SELECT r.id,
        r.lancamento_id,
        r.company_id,
        r.conta_id,
        r.centrocusto_id,
        r.hr_contract_id,
        r.hr_department_id,
        r.veiculo_id,
        r.project_id,
        sum(cast(COALESCE(r.porcentagem, 0) as numeric)) AS porcentagem
    FROM finan_lancamento_rateio r
    GROUP BY r.id, r.lancamento_id, r.company_id, r.conta_id, r.centrocusto_id, r.hr_contract_id, r.project_id, r.hr_department_id, r.veiculo_id
    ORDER BY 1, 2, 3, 4, 5, 6;
"""


SQL_VIEW_FINAN_PAGAMENTO_RATEIO = """
    CREATE OR REPLACE VIEW finan_pagamento_rateio AS
    SELECT rateio.id,
        divida.id AS lancamento_id,
        divida.tipo,
        pagamento.data_quitacao,
        pagamento.data,
        pagamento.res_partner_bank_id,
            CASE
                WHEN pagamento.data IS NOT NULL THEN pagamento.data
                ELSE pagamento.data_quitacao
            END AS data_compensacao,
        divida.data_vencimento,
        rateio.company_id,
        rateio.conta_id,
        rateio.centrocusto_id,
        rateio.porcentagem,
            CASE
                WHEN pagamento.valor_documento = 0::numeric THEN 0::numeric
                ELSE pagamento.valor_documento * rateio.porcentagem / 100.00
            END AS valor_documento,
            CASE
                WHEN pagamento.valor = 0::numeric THEN 0::numeric
                ELSE pagamento.valor * rateio.porcentagem / 100.00
            END AS valor,
        divida.valor * rateio.porcentagem / 100.00 AS valor_original,
        divida.valor_documento * rateio.porcentagem / 100.00 AS valor_documento_original,
        divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original,
        pagamento.id as pagamento_id,
        null as lote_id

    FROM finan_lancamento_rateio_geral_folha rateio
        JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['P'::character varying::text, 'R'::character varying::text]))
        JOIN finan_lancamento pagamento ON pagamento.lancamento_id = divida.id AND (pagamento.tipo::text = ANY (ARRAY['PR'::character varying::text, 'PP'::character varying::text]))
    UNION ALL
    SELECT rateio.id,
        divida.id AS lancamento_id,
        divida.tipo,
        pagamento.data_quitacao,
        pagamento.data,
        pagamento.res_partner_bank_id,
            CASE
                WHEN pagamento.data IS NOT NULL THEN pagamento.data
                ELSE pagamento.data_quitacao
            END AS data_compensacao,
        divida.data_vencimento,
        rateio.company_id,
        rateio.conta_id,
        rateio.centrocusto_id,
        rateio.porcentagem,
            CASE
                WHEN pagamento.valor_documento = 0::numeric THEN 0::numeric
                ELSE pagamento.valor_documento * (divida.valor_documento / pagamento.valor_documento) * rateio.porcentagem / 100.00
            END AS valor_documento,
            CASE
                WHEN pagamento.valor = 0::numeric THEN 0::numeric
                ELSE pagamento.valor * (divida.valor / pagamento.valor) * rateio.porcentagem / 100.00
            END AS valor,
        divida.valor_documento * rateio.porcentagem / 100.00 AS valor_original,
        divida.valor * rateio.porcentagem / 100.00 AS valor_documento_original,
        divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original,
        pagamento.id as pagamento_id,
        lote.id as lote_id

    FROM finan_lancamento_rateio_geral_folha rateio
        JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['P'::character varying::text, 'R'::character varying::text]))
        JOIN finan_lancamento lote ON lote.id = divida.lancamento_id AND (lote.tipo::text = ANY (ARRAY['LP'::character varying::text, 'LR'::character varying::text]))
        JOIN finan_lancamento pagamento ON pagamento.lancamento_id = lote.id AND (pagamento.tipo::text = ANY (ARRAY['PP'::character varying::text, 'PR'::character varying::text]))
    UNION ALL
    SELECT rateio.id,
        divida.id AS lancamento_id,
        divida.tipo,
        divida.data_quitacao,
        divida.data,
        divida.res_partner_bank_id,
            CASE
                WHEN divida.data IS NOT NULL THEN divida.data
                ELSE divida.data_quitacao
            END AS data_compensacao,
        divida.data_vencimento,
        rateio.company_id,
        rateio.conta_id,
        rateio.centrocusto_id,
        rateio.porcentagem,
        divida.valor_documento * rateio.porcentagem / 100.00 AS valor_documento,
        divida.valor * rateio.porcentagem / 100.00 AS valor,
        divida.valor * rateio.porcentagem / 100.00 AS valor_original,
        divida.valor_documento * rateio.porcentagem / 100.00 AS valor_documento_original,
        divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original,
        null as pagamento_id,
        null as lote_id
    FROM finan_lancamento_rateio_geral_folha rateio
        JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['E'::character varying::text, 'S'::character varying::text]));
"""


SQL_VIEW_FINAN_PAGAMENTO_RATEIO_FOLHA = """
    CREATE OR REPLACE VIEW finan_pagamento_rateio_folha AS
    SELECT rateio.id,
        divida.id AS lancamento_id,
        divida.tipo,
        pagamento.data_quitacao,
        pagamento.data,
        pagamento.res_partner_bank_id,
            CASE
                WHEN pagamento.data IS NOT NULL THEN pagamento.data
                ELSE pagamento.data_quitacao
            END AS data_compensacao,
        divida.data_vencimento,
        rateio.company_id,
        rateio.conta_id,
        rateio.centrocusto_id,
        rateio.hr_contract_id,
        rateio.hr_department_id,

        rateio.veiculo_id,
        rateio.project_id,
        rateio.porcentagem,
            CASE
                WHEN pagamento.valor_documento = 0::numeric OR pagamento.valor_documento IS NULL THEN 0::numeric
                ELSE pagamento.valor_documento * rateio.porcentagem / 100.00
            END AS valor_documento,
            CASE
                WHEN pagamento.valor = 0::numeric OR pagamento.valor IS NULL THEN 0::numeric
                ELSE pagamento.valor * rateio.porcentagem / 100.00
            END AS valor,
            CASE
                WHEN pagamento.valor_desconto = 0::numeric OR pagamento.valor_desconto IS NULL THEN 0::numeric
                ELSE pagamento.valor_desconto * rateio.porcentagem / 100.00
            END AS valor_desconto,
            CASE
                WHEN pagamento.valor_juros = 0::numeric OR pagamento.valor_juros IS NULL THEN 0::numeric
                ELSE pagamento.valor_juros * rateio.porcentagem / 100.00
            END AS valor_juros,
            CASE
                WHEN pagamento.valor_multa = 0::numeric OR pagamento.valor_multa IS NULL THEN 0::numeric
                ELSE pagamento.valor_multa * rateio.porcentagem / 100.00
            END AS valor_multa,
        divida.valor * rateio.porcentagem / 100.00 AS valor_original,
        divida.valor_documento * rateio.porcentagem / 100.00 AS valor_documento_original,
        divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original,
        pagamento.id as pagamento_id,
        null as lote_id

    FROM finan_lancamento_rateio_geral_folha rateio
        JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['P'::character varying::text, 'R'::character varying::text]))
        JOIN finan_lancamento pagamento ON pagamento.lancamento_id = divida.id AND (pagamento.tipo::text = ANY (ARRAY['PR'::character varying::text, 'PP'::character varying::text]))
    UNION ALL
    SELECT rateio.id,
        divida.id AS lancamento_id,
        divida.tipo,
        pagamento.data_quitacao,
        pagamento.data,
        pagamento.res_partner_bank_id,
            CASE
                WHEN pagamento.data IS NOT NULL THEN pagamento.data
                ELSE pagamento.data_quitacao
            END AS data_compensacao,
        divida.data_vencimento,
        rateio.company_id,
        rateio.conta_id,
        rateio.centrocusto_id,
        rateio.hr_contract_id,
        rateio.hr_department_id,

        rateio.veiculo_id,
        rateio.project_id,
        rateio.porcentagem,
            CASE
                WHEN pagamento.valor_documento = 0::numeric OR pagamento.valor_documento IS NULL THEN 0::numeric
                ELSE pagamento.valor_documento * (divida.valor_documento / pagamento.valor_documento) * rateio.porcentagem / 100.00
            END AS valor_documento,
            CASE
                WHEN pagamento.valor = 0::numeric OR pagamento.valor IS NULL THEN 0::numeric
                ELSE pagamento.valor * (divida.valor_documento / pagamento.valor_documento) * rateio.porcentagem / 100.00
            END AS valor,
            CASE
                WHEN pagamento.valor_desconto = 0::numeric OR pagamento.valor_desconto IS NULL THEN 0::numeric
                ELSE pagamento.valor_desconto * (divida.valor_documento / pagamento.valor_documento) * rateio.porcentagem / 100.00
            END AS valor_desconto,
            CASE
                WHEN pagamento.valor_juros = 0::numeric OR pagamento.valor_juros IS NULL THEN 0::numeric
                ELSE pagamento.valor_juros * (divida.valor_documento / pagamento.valor_documento) * rateio.porcentagem / 100.00
            END AS valor_juros,
            CASE
                WHEN pagamento.valor_multa = 0::numeric OR pagamento.valor_multa IS NULL THEN 0::numeric
                ELSE pagamento.valor_multa * (divida.valor_documento / pagamento.valor_documento) * rateio.porcentagem / 100.00
            END AS valor_multa,
        divida.valor_documento * rateio.porcentagem / 100.00 AS valor_original,
        divida.valor * rateio.porcentagem / 100.00 AS valor_documento_original,
        divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original,
        pagamento.id as pagamento_id,
        lote.id as lote_id

    FROM finan_lancamento_rateio_geral_folha rateio
        JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['P'::character varying::text, 'R'::character varying::text]))
        JOIN finan_lancamento lote ON lote.id = divida.lancamento_id AND (lote.tipo::text = ANY (ARRAY['LP'::character varying::text, 'LR'::character varying::text]))
        JOIN finan_lancamento pagamento ON pagamento.lancamento_id = lote.id AND (pagamento.tipo::text = ANY (ARRAY['PP'::character varying::text, 'PR'::character varying::text]))
    UNION ALL
    SELECT rateio.id,
        divida.id AS lancamento_id,
        divida.tipo,
        divida.data_quitacao,
        divida.data,
        divida.res_partner_bank_id,
            CASE
                WHEN divida.data IS NOT NULL THEN divida.data
                ELSE divida.data_quitacao
            END AS data_compensacao,
        divida.data_vencimento,
        rateio.company_id,
        rateio.conta_id,
        rateio.centrocusto_id,
        rateio.hr_contract_id,
        rateio.hr_department_id,

        rateio.veiculo_id,
        rateio.project_id,
        rateio.porcentagem,
        divida.valor * rateio.porcentagem / 100.00 AS valor_documento,
        divida.valor * rateio.porcentagem / 100.00 AS valor,
        COALESCE(divida.valor_desconto, 0::numeric) * rateio.porcentagem / 100.00 AS valor_desconto,
        COALESCE(divida.valor_juros, 0::numeric) * rateio.porcentagem / 100.00 AS valor_juros,
        COALESCE(divida.valor_multa, 0::numeric) * rateio.porcentagem / 100.00 AS valor_multa,
        divida.valor * rateio.porcentagem / 100.00 AS valor_original,
        divida.valor * rateio.porcentagem / 100.00 AS valor_documento_original,
        divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original,
        null as pagamento_id,
        null as lote_id

    FROM finan_lancamento_rateio_geral_folha rateio
        JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['E'::character varying::text, 'S'::character varying::text]));
"""


SQL_VIEW_FINAN_PAGAMENTO_RESUMO = """
    CREATE OR REPLACE VIEW finan_pagamento_resumo AS
    SELECT max(f.id) AS id,
        f.tipo,
        f.lancamento_id,
        max(f.data_quitacao) AS data_quitacao,
        COALESCE(sum(COALESCE(f.valor_multa, 0::numeric)), 0::numeric) AS valor_multa,
        COALESCE(sum(COALESCE(f.valor_juros, 0::numeric)), 0::numeric) AS valor_juros,
        COALESCE(sum(COALESCE(f.valor_desconto, 0::numeric)), 0::numeric) AS valor_desconto,
        COALESCE(sum(COALESCE(f.valor, 0::numeric)), 0::numeric) AS valor,
        COALESCE(sum(COALESCE(f.valor_documento, 0::numeric)), 0::numeric) AS valor_documento,
        ( SELECT ff.res_partner_bank_id
            FROM finan_lancamento ff
            WHERE ff.id = max(f.id)) AS res_partner_bank_id,
        ( SELECT ff.formapagamento_id
            FROM finan_lancamento ff
            WHERE ff.id = max(f.id)) AS formapagamento_id
    FROM finan_lancamento f
    WHERE f.tipo::text = ANY (ARRAY['PP'::character varying::text, 'PR'::character varying::text])
    GROUP BY f.lancamento_id, f.tipo;
"""


SQL_VIEW_FINAN_SAIDA = """
    CREATE OR REPLACE VIEW finan_saida AS
    SELECT 'S'::text AS tipo,
        e.id,
        e.data_documento,
        e.numero_documento,
        e.data_quitacao AS data_vencimento,
        e.data_quitacao,
        e.data AS data_compensacao,
        e.valor_documento,
        e.valor AS valor_compensado,
        e.valor_multa,
        e.valor_juros,
        e.valor_desconto,
        e.partner_id,
        e.conta_id,
        e.res_partner_bank_id,
        e.conciliado,
        e.id AS lancamento_id,
        e.company_id
    FROM finan_lancamento e
    WHERE e.tipo::text = 'S'::text
    UNION
    SELECT 'T'::text AS tipo,
        te.id * (-1) AS id,
        te.data_documento,
        te.numero_documento,
        te.data AS data_vencimento,
        te.data AS data_quitacao,
        te.data AS data_compensacao,
        te.valor AS valor_documento,
        te.valor AS valor_compensado,
        COALESCE(te.valor_multa, 0::numeric) AS valor_multa,
        COALESCE(te.valor_juros, 0::numeric) AS valor_juros,
        COALESCE(te.valor_desconto, 0::numeric) AS valor_desconto,
        te.partner_id,
        COALESCE(te.conta_id, b.conta_id) AS conta_id,
        te.res_partner_bank_id,
        te.conciliado,
        te.id AS lancamento_id,
        te.company_id
    FROM finan_lancamento te
        JOIN res_partner_bank b ON b.id = te.res_partner_bank_id
    WHERE te.tipo::text = 'T'::text
    UNION
    SELECT 'P'::text AS tipo,
        pr.id,
        r.data_documento,
        r.numero_documento,
        r.data_vencimento,
        pr.data_quitacao,
        COALESCE(pr.data, pr.data_quitacao) AS data_compensacao,
        pr.valor_documento,
        pr.valor AS valor_compensado,
        pr.valor_multa,
        pr.valor_juros,
        pr.valor_desconto,
        r.partner_id,
        r.conta_id,
        pr.res_partner_bank_id,
        pr.conciliado,
        pr.lancamento_id,
        r.company_id
    FROM finan_lancamento pr
        JOIN finan_lancamento r ON r.id = pr.lancamento_id
    WHERE pr.tipo::text = 'PP'::text;
"""


SQL_VIEW_FINAN_SAIDA_LOTE = """
    CREATE OR REPLACE VIEW finan_saida_lote AS
    SELECT
        s.tipo,
        s.id,
        s.data_documento,
        coalesce(fl.numero_documento, s.numero_documento) as numero_documento,
        s.data_vencimento,
        s.data_quitacao,
        s.data_compensacao,
        cast(cast(coalesce(s.valor_documento, 0) as numeric) * cast(coalesce(ldp.porcentagem, 1) as numeric) as numeric) as valor_documento,
        cast(cast(coalesce(s.valor_compensado, 0) as numeric) * cast(coalesce(ldp.porcentagem, 1) as numeric) as numeric) as valor_compensado,
        cast(cast(coalesce(s.valor_multa, 0) as numeric) * cast(coalesce(ldp.porcentagem, 1) as numeric) as numeric) as valor_multa,
        cast(cast(coalesce(s.valor_juros, 0) as numeric) * cast(coalesce(ldp.porcentagem, 1) as numeric) as numeric) as valor_juros,
        cast(cast(coalesce(s.valor_desconto, 0) as numeric) * cast(coalesce(ldp.porcentagem, 1) as numeric) as numeric) as valor_desconto,
        coalesce(fl.partner_id, s.partner_id) as partner_id,
        coalesce(fl.conta_id, s.conta_id) as conta_id,
        s.res_partner_bank_id,
        s.conciliado,
        coalesce(fl.id, s.lancamento_id) as lancamento_id,
        coalesce(fl.company_id, s.company_id) as company_id,
        coalesce(ldp.porcentagem, 1) as porcentagem

    FROM
        finan_saida s
        left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = s.id and ldp.lote_id = s.lancamento_id
        left join finan_lancamento fl on (ldp.divida_id is not null and fl.id = ldp.divida_id) or (ldp.divida_id is null and fl.id = s.lancamento_id);
"""


SQL_VIEW_FINAN_SALDO_BANCARIO_HOJE = """
    CREATE OR REPLACE VIEW finan_saldo_bancario_hoje AS
    SELECT b.id,
        b.company_id,
        b.id AS res_partner_bank_id,
        b.state AS tipo,
        COALESCE(s.saldo_final, 0::numeric) + COALESCE(( SELECT sum(e.credito) AS sum
            FROM finan_saldo_resumo_data_quitacao e
            WHERE e.res_partner_bank_id = b.id AND e.data_quitacao > s.data AND e.data_quitacao < 'now'::text::date), 0::numeric) - COALESCE(( SELECT sum(e.debito) AS sum
            FROM finan_saldo_resumo_data_quitacao e
            WHERE e.res_partner_bank_id = b.id AND e.data_quitacao > s.data AND e.data_quitacao < 'now'::text::date), 0::numeric) AS saldo_anterior,
        COALESCE(( SELECT sum(e.credito) AS sum
            FROM finan_saldo_resumo_data_quitacao e
            WHERE e.res_partner_bank_id = b.id AND e.data_quitacao = 'now'::text::date), 0::numeric) AS credito,
        COALESCE(( SELECT sum(e.debito) AS sum
            FROM finan_saldo_resumo_data_quitacao e
            WHERE e.res_partner_bank_id = b.id AND e.data_quitacao = 'now'::text::date), 0::numeric) AS debito,
        COALESCE(s.saldo_final, 0::numeric) + COALESCE(( SELECT sum(e.credito) AS sum
            FROM finan_saldo_resumo_data_quitacao e
            WHERE e.res_partner_bank_id = b.id AND e.data_quitacao > s.data AND e.data_quitacao <= 'now'::text::date), 0::numeric) - COALESCE(( SELECT sum(e.debito) AS sum
            FROM finan_saldo_resumo_data_quitacao e
            WHERE e.res_partner_bank_id = b.id AND e.data_quitacao > s.data AND e.data_quitacao <= 'now'::text::date), 0::numeric) AS saldo
    FROM res_partner_bank b
        JOIN finan_saldo s ON s.res_partner_bank_id = b.id AND s.data = (( SELECT max(ss.data) AS max
            FROM finan_saldo ss
            WHERE ss.res_partner_bank_id = b.id AND ss.data < 'now'::text::date))
    ORDER BY b.bank_name;
"""


SQL_VIEW_FINAN_SALDO_QUITACAO = """
    CREATE OR REPLACE VIEW finan_saldo_quitacao AS
    SELECT e.res_partner_bank_id,
        e.data_quitacao,
        sum(e.valor_documento_credito) AS valor_documento_credito,
        sum(e.valor_compensado_credito) AS valor_compensado_credito,
        sum(e.valor_multa_credito) AS valor_multa_credito,
        sum(e.valor_juros_credito) AS valor_juros_credito,
        sum(e.valor_desconto_credito) AS valor_desconto_credito,
        sum(e.valor_documento_debito) AS valor_documento_debito,
        sum(e.valor_compensado_debito) AS valor_compensado_debito,
        sum(e.valor_multa_debito) AS valor_multa_debito,
        sum(e.valor_juros_debito) AS valor_juros_debito,
        sum(e.valor_desconto_debito) AS valor_desconto_debito,
        sum(e.valor_documento_credito - e.valor_documento_debito) AS valor_documento_saldo,
        sum(e.valor_compensado_credito - e.valor_compensado_debito) AS valor_compensado_saldo,
        sum(e.valor_multa_credito - e.valor_multa_debito) AS valor_multa_saldo,
        sum(e.valor_juros_credito - e.valor_juros_debito) AS valor_juros_saldo,
        sum(e.valor_desconto_credito - e.valor_desconto_debito) AS valor_desconto_saldo
    FROM finan_extrato e
    GROUP BY e.res_partner_bank_id, e.data_quitacao;
"""


SQL_VIEW_FINAN_SALDO_QUITACAO_EMPRESA_BANCO = """
    CREATE OR REPLACE VIEW finan_saldo_quitacao_empresa_banco AS
    SELECT e.company_id,
        e.res_partner_bank_id,
        e.data_quitacao,
        sum(e.valor_documento_credito) AS valor_documento_credito,
        sum(e.valor_compensado_credito) AS valor_compensado_credito,
        sum(e.valor_multa_credito) AS valor_multa_credito,
        sum(e.valor_juros_credito) AS valor_juros_credito,
        sum(e.valor_desconto_credito) AS valor_desconto_credito,
        sum(e.valor_documento_debito) AS valor_documento_debito,
        sum(e.valor_compensado_debito) AS valor_compensado_debito,
        sum(e.valor_multa_debito) AS valor_multa_debito,
        sum(e.valor_juros_debito) AS valor_juros_debito,
        sum(e.valor_desconto_debito) AS valor_desconto_debito,
        sum(e.valor_documento_credito - e.valor_documento_debito) AS valor_documento_saldo,
        sum(e.valor_compensado_credito - e.valor_compensado_debito) AS valor_compensado_saldo,
        sum(e.valor_multa_credito - e.valor_multa_debito) AS valor_multa_saldo,
        sum(e.valor_juros_credito - e.valor_juros_debito) AS valor_juros_saldo,
        sum(e.valor_desconto_credito - e.valor_desconto_debito) AS valor_desconto_saldo
    FROM finan_extrato e
    GROUP BY e.company_id, e.res_partner_bank_id, e.data_quitacao;
"""


SQL_VIEW_FINAN_SALDO_RESUMO = """
    CREATE OR REPLACE VIEW finan_saldo_resumo AS
    SELECT e.res_partner_bank_id::character varying::text || to_char(e.data_compensacao::timestamp with time zone, 'YYYYmmdd'::text) AS id,
        e.res_partner_bank_id,
        e.data_compensacao,
        COALESCE(( SELECT sum(ee.valor_compensado_credito - ee.valor_compensado_debito) AS sum
            FROM finan_extrato ee
            WHERE ee.data_compensacao IS NOT NULL AND ee.res_partner_bank_id = e.res_partner_bank_id AND ee.data_compensacao < e.data_compensacao AND ee.conciliado = true), 0::numeric) AS saldo_anterior,
        sum(e.valor_compensado_credito) AS credito,
        sum(e.valor_compensado_debito) AS debito,
        COALESCE(( SELECT sum(ee.valor_compensado_credito - ee.valor_compensado_debito) AS sum
            FROM finan_extrato ee
            WHERE ee.data_compensacao IS NOT NULL AND ee.res_partner_bank_id = e.res_partner_bank_id AND ee.data_compensacao <= e.data_compensacao AND ee.conciliado = true), 0::numeric) AS saldo
    FROM finan_extrato e
        JOIN res_partner_bank b ON b.id = e.res_partner_bank_id
    WHERE e.data_compensacao IS NOT NULL AND e.conciliado = true
    GROUP BY e.res_partner_bank_id, e.data_compensacao
    ORDER BY e.res_partner_bank_id, e.data_compensacao;
"""


SQL_VIEW_FINAN_SALDO_RESUMO_DATA_QUITACAO = """
    CREATE OR REPLACE VIEW finan_saldo_resumo_data_quitacao AS
    SELECT e.res_partner_bank_id::character varying::text || to_char(e.data_quitacao::timestamp with time zone, 'YYYYmmdd'::text) AS id,
        e.res_partner_bank_id,
        e.data_quitacao,
        COALESCE(( SELECT sum(ee.valor_compensado_credito - ee.valor_compensado_debito) AS sum
            FROM finan_extrato ee
            WHERE ee.res_partner_bank_id = e.res_partner_bank_id AND ee.data_quitacao < e.data_quitacao), 0::numeric) AS saldo_anterior,
        sum(e.valor_compensado_credito) AS credito,
        sum(e.valor_compensado_debito) AS debito,
        COALESCE(( SELECT sum(ee.valor_compensado_credito - ee.valor_compensado_debito) AS sum
            FROM finan_extrato ee
            WHERE ee.res_partner_bank_id = e.res_partner_bank_id AND ee.data_quitacao <= e.data_quitacao), 0::numeric) AS saldo
    FROM finan_extrato e
    WHERE e.data_quitacao IS NOT NULL
    GROUP BY e.res_partner_bank_id, e.data_quitacao
    ORDER BY e.res_partner_bank_id, e.data_quitacao;
"""


SQL_VIEW_FINAN_SALDO_RESUMO_DATA_QUITACAO_EMPRESA = """
    CREATE OR REPLACE VIEW finan_saldo_resumo_data_quitacao_empresa AS
    SELECT (e.company_id::character varying::text || e.res_partner_bank_id::character varying::text) || to_char(e.data_quitacao::timestamp with time zone, 'YYYYmmdd'::text) AS id,
        e.company_id,
        e.res_partner_bank_id,
        e.data_quitacao,
        COALESCE(( SELECT sum(ee.valor_compensado_credito - ee.valor_compensado_debito) AS sum
            FROM finan_extrato ee
            WHERE ee.company_id = e.company_id AND ee.res_partner_bank_id = e.res_partner_bank_id AND ee.data_quitacao < e.data_quitacao), 0::numeric) AS saldo_anterior,
        sum(e.valor_compensado_credito) AS credito,
        sum(e.valor_compensado_debito) AS debito,
        COALESCE(( SELECT sum(ee.valor_compensado_credito - ee.valor_compensado_debito) AS sum
            FROM finan_extrato ee
            WHERE ee.company_id = e.company_id AND ee.res_partner_bank_id = e.res_partner_bank_id AND ee.data_quitacao <= e.data_quitacao), 0::numeric) AS saldo
    FROM finan_extrato e
    WHERE e.data_quitacao IS NOT NULL
    GROUP BY e.company_id, e.res_partner_bank_id, e.data_quitacao
    ORDER BY e.company_id, e.res_partner_bank_id, e.data_quitacao;
"""


SQL_VIEW_FINAN_SALDO_RESUMO_FORMAPAGAMENTO = """
    CREATE OR REPLACE VIEW finan_saldo_resumo_formapagamento AS
    SELECT to_char(l.data_quitacao::timestamp with time zone, 'yyyymmdd'::text)::bigint * 1000000 + l.res_partner_bank_id * 1000 + l.formapagamento_id AS id,
        l.res_partner_bank_id,
        l.data_quitacao,
        l.formapagamento_id,
        sum(l.valor) AS valor
    FROM finan_lancamento l
    WHERE l.tipo::text = 'PR'::text
    GROUP BY l.res_partner_bank_id, l.data_quitacao, l.formapagamento_id;
"""



SQL_VIEW_GERAL = SQL_CRIA_ARVORE
SQL_VIEW_GERAL += """
    DROP VIEW IF EXISTS finan_conferencia_fluxo;
    DROP VIEW IF EXISTS finan_fluxo_caixa_sintetico_rateio;
    DROP VIEW IF EXISTS finan_fluxo_caixa_sintetico_departamento;
    DROP VIEW IF EXISTS finan_fluxo_caixa_sintetico;
    DROP VIEW IF EXISTS finan_fluxo_mensal_diario_rateio;
    DROP VIEW IF EXISTS finan_fluxo_mensal_diario;

    DROP VIEW IF EXISTS finan_contacorrente_rateio;

    DROP VIEW IF EXISTS finan_pagamento_rateio_folha;
    DROP VIEW IF EXISTS finan_pagamento_rateio;

    DROP VIEW IF EXISTS finan_lancamento_rateio_geral_folha;
    DROP VIEW IF EXISTS finan_lancamento_rateio_geral;

    DROP VIEW IF EXISTS finan_pagamento_resumo;

    DROP VIEW IF EXISTS finan_saldo_bancario_hoje;
    DROP VIEW IF EXISTS finan_saldo_resumo_formapagamento;
    DROP VIEW IF EXISTS finan_saldo_resumo_data_quitacao_empresa;
    DROP VIEW IF EXISTS finan_saldo_resumo_data_quitacao;
    DROP VIEW IF EXISTS finan_saldo_resumo;
    DROP VIEW IF EXISTS finan_saldo_quitacao_empresa_banco;
    DROP VIEW IF EXISTS finan_saldo_quitacao;

    DROP VIEW IF EXISTS finan_adiantamento_devolucao;
    DROP VIEW IF EXISTS finan_contacorrente;

    DROP VIEW IF EXISTS finan_saida_lote;
    DROP VIEW IF EXISTS finan_entrada_lote;
    DROP VIEW IF EXISTS finan_lancamento_lote_divida_pagamento;
    DROP VIEW IF EXISTS finan_extrato_fluxo;
    DROP VIEW IF EXISTS finan_extrato;
    DROP VIEW IF EXISTS finan_saida;
    DROP VIEW IF EXISTS finan_entrada;

"""

SQL_VIEW_GERAL += SQL_VIEW_FINAN_ENTRADA
SQL_VIEW_GERAL += SQL_VIEW_FINAN_SAIDA
SQL_VIEW_GERAL += SQL_VIEW_FINAN_EXTRATO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_LANCAMENTO_LOTE_DIVIDA_PAGAMENTO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_ENTRADA_LOTE
SQL_VIEW_GERAL += SQL_VIEW_FINAN_SAIDA_LOTE
SQL_VIEW_GERAL += SQL_VIEW_FINAN_EXTRATO_FLUXO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_CONTACORRENTE
SQL_VIEW_GERAL += SQL_VIEW_FINAN_ADIANTAMENTO_DEVOLUCAO

SQL_VIEW_GERAL += SQL_VIEW_FINAN_SALDO_QUITACAO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_SALDO_QUITACAO_EMPRESA_BANCO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_SALDO_RESUMO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_SALDO_RESUMO_DATA_QUITACAO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_SALDO_RESUMO_DATA_QUITACAO_EMPRESA
SQL_VIEW_GERAL += SQL_VIEW_FINAN_SALDO_RESUMO_FORMAPAGAMENTO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_SALDO_BANCARIO_HOJE

SQL_VIEW_GERAL += SQL_VIEW_FINAN_PAGAMENTO_RESUMO

SQL_VIEW_GERAL += SQL_VIEW_FINAN_LANCAMENTO_RATEIO_GERAL
SQL_VIEW_GERAL += SQL_VIEW_FINAN_LANCAMENTO_RATEIO_GERAL_FOLHA

SQL_VIEW_GERAL += SQL_VIEW_FINAN_PAGAMENTO_RATEIO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_PAGAMENTO_RATEIO_FOLHA

SQL_VIEW_GERAL += SQL_VIEW_FINAN_CONTACORRENTE_RATEIO

SQL_VIEW_GERAL += SQL_VIEW_FINAN_FLUXO_MENSAL_DIARIO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_FLUXO_MENSAL_DIARIO_RATEIO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_FLUXO_CAIXA_SINTETICO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_FLUXO_CAIXA_SINTETICO_DEPARTAMENTO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_FLUXO_CAIXA_SINTETICO_RATEIO
SQL_VIEW_GERAL += SQL_VIEW_FINAN_CONFERENCIA_FLUXO
