# -*- coding: utf-8 -*-

SQL_CONFERENCIA_ECONOMICA = """
DROP VIEW finan_rateio_economico_bi;

CREATE OR REPLACE VIEW finan_rateio_economico_bi AS
 SELECT
    pr.id,
    true AS controle,
    pr.lancamento_id,
    pr.tipo,
    pr.data_quitacao,
    pr.data_vencimento,
    pr.company_id,
    pr.conta_id,
    pr.centrocusto_id,
    pr.hr_contract_id,
    pr.porcentagem,
    CASE
        WHEN pr.tipo::text = 'P'::text OR pr.tipo::text = 'S'::text OR pr.tipo::text = 'PP'::text OR pr.tipo::text = 'LP'::text THEN pr.valor_documento * (-1)::numeric
        ELSE pr.valor_documento
    END AS valor_documento,
    CASE
        WHEN pr.tipo::text = 'P'::text OR pr.tipo::text = 'S'::text OR pr.tipo::text = 'PP'::text OR pr.tipo::text = 'LP'::text THEN pr.valor * (-1)::numeric
        ELSE pr.valor
    END AS valor,
    CASE
        WHEN pr.tipo::text = 'P'::text OR pr.tipo::text = 'S'::text OR pr.tipo::text = 'PP'::text OR pr.tipo::text = 'LP'::text THEN pr.valor_desconto
        ELSE pr.valor_desconto * (-1)::numeric
    END AS valor_desconto,
    CASE
        WHEN pr.tipo::text = 'P'::text OR pr.tipo::text = 'S'::text OR pr.tipo::text = 'PP'::text OR pr.tipo::text = 'LP'::text THEN pr.valor_juros * (-1)::numeric
        ELSE pr.valor_juros
    END AS valor_juros,
    CASE
        WHEN pr.tipo::text = 'P'::text OR pr.tipo::text = 'S'::text OR pr.tipo::text = 'PP'::text OR pr.tipo::text = 'LP'::text THEN pr.valor_multa * (-1)::numeric
        ELSE pr.valor_multa
    END AS valor_multa,
    pr.valor_original,
    pr.valor_documento_original,
    pr.saldo_original,
    c.parent_id AS grupo_id,
    ec.id AS econo_conta_id,
    pr.res_partner_bank_id as partner_bank_id

   FROM finan_pagamento_rateio_folha pr
     JOIN res_company c ON c.id = pr.company_id
     LEFT JOIN econo_conta ec ON ec.sintetica = false AND (ec.filtro_company_ids <> '|'::text OR ec.filtro_conta_ids <> '|'::text OR ec.filtro_centrocusto_ids <> '|'::text OR ec.filtro_contract_ids <> '|'::text OR ec.filtro_contract_exclui_ids <> '|'::text) AND (ec.filtro_company_ids = '|'::text OR pr.company_id IS NOT NULL AND ec.filtro_company_ids ~~ (('%|'::text || pr.company_id::character varying::text) || '|%'::text)) AND (ec.filtro_conta_ids = '|'::text OR pr.conta_id IS NOT NULL AND ec.filtro_conta_ids ~~ (('%|'::text || pr.conta_id::character varying::text) || '|%'::text)) AND (ec.filtro_centrocusto_ids = '|'::text OR pr.centrocusto_id IS NOT NULL AND ec.filtro_centrocusto_ids ~~ (('%|'::text || pr.centrocusto_id::character varying::text) || '|%'::text)) AND (ec.filtro_contract_ids = '|'::text OR pr.hr_contract_id IS NOT NULL AND ec.filtro_contract_ids ~~ (('%|'::text || pr.hr_contract_id::character varying::text) || '|%'::text)) AND (ec.filtro_contract_exclui_ids = '|'::text OR pr.hr_contract_id IS NULL OR ec.filtro_contract_exclui_ids !~~ (('%|'::text || pr.hr_contract_id::character varying::text) || '|%'::text))
  ORDER BY pr.id;

"""


SQL_CONFERENCIA_ECONOMICA_TABELA = """
DROP TABLE finan_rateio_economico_bi;

CREATE TABLE finan_rateio_economico_bi AS (
 SELECT
    row_number() over() as id,
    true AS controle,
    pr.lancamento_id,
    pr.tipo,
    pr.data_quitacao,
    pr.data_vencimento,
    pr.company_id,
    pr.conta_id,
    pr.centrocusto_id,
    pr.hr_contract_id,
    pr.porcentagem,
    CASE
        WHEN pr.tipo::text = 'P'::text OR pr.tipo::text = 'S'::text OR pr.tipo::text = 'PP'::text OR pr.tipo::text = 'LP'::text THEN pr.valor_documento * (-1)::numeric
        ELSE pr.valor_documento
    END AS valor_documento,
    CASE
        WHEN pr.tipo::text = 'P'::text OR pr.tipo::text = 'S'::text OR pr.tipo::text = 'PP'::text OR pr.tipo::text = 'LP'::text THEN pr.valor * (-1)::numeric
        ELSE pr.valor
    END AS valor,
    CASE
        WHEN pr.tipo::text = 'P'::text OR pr.tipo::text = 'S'::text OR pr.tipo::text = 'PP'::text OR pr.tipo::text = 'LP'::text THEN pr.valor_desconto
        ELSE pr.valor_desconto * (-1)::numeric
    END AS valor_desconto,
    CASE
        WHEN pr.tipo::text = 'P'::text OR pr.tipo::text = 'S'::text OR pr.tipo::text = 'PP'::text OR pr.tipo::text = 'LP'::text THEN pr.valor_juros * (-1)::numeric
        ELSE pr.valor_juros
    END AS valor_juros,
    CASE
        WHEN pr.tipo::text = 'P'::text OR pr.tipo::text = 'S'::text OR pr.tipo::text = 'PP'::text OR pr.tipo::text = 'LP'::text THEN pr.valor_multa * (-1)::numeric
        ELSE pr.valor_multa
    END AS valor_multa,
    pr.valor_original,
    pr.valor_documento_original,
    pr.saldo_original,
    c.parent_id AS grupo_id,
    ec.id AS econo_conta_id,
    pr.res_partner_bank_id as partner_bank_id

   FROM finan_pagamento_rateio_folha pr
     JOIN res_company c ON c.id = pr.company_id
     LEFT JOIN econo_conta ec ON ec.sintetica = false AND (ec.filtro_company_ids <> '|'::text OR ec.filtro_conta_ids <> '|'::text OR ec.filtro_centrocusto_ids <> '|'::text OR ec.filtro_contract_ids <> '|'::text OR ec.filtro_contract_exclui_ids <> '|'::text) AND (ec.filtro_company_ids = '|'::text OR pr.company_id IS NOT NULL AND ec.filtro_company_ids ~~ (('%|'::text || pr.company_id::character varying::text) || '|%'::text)) AND (ec.filtro_conta_ids = '|'::text OR pr.conta_id IS NOT NULL AND ec.filtro_conta_ids ~~ (('%|'::text || pr.conta_id::character varying::text) || '|%'::text)) AND (ec.filtro_centrocusto_ids = '|'::text OR pr.centrocusto_id IS NOT NULL AND ec.filtro_centrocusto_ids ~~ (('%|'::text || pr.centrocusto_id::character varying::text) || '|%'::text)) AND (ec.filtro_contract_ids = '|'::text OR pr.hr_contract_id IS NOT NULL AND ec.filtro_contract_ids ~~ (('%|'::text || pr.hr_contract_id::character varying::text) || '|%'::text)) AND (ec.filtro_contract_exclui_ids = '|'::text OR pr.hr_contract_id IS NULL OR ec.filtro_contract_exclui_ids !~~ (('%|'::text || pr.hr_contract_id::character varying::text) || '|%'::text))
  );

"""

"""
CREATE OR REPLACE VIEW finan_rateio_economico_bi AS
    select
        row_number() over() as id,
        true AS controle,
        pr.lancamento_id,
        pr.tipo,
        pr.data_quitacao,
        pr.data_vencimento,
        pr.company_id,
        pr.conta_id,
        pr.centrocusto_id,
        pr.hr_contract_id,
        pr.porcentagem,
        pr.valor_documento,
        case
            when pr.tipo in ('P', 'S', 'PP', 'LP') then pr.valor * -1
            else pr.valor
        end as valor,
        pr.valor_original,
        pr.valor_documento_original,
        pr.saldo_original,
        c.parent_id AS grupo_id,
        ec.id as econo_conta_id

    from
        finan_pagamento_rateio_folha pr
        join res_company c ON c.id = pr.company_id
        left join econo_conta ec on (
                ec.sintetica = False
            and (   ec.filtro_company_ids != '|'
                 or ec.filtro_conta_ids != '|'
                 or ec.filtro_centrocusto_ids != '|'
                 or ec.filtro_contract_ids != '|'
                 or ec.filtro_contract_exclui_ids != '|')
            and (ec.filtro_company_ids = '|' or (pr.company_id is not null and ec.filtro_company_ids like '%|' || cast(pr.company_id as varchar) || '|%'))
            and (ec.filtro_conta_ids = '|' or (pr.conta_id is not null and ec.filtro_conta_ids like '%|' || cast(pr.conta_id as varchar) || '|%'))
            and (ec.filtro_centrocusto_ids = '|' or (pr.centrocusto_id is not null and ec.filtro_centrocusto_ids like '%|' || cast(pr.centrocusto_id as varchar) || '|%'))
            and (ec.filtro_contract_ids = '|' or (pr.hr_contract_id is not null and ec.filtro_contract_ids like '%|' || cast(pr.hr_contract_id as varchar) || '|%'))
            and (ec.filtro_contract_exclui_ids = '|' or pr.hr_contract_id is null or ec.filtro_contract_exclui_ids not like '%|' || cast(pr.hr_contract_id as varchar) || '|%')
        );
"""