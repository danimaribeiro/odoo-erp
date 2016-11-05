# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


SQL_VIEW_GERAL = """
    DROP VIEW IF EXISTS finan_saldo_bancario_hoje;
    DROP VIEW IF EXISTS finan_saldo_resumo_data_quitacao_empresa;
    DROP VIEW IF EXISTS finan_saldo_resumo_data_quitacao;
    DROP VIEW IF EXISTS finan_saldo_resumo;
    DROP VIEW IF EXISTS finan_saldo_quitacao_empresa_banco;
    DROP VIEW IF EXISTS finan_saldo_quitacao;
    DROP VIEW IF EXISTS finan_extrato;
    DROP VIEW IF EXISTS finan_saida;
    DROP VIEW IF EXISTS finan_entrada;
    DROP VIEW IF EXISTS finan_saldo_resumo_formapagamento;

    CREATE OR REPLACE VIEW finan_entrada AS
        SELECT
            'I' AS tipo,
            (b.id * -1) AS id,
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
            NULL::integer AS conta_id,
            b.id AS res_partner_bank_id,
            True as conciliado,
            null::integer as lancamento_id,
            b.company_id as company_id
        FROM res_partner_bank b
        UNION
        SELECT
            'E' AS tipo,
            e.id,
            e.data_documento,
            e.numero_documento,
            e.data_quitacao as data_vencimento,
            e.data_quitacao as data_quitacao,
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
            e.id as lancamento_id,
            e.company_id
        FROM finan_lancamento e
        WHERE e.tipo = 'E'
        UNION
        SELECT
            'T' AS tipo,
            te.id,
            te.data_documento,
            te.numero_documento,
            te.data as data_vencimento,
            te.data as data_quitacao,
            te.data AS data_compensacao,
            te.valor as valor_documento,
            te.valor AS valor_compensado,
            coalesce(te.valor_multa, 0) as valor_multa,
            coalesce(te.valor_juros, 0) as valor_juros,
            coalesce(te.valor_desconto, 0) as valor_desconto,
            te.partner_id,
            te.conta_id,
            te.res_partner_bank_creditar_id AS res_partner_bank_id,
            te.conciliado,
            te.id as lancamento_id,
            te.company_id
        FROM finan_lancamento te
        WHERE te.tipo = 'T'
        UNION
        SELECT
            'R' AS tipo,
            pr.id,
            r.data_documento,
            r.numero_documento,
            r.data_vencimento,
            pr.data_quitacao,
            pr.data AS data_compensacao,
            pr.valor_documento,
            pr.valor AS valor_compensado,
            pr.valor_multa,
            pr.valor_juros,
            pr.valor_desconto,
            r.partner_id,
            r.conta_id,
            pr.res_partner_bank_id,
            pr.conciliado,
            pr.lancamento_id as lancamento_id,
            r.company_id
            FROM finan_lancamento pr
        JOIN finan_lancamento r ON r.id = pr.lancamento_id
        WHERE pr.tipo = 'PR';

    CREATE OR REPLACE VIEW finan_saida AS
        SELECT
            'S' AS tipo,
            e.id,
            e.data_documento,
            e.numero_documento,
            e.data_quitacao as data_vencimento,
            e.data_quitacao as data_quitacao,
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
            e.id as lancamento_id,
            e.company_id
        FROM finan_lancamento e
        WHERE e.tipo = 'S'
        UNION
        SELECT
            'T' AS tipo,
            te.id * -1 as id,
            te.data_documento,
            te.numero_documento,
            te.data as data_vencimento,
            te.data as data_quitacao,
            te.data AS data_compensacao,
            te.valor as valor_documento,
            te.valor AS valor_compensado,
            coalesce(te.valor_multa, 0) as valor_multa,
            coalesce(te.valor_juros, 0) as valor_juros,
            coalesce(te.valor_desconto, 0) as valor_desconto,
            te.partner_id,
            te.conta_id,
            te.res_partner_bank_id,
            te.conciliado,
            te.id as lancamento_id,
            te.company_id
        FROM finan_lancamento te
        WHERE te.tipo = 'T'
        UNION
        SELECT
            'P' AS tipo,
            pr.id,
            r.data_documento,
            r.numero_documento,
            r.data_vencimento,
            pr.data_quitacao,
            pr.data AS data_compensacao,
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
        WHERE pr.tipo = 'PP';

    CREATE OR REPLACE VIEW finan_extrato AS
        SELECT
            e.tipo,
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
        SELECT
            s.tipo,
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

    CREATE OR REPLACE VIEW finan_saldo_quitacao AS
        SELECT
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
        FROM
            finan_extrato e
        GROUP BY
            e.res_partner_bank_id,
            e.data_quitacao;

    CREATE OR REPLACE VIEW finan_saldo_quitacao_empresa_banco AS
        SELECT
            e.company_id,
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
        FROM
            finan_extrato e
        GROUP BY
            e.company_id,
            e.res_partner_bank_id,
            e.data_quitacao;

    CREATE OR REPLACE VIEW finan_saldo_resumo AS
      SELECT
      (cast(e.res_partner_bank_id as varchar) || to_char(e.data_compensacao, 'YYYYmmdd')) as id,
      e.res_partner_bank_id,
      e.data_compensacao,

      coalesce((select sum(ee.valor_compensado_credito - ee.valor_compensado_debito) from finan_extrato ee where ee.data_compensacao is not null and
      ee.res_partner_bank_id = e.res_partner_bank_id and ee.data_compensacao < e.data_compensacao and ee.conciliado = True), 0) as saldo_anterior,

      sum(e.valor_compensado_credito) as credito,
      sum(e.valor_compensado_debito) as debito,

      coalesce((select sum(ee.valor_compensado_credito - ee.valor_compensado_debito) from finan_extrato ee where ee.data_compensacao is not null and
      ee.res_partner_bank_id = e.res_partner_bank_id and ee.data_compensacao <= e.data_compensacao  and ee.conciliado = True), 0) as saldo

    FROM finan_extrato e
    JOIN res_partner_bank b ON b.id = e.res_partner_bank_id

    WHERE e.data_compensacao is not null and e.conciliado = True

    GROUP BY
      e.res_partner_bank_id,
      e.data_compensacao

    ORDER BY e.res_partner_bank_id, e.data_compensacao ;

    CREATE OR REPLACE VIEW finan_saldo_resumo_data_quitacao AS
    SELECT
      (cast(e.res_partner_bank_id as varchar) || to_char(e.data_quitacao, 'YYYYmmdd')) as id,
      e.res_partner_bank_id,
      e.data_quitacao,

      coalesce((select sum(ee.valor_compensado_credito - ee.valor_compensado_debito) from finan_extrato ee where
      ee.res_partner_bank_id = e.res_partner_bank_id and ee.data_quitacao < e.data_quitacao), 0) as saldo_anterior,

      sum(e.valor_compensado_credito) as credito,
      sum(e.valor_compensado_debito) as debito,

      coalesce((select sum(ee.valor_compensado_credito - ee.valor_compensado_debito) from finan_extrato ee where
      ee.res_partner_bank_id = e.res_partner_bank_id and ee.data_quitacao <= e.data_quitacao), 0) as saldo

    FROM finan_extrato e

    WHERE e.data_quitacao is not null

    GROUP BY
      e.res_partner_bank_id,
      e.data_quitacao

    ORDER BY
      e.res_partner_bank_id,
      e.data_quitacao;

    CREATE OR REPLACE VIEW finan_saldo_resumo_data_quitacao_empresa AS
    SELECT
      (cast(e.company_id as varchar) || cast(e.res_partner_bank_id as varchar) || to_char(e.data_quitacao, 'YYYYmmdd')) as id,
      e.company_id,
      e.res_partner_bank_id,
      e.data_quitacao,

      coalesce((select sum(ee.valor_compensado_credito - ee.valor_compensado_debito) from finan_extrato ee where
      ee.company_id = e.company_id and ee.res_partner_bank_id = e.res_partner_bank_id and ee.data_quitacao < e.data_quitacao), 0) as saldo_anterior,

      sum(e.valor_compensado_credito) as credito,
      sum(e.valor_compensado_debito) as debito,

      coalesce((select sum(ee.valor_compensado_credito - ee.valor_compensado_debito) from finan_extrato ee where
      ee.company_id = e.company_id and ee.res_partner_bank_id = e.res_partner_bank_id and ee.data_quitacao <= e.data_quitacao), 0) as saldo

    FROM finan_extrato e
    WHERE e.data_quitacao is not null

    GROUP BY
      e.company_id,
      e.res_partner_bank_id,
      e.data_quitacao

    ORDER BY
      e.company_id,
      e.res_partner_bank_id,
      e.data_quitacao;

    CREATE OR REPLACE VIEW finan_saldo_bancario_hoje as

     select
     b.id as id,
     b.company_id as company_id,
     b.id as res_partner_bank_id,
     b.state as tipo,
     coalesce((select ee.saldo from finan_saldo_resumo_data_quitacao ee where ee.data_quitacao < current_date and ee.res_partner_bank_id = b.id order by ee.data_quitacao desc limit 1), 0) as saldo_anterior,
     coalesce((select sum(e.credito) from finan_saldo_resumo_data_quitacao e where e.res_partner_bank_id = b.id and e.data_quitacao::date = current_date), 0) as credito,
     coalesce((select sum(e.debito) from finan_saldo_resumo_data_quitacao e where e.res_partner_bank_id = b.id and e.data_quitacao::date = current_date), 0) as debito,
     coalesce(

     coalesce((select ee.saldo from finan_saldo_resumo_data_quitacao ee where ee.data_quitacao < current_date and ee.res_partner_bank_id = b.id order by ee.data_quitacao desc limit 1), 0)
     +
     coalesce((select sum(e.credito) from finan_saldo_resumo_data_quitacao e where e.res_partner_bank_id = b.id and e.data_quitacao::date = current_date), 0)
     -
     coalesce((select sum(e.debito) from finan_saldo_resumo_data_quitacao e where e.res_partner_bank_id = b.id and e.data_quitacao::date = current_date), 0)

     , 0) as saldo
     from res_partner_bank b

     order by
     b.bank_name;

     CREATE OR REPLACE VIEW finan_saldo_resumo_formapagamento as

        select
            cast(to_char(l.data_quitacao, 'yyyymmdd') as bigint) * 1000000 + l.res_partner_bank_id * 1000 + l.formapagamento_id as id,
            l.res_partner_bank_id,
            l.data_quitacao,
            l.formapagamento_id,
            sum(l.valor) as valor


        from
            finan_lancamento l

        where
            l.tipo = 'PR'


        group by
            l.res_partner_bank_id,
            l.data_quitacao,
            l.formapagamento_id
    ;
    """
