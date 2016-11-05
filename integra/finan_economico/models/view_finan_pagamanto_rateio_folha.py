sql = """
DROP VIEW finan_pagamento_rateio_folha;

CREATE OR REPLACE VIEW finan_pagamento_rateio_folha AS
 SELECT rateio.id,
    divida.id AS lancamento_id,
    divida.tipo,
    pagamento.data_quitacao,
    pagamento.data,
    case
      when pagamento.data is not null then pagamento.data
      else pagamento.data_quitacao
    end as data_compensacao,
    divida.data_vencimento,
    rateio.company_id,
    rateio.conta_id,
    rateio.centrocusto_id,
    rateio.hr_contract_id,
    rateio.porcentagem,
        CASE
            WHEN pagamento.valor_documento = 0::numeric THEN 0::numeric
            ELSE (pagamento.valor_documento * rateio.porcentagem / 100.00)::numeric(18,2)
        END AS valor_documento,
        CASE
            WHEN pagamento.valor_documento = 0::numeric THEN 0::numeric
            ELSE (pagamento.valor * rateio.porcentagem / 100.00)::numeric(18,2)
        END AS valor,
    (divida.valor * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_original,
    (divida.valor_documento * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_documento_original,
    (divida.valor_saldo * rateio.porcentagem / 100.00)::numeric(18,2) AS saldo_original
   FROM finan_lancamento_rateio_geral_folha rateio
     JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['P'::character varying::text, 'R'::character varying::text]))
     JOIN finan_lancamento pagamento ON pagamento.lancamento_id = divida.id AND (pagamento.tipo::text = ANY (ARRAY['PR'::character varying::text, 'PP'::character varying::text]))
UNION ALL
 SELECT rateio.id,
    divida.id AS lancamento_id,
    divida.tipo,
    pagamento.data_quitacao,
    pagamento.data,
    case
      when pagamento.data is not null then pagamento.data
      else pagamento.data_quitacao
    end as data_compensacao,
    divida.data_vencimento,
    rateio.company_id,
    rateio.conta_id,
    rateio.centrocusto_id,
    rateio.hr_contract_id,
    rateio.porcentagem,
        CASE
            WHEN pagamento.valor_documento = 0::numeric THEN 0::numeric
            ELSE (pagamento.valor_documento * (divida.valor_documento / pagamento.valor_documento) * rateio.porcentagem / 100.00)::numeric(18,2)
        END AS valor_documento,
        CASE
            WHEN pagamento.valor_documento = 0::numeric THEN 0::numeric
            ELSE (pagamento.valor * (divida.valor / pagamento.valor) * rateio.porcentagem / 100.00)::numeric(18,2)
        END AS valor,
    (divida.valor_documento * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_original,
    (divida.valor * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_documento_original,
    (divida.valor_saldo * rateio.porcentagem / 100.00)::numeric(18,2) AS saldo_original
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
    case
      when divida.data is not null then divida.data
      else divida.data_quitacao
    end as data_compensacao,
    divida.data_vencimento,
    rateio.company_id,
    rateio.conta_id,
    rateio.centrocusto_id,
    rateio.hr_contract_id,
    rateio.porcentagem,
    (divida.valor_documento * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_documento,
    (divida.valor * rateio.porcentagem / 100.00)::numeric(18,2) AS valor,
    (divida.valor * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_original,
    (divida.valor_documento * rateio.porcentagem / 100.00)::numeric(18,2) AS valor_documento_original,
    (divida.valor_saldo * rateio.porcentagem / 100.00)::numeric(18,2) AS saldo_original
   FROM finan_lancamento_rateio_geral_folha rateio
     JOIN finan_lancamento divida ON divida.id = rateio.lancamento_id AND (divida.tipo::text = ANY (ARRAY['P'::character varying::text, 'R'::character varying::text, 'E'::character varying::text, 'S'::character varying::text])) AND NOT (EXISTS ( SELECT pagamento.id
           FROM finan_lancamento pagamento
          WHERE pagamento.lancamento_id = divida.id)) AND NOT (EXISTS ( SELECT lote.id
           FROM finan_lancamento lote
          WHERE lote.id = divida.lancamento_id));

"""