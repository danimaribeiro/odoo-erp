# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


SQL_VIEW_PAGAMENTO_RESUMO = """
    DROP VIEW IF EXISTS finan_pagamento_resumo;
    CREATE OR REPLACE VIEW finan_pagamento_resumo AS
      select
        max(f.id) as id,
        f.tipo,
        f.lancamento_id,
        max(f.data_quitacao) as data_quitacao,
        coalesce(sum(f.valor_multa), 0) as valor_multa,
        coalesce(sum(f.valor_juros), 0) as valor_juros,
        coalesce(sum(f.valor_desconto), 0) as valor_desconto,
        coalesce(sum(f.valor), 0) as valor,
        coalesce(sum(f.valor_documento), 0) as valor_documento,
        (select ff.res_partner_bank_id from finan_lancamento ff where ff.id = max(f.id)) as res_partner_bank_id,
        (select ff.formapagamento_id from finan_lancamento ff where ff.id = max(f.id)) as formapagamento_id
      from
        finan_lancamento f
      where
        f.tipo in ('PP', 'PR')
      group by
        f.lancamento_id, f.tipo;
    """

SQL_AJUSTA_QUITACAO = """
    update finan_lancamento f set
      valor_juros = coalesce((select r.valor_juros from finan_pagamento_resumo r where r.lancamento_id = f.id), 0),
      valor_multa = coalesce((select r.valor_multa from finan_pagamento_resumo r where r.lancamento_id = f.id), 0),
      valor_desconto = coalesce((select r.valor_desconto from finan_pagamento_resumo r where r.lancamento_id = f.id), 0),
      valor = coalesce((select r.valor from finan_pagamento_resumo r where r.lancamento_id = f.id), 0),
      res_partner_bank_id = (select r.res_partner_bank_id from finan_pagamento_resumo r where r.lancamento_id = f.id),
      valor_saldo = case when coalesce((select r.valor_documento from finan_pagamento_resumo r where r.lancamento_id = f.id), 0) >= f.valor_documento then 0
      else f.valor_documento - coalesce((select r.valor_documento from finan_pagamento_resumo r where r.lancamento_id = f.id), 0)
      end

    where
      f.tipo in ('R', 'P', 'LR', 'LP')
      and f.id = %d
      and f.lancamento_id is null
      and (
          coalesce(f.valor_juros, 0) <> coalesce((select r.valor_juros from finan_pagamento_resumo r where r.lancamento_id = f.id), 0)
       or coalesce(f.valor_multa, 0) <> coalesce((select r.valor_multa from finan_pagamento_resumo r where r.lancamento_id = f.id), 0)
       or coalesce(f.valor_desconto, 0) <> coalesce((select r.valor_desconto from finan_pagamento_resumo r where r.lancamento_id = f.id), 0)
       or coalesce(f.valor, 0) <> coalesce((select r.valor from finan_pagamento_resumo r where r.lancamento_id = f.id), 0)
       or f.res_partner_bank_id <> (select r.res_partner_bank_id from finan_pagamento_resumo r where r.lancamento_id = f.id)
       or coalesce(f.valor_saldo, 0) <> case when coalesce((select r.valor_documento from finan_pagamento_resumo r where r.lancamento_id = f.id), 0) >= f.valor_documento then 0
      else f.valor_documento - coalesce((select r.valor_documento from finan_pagamento_resumo r where r.lancamento_id = f.id), 0)
      end
      );

    update finan_lancamento f set
      valor_saldo = case
        when coalesce((select r.valor_documento from finan_pagamento_resumo r where r.lancamento_id = f.id), 0) >= f.valor_documento then 0
        else f.valor_documento - coalesce((select r.valor_documento from finan_pagamento_resumo r where r.lancamento_id = f.id), 0)
      end,
      data_ultimo_pagamento = (select max(r.data_quitacao) from finan_lancamento r where r.lancamento_id = f.id and r.tipo in ('PP', 'PR'))

    where
      f.tipo in ('R', 'P', 'LR', 'LP')
      and f.id = %d
      and f.lancamento_id is null
      and coalesce(f.valor_saldo, 0) <> case when coalesce((select r.valor_documento from finan_pagamento_resumo r where r.lancamento_id = f.id), 0) >= f.valor_documento then 0
      else f.valor_documento - coalesce((select r.valor_documento from finan_pagamento_resumo r where r.lancamento_id = f.id), 0)
      end
      ;

    update finan_lancamento f set
      data_quitacao = null
    where
      f.tipo in ('R', 'P')
      and f.id = %d
      and f.valor_saldo = f.valor_documento and f.lancamento_id is null;

    update finan_lancamento f set
      data_quitacao = (select r.data_quitacao from finan_pagamento_resumo r where r.lancamento_id = f.id)
    where
      f.tipo in ('R', 'P')
      and f.id = %d
      and f.valor_saldo <= 0 and f.lancamento_id is null;

    update finan_lancamento f set
      situacao = case
        when (f.tipo in ('T', 'LP', 'LR')) or (f.conciliado = True) then 'Conciliado'
        when (f.tipo in ('P', 'R')) and (f.data_baixa is not null) and (coalesce(f.valor, 0) = 0) then 'Baixado'
        when (f.tipo in ('P', 'R')) and (f.data_baixa is not null) and (coalesce(f.valor, 0) != 0) then 'Baixado parcial'
        when (f.tipo in ('P', 'R', 'PP', 'PR', 'E', 'S')) and (f.data_quitacao is not null) then 'Quitado'
        when (f.tipo in ('P', 'R')) and (f.data_vencimento is null) then 'Sem informação de vencimento'
        when (f.tipo in ('P', 'R')) and (f.data_vencimento::date = current_date::date) then 'Vence hoje'
        when (f.tipo in ('P', 'R')) and (f.data_vencimento::date < current_date::date) then 'Vencido'
        when (f.tipo in ('P', 'R')) and (f.data_vencimento::date > current_date::date) then 'A vencer'
        else
        'Não identificado'
      end
      where f.id = %d or f.lancamento_id = %d;

      update finan_lancamento f set
          data_quitacao = data
      where
          f.tipo in ('E', 'S', 'T') and f.data != f.data_quitacao and f.id = %d;

      update finan_lancamento f set
          conciliado = True
      where
          f.tipo in ('E', 'S', 'T') and (f.conciliado is null or f.conciliado = False) and f.id = %d;

      update finan_lancamento f set
          valor_documento = valor
      where
          f.tipo in ('E', 'S', 'T') and (f.valor_documento != f.valor) and f.id = %d;

      update finan_lancamento f set
          data = data_quitacao
      where
          f.tipo in ('PP', 'PR') and f.conciliado = True and f.data is null and (f.id = %d or f.lancamento_id = %d);

      update finan_lancamento f set
          conta_id = (select ff.conta_id from finan_lancamento ff where ff.id = f.lancamento_id)

      where
          f.tipo in ('PP', 'PR') and f.conta_id is null  and (f.id = %d or f.lancamento_id = %d);
    """


SQL_AJUSTA_QUITACAO_DEMORADO = """
    update finan_lancamento f set
      situacao = case
        when (f.tipo in ('T', 'LP', 'LR')) or (f.conciliado = True) then 'Conciliado'
        when (f.tipo in ('P', 'R')) and (f.data_baixa is not null) and (coalesce(f.valor, 0) = 0) then 'Baixado'
        when (f.tipo in ('P', 'R')) and (f.data_baixa is not null) and (coalesce(f.valor, 0) != 0) then 'Baixado parcial'
        when (f.tipo in ('P', 'R', 'PP', 'PR', 'E', 'S')) and (f.data_quitacao is not null) then 'Quitado'
        when (f.tipo in ('P', 'R')) and (f.data_vencimento is null) then 'Sem informação de vencimento'
        when (f.tipo in ('P', 'R')) and (f.data_vencimento::date = current_date::date) then 'Vence hoje'
        when (f.tipo in ('P', 'R')) and (f.data_vencimento::date < current_date::date) then 'Vencido'
        when (f.tipo in ('P', 'R')) and (f.data_vencimento::date > current_date::date) then 'A vencer'
        else
        'Não identificado'
      end;
    """

##SQL_AJUSTA_QUITACAO_DEMORADO = """
    ##update finan_lancamento f set
      ##valor_saldo = case
        ##when coalesce((select r.valor_documento from finan_pagamento_resumo r where r.lancamento_id = f.id), 0) >= f.valor_documento then 0
        ##else f.valor_documento - coalesce((select r.valor_documento from finan_pagamento_resumo r where r.lancamento_id = f.id), 0)
      ##end,
      ##data_ultimo_pagamento = (select max(r.data_quitacao) from finan_lancamento r where r.lancamento_id = f.id and r.tipo in ('PP', 'PR'))

    ##where
      ##f.tipo in ('R', 'P', 'LR', 'LP')
      ##and f.lancamento_id is null;
