   
sql_razao_antigo = """
        select
            coalesce((select r.razao_social from res_partner r where r.cnpj_cpf = rp.cnpj_cpf limit 1),'') as empresa,
            rp.cnpj_cpf,
            lc.data as data_lancamento,
            lc.codigo as codigo_lancamento,
            fc.id as conta_id,
            fc.data as data_criacao,
            coalesce(fc.nome, '') as conta_contabil,
            coalesce(fc.codigo_completo,'') as codigo_completo,
            coalesce(fc.codigo, 0) as conta_reduzida,
            'Conta Contábil: [' || coalesce(fc.codigo, 0) || '] ' || coalesce(fc.codigo_completo,'') || ' ' || coalesce(fc.nome, '') as conta_nome,
            coalesce(pt.vr_debito, 0) as vr_debito,
            coalesce(pt.vr_credito, 0) as vr_credito,
            pt.historico,
            cc.codigo as centro_custo,
            (select
            fcs.codigo as contra_partida
            from ecd_lancamento_contabil lcs
            join ecd_partida_lancamento pts on pts.lancamento_id = lcs.id
            join finan_conta fcs on fcs.id = pts.conta_id
            where
            lcs.id = lc.id
            and pts.id != pt.id
            and pts.tipo != pt.tipo
            limit 1
            ) as contra_partidada

        from ecd_lancamento_contabil lc
            join ecd_partida_lancamento pt on pt.lancamento_id = lc.id
            left join finan_centrocusto cc on cc.id = pt.centrocusto_id
            join finan_conta fc on fc.id = pt.conta_id
            join ecd_plano_conta ep on ep.id = fc.plano_id
            join res_company c on c.plano_id = ep.id and c.id = lc.company_id
            join res_partner rp on rp.id = c.partner_id

        where
            lc.data between '{data_inicial}' and '{data_final}'"""

      

sql_balancete_antigo = """
        select
            coalesce((select r.razao_social from res_partner r where r.cnpj_cpf = rp.cnpj_cpf limit 1),'') as empresa,
            rp.cnpj_cpf,
            coalesce(fc.codigo, 0) as codigo,
            coalesce(fc.codigo_completo,'') as codigo_completo,
            coalesce(fc.nome, '') as nome,
            case
            when fc.tipo = 'A' then
            'Ativo'
            when fc.tipo = 'P' then
            'Passivo'
            when fc.tipo = 'R' then
            'Receita'
            when fc.tipo = 'C' then
            'Custo'
            when fc.tipo = 'D' then
            'Despesa'
            when fc.tipo = 'T' then
            'Transferência'
            when fc.tipo = 'O' then
            'Outras' end as tipo,
            fc.sintetica,

            (select
            coalesce(sum(es.saldo),0)  as saldo_anterior
            
            from ecd_saldo es
            join finan_conta fcs on fcs.id = es.conta_id
            join res_company css on css.id = es.company_id
            join res_partner rps on rps.id = css.partner_id
            
            where
            fcs.codigo_completo like fc.codigo_completo || '%'
            and es.data = cast('{data_inicial}' as date) + interval '-1 day'                        
            and rps.cnpj_cpf = rp.cnpj_cpf
            and css.id = c.id            
            ) as saldo_anterior,

            (select
            coalesce(sum(cast(pts.vr_debito as numeric(18,2))), 0) as total_debito
            from ecd_lancamento_contabil lcs
            join ecd_partida_lancamento pts on pts.lancamento_id = lcs.id
            join finan_conta fcs on fcs.id = pts.conta_id
            join res_company cs on cs.id = lcs.company_id
            join res_partner rps on rps.id = cs.partner_id
            where
            fcs.codigo_completo like fc.codigo_completo || '%'
            and lcs.data between '{data_inicial}' and '{data_final}'
            and cs.id = c.id
            and rps.cnpj_cpf = rp.cnpj_cpf
            ) as total_debito,

            (select
            coalesce(sum(cast(pts.vr_credito as numeric(18,2))), 0) as total_credito
            from ecd_lancamento_contabil lcs
            join ecd_partida_lancamento pts on pts.lancamento_id = lcs.id
            join finan_conta fcs on fcs.id = pts.conta_id
            join res_company cs on cs.id = lcs.company_id
            join res_partner rps on rps.id = cs.partner_id
            where
            fcs.codigo_completo like fc.codigo_completo || '%'
            and lcs.data between '{data_inicial}' and '{data_final}'
            and cs.id = c.id
            and rps.cnpj_cpf = rp.cnpj_cpf
            ) as total_credito

        from finan_conta fc
            join ecd_plano_conta ep on ep.id = fc.plano_id
            join res_company c on c.plano_id = ep.id
            join res_partner rp on rp.id = c.partner_id
            left join ecd_partida_lancamento pt on pt.conta_id = fc.id
            left join ecd_lancamento_contabil lc on  lc.id = pt.lancamento_id
        where """

      

sql_balanco_antigo = """        
        select
            coalesce((select r.razao_social from res_partner r where r.cnpj_cpf = rp.cnpj_cpf limit 1),'') as empresa,
            rp.cnpj_cpf,
            coalesce(fc.codigo, 0) as codigo,
            coalesce(fc.codigo_completo,'') as codigo_completo,
            coalesce(fc.nome, '') as nome,
            case
            when fc.tipo = 'A' then
            'Ativo'
            when fc.tipo = 'P' then
            'Passivo'
            end as tipo,
            fc.sintetica,

            (select
            coalesce(sum(cast(pts.vr_debito as numeric(18,2))) - sum(cast(pts.vr_credito as numeric(18,2))), 0) as saldo_anterior
            from ecd_lancamento_contabil lcs
            join ecd_partida_lancamento pts on pts.lancamento_id = lcs.id
            join finan_conta fcs on fcs.id = pts.conta_id
            join res_company cs on cs.id = lcs.company_id
            join res_partner rps on rps.id = cs.partner_id
            where
            fcs.codigo_completo like fc.codigo_completo || '%'
            and lcs.data < '{data_final}'
            and rps.cnpj_cpf = rp.cnpj_cpf
            ) as saldo_aTUAL

        from finan_conta fc
            join ecd_plano_conta ep on ep.id = fc.plano_id
            join res_company c on c.plano_id = ep.id
            join res_partner rp on rp.id = c.partner_id
            left join ecd_partida_lancamento pt on pt.conta_id = fc.id
            left join ecd_lancamento_contabil lc on  lc.id = pt.lancamento_id
        where
            fc.tipo in ('A','P')"""