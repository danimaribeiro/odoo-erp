DROP VIEW finan_pagamento_rateio;
DROP VIEW finan_pagamento_rateio_folha;
DROP VIEW finan_lancamento_rateio_geral_folha;

CREATE OR REPLACE VIEW finan_lancamento_rateio_geral_folha AS 
 SELECT l.id * (-1) AS id,
    l.id AS lancamento_id,
    l.company_id,
    l.conta_id,
    l.centrocusto_id,
    NULL::integer AS hr_contract_id,
    100.00 AS porcentagem,
    NULL::integer AS project_id,
    l.contrato_id AS contrato_id,
    NULL::integer AS hr_department_id,
    NULL::integer AS veiculo_id
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
    sum(COALESCE(r.porcentagem, 0::numeric)) AS porcentagem,
    r.project_id,
    r.contrato_id,
    r.hr_department_id,
    r.veiculo_id
   FROM finan_lancamento_rateio r
  GROUP BY r.id, r.lancamento_id, r.company_id, r.conta_id, r.centrocusto_id, r.hr_contract_id, r.project_id, r.contrato_id, r.hr_department_id, r.veiculo_id
  ORDER BY 1, 2, 3, 4, 5, 6;



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
    rateio.contrato_id,
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
    divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original
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
    rateio.contrato_id,
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
    divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original
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
    rateio.contrato_id,
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
    divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original
   FROM finan_lancamento_rateio_geral_folha rateio
     JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['E'::character varying::text, 'S'::character varying::text]));



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
    divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original
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
    divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original
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
    divida.valor_saldo * rateio.porcentagem / 100.00 AS saldo_original
   FROM finan_lancamento_rateio_geral_folha rateio
     JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['E'::character varying::text, 'S'::character varying::text]));

