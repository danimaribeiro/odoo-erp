
-- View: finan_pagamento_resumo

DROP VIEW IF EXISTS finan_pagamento_resumo;

CREATE OR REPLACE VIEW finan_pagamento_resumo AS
 SELECT max(f.id) AS id,
    f.tipo,
    f.lancamento_id,
    max(f.data_quitacao) AS data_quitacao,
    COALESCE(sum(f.valor_multa), 0::numeric) AS valor_multa,
    COALESCE(sum(f.valor_juros), 0::numeric) AS valor_juros,
    COALESCE(sum(f.valor_desconto), 0::numeric) AS valor_desconto,
    COALESCE(sum(f.valor), 0::numeric) AS valor,
    COALESCE(sum(f.valor_documento), 0::numeric) AS valor_documento,
    ( SELECT ff.res_partner_bank_id
           FROM finan_lancamento ff
          WHERE ff.id = max(f.id)) AS res_partner_bank_id,
    ( SELECT ff.formapagamento_id
           FROM finan_lancamento ff
          WHERE ff.id = max(f.id)) AS formapagamento_id
   FROM finan_lancamento f
  WHERE f.tipo::text = ANY (ARRAY['PP'::character varying::text, 'PR'::character varying::text])
  GROUP BY f.lancamento_id, f.tipo;


DROP VIEW IF EXISTS finan_fluxo_mensal_diario;

CREATE OR REPLACE VIEW finan_fluxo_mensal_diario AS
        (         SELECT e.id,
                    to_char(e.data_quitacao::timestamp with time zone, 'yyyy/mm'::text) AS mes,
                    e.data_quitacao AS data,
                    e.valor_compensado AS valor_entrada,
                    0 AS valor_saida,
                    COALESCE(l.provisionado, false) AS provisionado,
                    e.company_id,
                    'Q'::text AS tipo
                   FROM finan_entrada e
              LEFT JOIN finan_lancamento l ON l.id = e.lancamento_id
             WHERE e.data_quitacao IS NOT NULL
        UNION ALL
                 SELECT s.id,
                    to_char(s.data_quitacao::timestamp with time zone, 'yyyy/mm'::text) AS mes,
                    s.data_quitacao AS data,
                    0 AS valor_entrada,
                    s.valor_compensado AS valor_saida,
                    COALESCE(l.provisionado, false) AS provisionado,
                    s.company_id,
                    'Q'::text AS tipo
                   FROM finan_saida s
              LEFT JOIN finan_lancamento l ON l.id = s.lancamento_id
             WHERE s.data_quitacao IS NOT NULL)
UNION ALL
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
            'V'::text AS tipo
           FROM finan_lancamento l
          WHERE (l.tipo::text = ANY (ARRAY['R'::character varying::text, 'P'::character varying::text])) AND l.provisionado = false AND (l.situacao::text = ANY (ARRAY['Vencido'::character varying::text, 'A vencer'::character varying::text, 'Vence hoje'::character varying::text]));


-- View: finan_pagamento_rateio

DROP VIEW IF EXISTS finan_pagamento_rateio;

CREATE OR REPLACE VIEW finan_pagamento_rateio AS
 SELECT divida.id AS lancamento_id,
    divida.tipo,
    pagamento.data_quitacao,
    divida.data_vencimento,
    rateio.company_id,
    rateio.conta_id,
    rateio.centrocusto_id,
    rateio.porcentagem,
    (pagamento.valor_documento * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_documento,
    (pagamento.valor * rateio.porcentagem / 100.00)::numeric(18,2) AS valor,
    (divida.valor * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_original,
    (divida.valor_documento * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_documento_original,
    (divida.valor_saldo * rateio.porcentagem / 100.00)::numeric(18,2) AS saldo_original
   FROM finan_lancamento_rateio_geral rateio
     JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['P'::character varying::text, 'R'::character varying::text]))
     JOIN finan_lancamento pagamento ON pagamento.lancamento_id = divida.id AND (pagamento.tipo::text = ANY (ARRAY['PR'::character varying::text, 'PP'::character varying::text]))
UNION ALL
 SELECT divida.id AS lancamento_id,
    divida.tipo,
    pagamento.data_quitacao,
    divida.data_vencimento,
    rateio.company_id,
    rateio.conta_id,
    rateio.centrocusto_id,
    rateio.porcentagem,
    (pagamento.valor_documento * (divida.valor_documento / pagamento.valor_documento) * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_documento,
    (pagamento.valor * (divida.valor / pagamento.valor) * rateio.porcentagem / 100.00)::numeric(18,2) AS valor,
    (divida.valor_documento * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_original,
    (divida.valor * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_documento_original,
    (divida.valor_saldo * rateio.porcentagem / 100.00)::numeric(18,2) AS saldo_original
   FROM finan_lancamento_rateio_geral rateio
     JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['P'::character varying::text, 'R'::character varying::text]))
     JOIN finan_lancamento lote ON lote.id = divida.lancamento_id AND (lote.tipo::text = ANY (ARRAY['LP'::character varying::text, 'LR'::character varying::text]))
     JOIN finan_lancamento pagamento ON pagamento.lancamento_id = lote.id AND (pagamento.tipo::text = ANY (ARRAY['PP'::character varying::text, 'PR'::character varying::text]))
UNION ALL
 SELECT divida.id AS lancamento_id,
    divida.tipo,
    divida.data_quitacao,
    divida.data_vencimento,
    rateio.company_id,
    rateio.conta_id,
    rateio.centrocusto_id,
    rateio.porcentagem,
    (divida.valor_documento * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_documento,
    (divida.valor * rateio.porcentagem / 100.00)::numeric(18,2) AS valor,
    (divida.valor * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_original,
    (divida.valor_documento * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_documento_original,
    (divida.valor_saldo * rateio.porcentagem / 100.00)::numeric(18,2) AS saldo_original
   FROM finan_lancamento_rateio_geral rateio
     JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['P'::character varying::text, 'R'::character varying::text, 'E'::character varying::text, 'S'::character varying::text])) AND NOT (EXISTS ( SELECT pagamento.id
           FROM finan_lancamento pagamento
          WHERE pagamento.lancamento_id = divida.id));

DROP VIEW IF exists finan_lancamento_rateio_geral;

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
