
drop view if exists finan_fluxo_caixa_sintetico;

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
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '01'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_01,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '02'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_02,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '03'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_03,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '04'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_04,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '05'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_05,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '06'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_06,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '07'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_07,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '08'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_08,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '09'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_09,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '10'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_10,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '11'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
            ELSE 0.00
        END, 0.00) AS quitado_11,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '12'::text THEN COALESCE(f.valor_entrada, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric) - COALESCE(f.valor_saida, 0::numeric) * COALESCE(ldp.porcentagem, 1::numeric)
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
     LEFT JOIN finan_lancamento_lote_divida_pagamento ldp ON ldp.lote_id = f.lancamento_id
     JOIN finan_lancamento fl ON ldp.divida_id IS NOT NULL AND fl.id = ldp.divida_id OR ldp.divida_id IS NULL AND fl.id = f.lancamento_id
     JOIN finan_conta fc ON fc.id = fl.conta_id
     JOIN finan_conta_arvore ca ON ca.conta_id = fl.conta_id
     JOIN finan_conta c ON c.id = ca.conta_pai_id
  WHERE f.tipo = 'Q'::text
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
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '01'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_01,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '02'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_02,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '03'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_03,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '04'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_04,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '05'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_05,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '06'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_06,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '07'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_07,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '08'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_08,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '09'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_09,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '10'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_10,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '11'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_11,
    COALESCE(
        CASE
            WHEN to_char(f.data::timestamp with time zone, 'MM'::text) = '12'::text THEN COALESCE(f.valor_entrada, 0::numeric) - COALESCE(f.valor_saida, 0::numeric)
            ELSE 0.00
        END, 0.00) AS vencido_12
   FROM finan_fluxo_mensal_diario f
     JOIN finan_lancamento l ON l.id = f.lancamento_id
     JOIN finan_conta fc ON fc.id = l.conta_id
     JOIN finan_conta_arvore ca ON ca.conta_id = l.conta_id
     JOIN finan_conta c ON c.id = ca.conta_pai_id
  WHERE f.tipo = 'V'::text;
