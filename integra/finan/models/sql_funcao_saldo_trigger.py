
SQL_CRIA_TABELA_BANCO = '''
    DROP TABLE if exists finan_saldo_trigger_banco;

    CREATE TABLE finan_saldo_trigger_banco
    (
    id serial NOT NULL,
    create_uid integer,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    write_uid integer,
    res_partner_bank_id integer,
    data date,
    saldo_anterior numeric(18, 2),
    saldo numeric(18, 2),
    credito numeric(18, 2),
    debito numeric(18, 2),
    CONSTRAINT finan_saldo_trigger_banco_pkey PRIMARY KEY (id),
    CONSTRAINT finan_saldo_trigger_banco_create_uid_fkey FOREIGN KEY (create_uid)
        REFERENCES res_users (id) MATCH SIMPLE
        ON UPDATE NO ACTION ON DELETE SET NULL,
    CONSTRAINT finan_saldo_trigger_banco_res_partner_bank_id_fkey FOREIGN KEY (res_partner_bank_id)
        REFERENCES res_partner_bank (id) MATCH SIMPLE
        ON UPDATE NO ACTION ON DELETE SET NULL,
    CONSTRAINT finan_saldo_trigger_banco_write_uid_fkey FOREIGN KEY (write_uid)
        REFERENCES res_users (id) MATCH SIMPLE
        ON UPDATE NO ACTION ON DELETE SET NULL,
    CONSTRAINT finan_saldo_trigger_banco_res_partner_bank_id_data_unique UNIQUE (res_partner_bank_id, data)
    )
    WITH (
    OIDS=FALSE
    );

    CREATE INDEX finan_saldo_trigger_banco_data_index
    ON finan_saldo_trigger_banco
    USING btree
    (data);

    CREATE INDEX finan_saldo_trigger_banco_res_partner_bank_id_index
    ON finan_saldo_trigger_banco
    USING btree
    (res_partner_bank_id);


    CREATE INDEX finan_saldo_trigger_banco_res_partner_bank_id_data_index
    ON finan_saldo_trigger_banco
    USING btree
    (res_partner_bank_id, data);
'''

SQL_CRIA_TABELA_PARTNER = '''
    DROP TABLE if exists finan_saldo_trigger_partner;

    CREATE TABLE finan_saldo_trigger_partner
    (
    id serial NOT NULL,
    create_uid integer,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    write_uid integer,
    res_partner_id integer,
    data date,
    saldo_anterior numeric(18, 2),
    saldo numeric(18, 2),
    credito numeric(18, 2),
    debito numeric(18, 2),
    CONSTRAINT finan_saldo_trigger_partner_pkey PRIMARY KEY (id),
    CONSTRAINT finan_saldo_trigger_partner_create_uid_fkey FOREIGN KEY (create_uid)
        REFERENCES res_users (id) MATCH SIMPLE
        ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT finan_saldo_trigger_partner_partner_id_fkey FOREIGN KEY (res_partner_id)
        REFERENCES res_partner (id) MATCH SIMPLE
        ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT finan_saldo_trigger_partner_write_uid_fkey FOREIGN KEY (write_uid)
        REFERENCES res_users (id) MATCH SIMPLE
        ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT finan_saldo_trigger_partner_res_partner_id_data_unique UNIQUE (res_partner_id, data)
    )
    WITH (
    OIDS=FALSE
    );

    CREATE INDEX finan_saldo_trigger_partner_data_index
    ON finan_saldo_trigger_partner
    USING btree
    (data);

    CREATE INDEX finan_saldo_trigger_partner_res_partner_id_index
    ON finan_saldo_trigger_partner
    USING btree
    (res_partner_id);


    CREATE INDEX finan_saldo_trigger_partner_res_partner_id_data_index
    ON finan_saldo_trigger_partner
    USING btree
    (res_partner_id, data);
'''

SQL_CRIA_FUNCAO_ATUALIZA_SALDOS = '''
drop function if exists atualiza_saldos();
drop function if exists atualiza_saldo_banco(v_bank_id integer, v_data date, v_credito numeric(18, 2), v_debito numeric(18, 2));
drop function if exists atualiza_saldo_partner(v_partner_id integer, v_data date, v_credito numeric(18, 2), v_debito numeric(18, 2));

create function atualiza_saldo_banco(v_bank_id integer, v_data date, v_credito numeric(18, 2), v_debito numeric(18, 2)) as $$
declare
    saldo_anterior numeric(18, 2);
    saldo numeric(18, 2);
begin

    if exists(select s.id from finan_saldo_trigger_banco s where s.res_partner_bank_id = v_bank_id and s.data = v_data) then
        begin
            update finan_saldo_trigger_banco s set
                credito = s.credito + v_credito,
                debito = s.debito + v_debito,
                saldo = s.saldo + v_credito - v_debito
            where s.res_partner_bank_id = v_bank_id and s.data = v_data;

            update finan_saldo_trigger_banco s set
                saldo_anterior = s.saldo_anterior + v_credito - v_debito,
                saldo = s.saldo + v_credito - v_debito
            where s.res_partner_bank_id = v_bank_id and s.data > v_data;
        end;
    else
        begin
            saldo_anterior = coalesce((select s.saldo from finan_saldo_trigger_banco s where s.res_partner_bank_id = v_bank_id and s.data < v_data order by s.data desc limit 1), 0);
            saldo = saldo_anterior + v_credito - v_debito;
            insert into finan_saldo_trigger_banco(res_partner_bank_id, data, saldo_anterior, credito, debito, saldo) values (v_bank_id, v_data, saldo_anterior, v_credito, v_debito, saldo);

            update finan_saldo_trigger_banco s set
                saldo_anterior = s.saldo_anterior + creditos - debitos,
                saldo = s.saldo + creditos - debitos
            where s.res_partner_bank_id = bank_id and s.data > v_data;
        end;
    end if;

end;
$$ LANGUAGE plpgsql;

CREATE FUNCTION atualiza_saldos() RETURNS boolean AS $$
declare
    bank_id integer;
    v_partner_id integer;
    saldo_anterior numeric(18, 2);
    creditos numeric(18, 2);
    debitos numeric(18, 2);
    saldo numeric(18, 2);
    v_data date;
    data_minima date;
    data_maxima date;
begin

    delete from finan_saldo_trigger_banco;

    for bank_id, v_partner_id, v_data, creditos, debitos in select res_partner_bank_id, partner_id, data_quitacao, valor_compensado_credito, valor_compensado_debito from finan_extrato loop
        if bank_id is not null then
            execute atualiza_saldo_banco(bank_id, v_data, creditos, debitos);
        end if;

        if v_partner_id is not null then
            if exists(select s.id from finan_saldo_trigger_partner s where s.res_partner_id = v_partner_id and s.data = v_data) then
                begin
                    update finan_saldo_trigger_partner s set
                        credito = s.credito + creditos,
                        debito = s.debito + debitos,
                        saldo = s.saldo + creditos - debitos
                    where s.res_partner_id = v_partner_id and s.data = v_data;

                    update finan_saldo_trigger_partner s set
                        saldo_anterior = s.saldo_anterior + creditos - debitos,
                        saldo = s.saldo + creditos - debitos
                    where s.res_partner_id = v_partner_id and s.data > v_data;
                end;
            else
                begin
                    saldo_anterior = coalesce((select s.saldo from finan_saldo_trigger_partner s where s.res_partner_id = bank_id and s.data < v_data order by s.data desc limit 1), 0);
                    saldo = saldo_anterior + creditos - debitos;
                    insert into finan_saldo_trigger_partner(res_partner_id, data, saldo_anterior, credito, debito, saldo) values (v_partner_id, v_data, saldo_anterior, creditos, debitos, saldo);

                    update finan_saldo_trigger_partner s set
                        saldo_anterior = s.saldo_anterior + creditos - debitos,
                        saldo = s.saldo + creditos - debitos
                    where s.res_partner_id = v_partner_id and s.data > v_data;
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

        for v_partner_id in (select e.partner_id from finan_lancamento e group by e.partner_id order by e.partner_id) loop
            if not exists(select s.id from finan_saldo_trigger_partner s where s.res_partner_id = v_partner_id and s.data = v_data) then
                begin
                    saldo_anterior = coalesce((select s.saldo from finan_saldo_trigger_partner s where s.res_partner_id = v_partner_id and s.data < v_data order by s.data desc limit 1), 0);
                    insert into finan_saldo_trigger_partner(res_partner_id, data, saldo_anterior, credito, debito, saldo) values (v_partner_id, v_data, saldo_anterior, 0, 0, saldo_anterior);
                end;
            end if;
        end loop;
    end loop;

  return true;
end;
$$ LANGUAGE plpgsql;
'''