drop function if exists atualiza_saldos();

CREATE FUNCTION atualiza_saldos() RETURNS boolean AS $$
declare
    bank_id integer;
    partner_id integer;
    saldo_anterior numeric(18, 2);
    creditos numeric(18, 2);
    debitos numeric(18, 2);
    saldo numeric(18, 2);
    v_data date;
    data_minima date;
    data_maxima date;
begin

    delete from finan_saldo_trigger_banco;

    for bank_id, partner_id, v_data, creditos, debitos in select res_partner_bank_id, partner_id, data_quitacao, valor_compensado_credito, valor_compensado_debito from finan_extrato loop
        if bank_id is not null then
            if exists(select s.id from finan_saldo_trigger_banco s where s.res_partner_bank_id = bank_id and s.data = v_data) then
                begin
                    update finan_saldo_trigger_banco s set
                        credito = s.credito + creditos,
                        debito = s.debito + debitos,
                        saldo = s.saldo + creditos - debitos
                    where s.res_partner_bank_id = bank_id and s.data = v_data;

                    update finan_saldo_trigger_banco s set
                        saldo_anterior = s.saldo_anterior + creditos - debitos,
                        saldo = s.saldo + creditos - debitos
                    where s.res_partner_bank_id = bank_id and s.data > v_data;
                end;
            else
                begin
                    saldo_anterior = coalesce((select s.saldo from finan_saldo_trigger_banco s where s.res_partner_bank_id = bank_id and s.data < v_data order by s.data desc limit 1), 0);
                    saldo = saldo_anterior + creditos - debitos;
                    insert into finan_saldo_trigger_banco(res_partner_bank_id, data, saldo_anterior, credito, debito, saldo) values (bank_id, v_data, saldo_anterior, creditos, debitos, saldo);

                    update finan_saldo_trigger_banco s set
                        saldo_anterior = s.saldo_anterior + creditos - debitos,
                        saldo = s.saldo + creditos - debitos
                    where s.res_partner_bank_id = bank_id and s.data > v_data;
                end;
            end if;
        end if;

        if partner_id is not null then
            if exists(select s.id from finan_saldo_trigger_partner s where s.res_partner_id = partner_id and s.data = v_data) then
                begin
                    update finan_saldo_trigger_partner s set
                        credito = s.credito + creditos,
                        debito = s.debito + debitos,
                        saldo = s.saldo + creditos - debitos
                    where s.res_partner_id = partner_id and s.data = v_data;

                    update finan_saldo_trigger_partner s set
                        saldo_anterior = s.saldo_anterior + creditos - debitos,
                        saldo = s.saldo + creditos - debitos
                    where s.res_partner_id = partner_id and s.data > v_data;
                end;
            else
                begin
                    saldo_anterior = coalesce((select s.saldo from finan_saldo_trigger_partner s where s.res_partner_id = bank_id and s.data < v_data order by s.data desc limit 1), 0);
                    saldo = saldo_anterior + creditos - debitos;
                    insert into finan_saldo_trigger_partner(res_partner_id, data, saldo_anterior, credito, debito, saldo) values (partner_id, v_data, saldo_anterior, creditos, debitos, saldo);

                    update finan_saldo_trigger_partner s set
                        saldo_anterior = s.saldo_anterior + creditos - debitos,
                        saldo = s.saldo + creditos - debitos
                    where s.res_partner_id = partner_id and s.data > v_data;
                end;
            end if;
        end if;
    end loop;

    data_maxima = (select max(s.data) from finan_saldo_trigger_banco s);
    data_minima = (select min(s.data) from finan_saldo_trigger_banco s);

    for i in 0..(data_maxima - data_minima) loop
      v_data = data_minima + i;

        for bank_id in (select b.id from res_partner_bank b order by b.id) loop
            if not exists(select s.id from finan_saldo_trigger_banco s where s.res_partner_bank_id = bank_id and s.data = v_data) then
                begin
                    saldo_anterior = coalesce((select s.saldo from finan_saldo_trigger_banco s where s.res_partner_bank_id = bank_id and s.data < v_data order by s.data desc limit 1), 0);
                    insert into finan_saldo_trigger_banco(res_partner_bank_id, data, saldo_anterior, credito, debito, saldo) values (bank_id, v_data, saldo_anterior, 0, 0, saldo_anterior);
                end;
            end if;
        end loop;

        for partner_id in (select e.partner_id from finan_lancamento e group by e.partner_id order by e.partner_id) loop
            if not exists(select s.id from finan_saldo_trigger_partner s where s.res_partner_id = partner_id and s.data = v_data) then
                begin
                    saldo_anterior = coalesce((select s.saldo from finan_saldo_trigger_partner s where s.res_partner_id = partner_id and s.data < v_data order by s.data desc limit 1), 0);
                    insert into finan_saldo_trigger_partner(res_partner_id, data, saldo_anterior, credito, debito, saldo) values (partner_id, v_data, saldo_anterior, 0, 0, saldo_anterior);
                end;
            end if;
        end loop;
    end loop;

  return true;
end;
$$ LANGUAGE plpgsql;
