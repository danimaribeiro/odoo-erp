# -*- encoding: utf-8 -*-


from openerp.osv import osv, fields
import pymssql


SQL_CREATE_BI_EYTANMAGAL = """
DROP TABLE dbo.eytanmagal;

CREATE TABLE dbo.eytanmagal
(
    cliente_integra VARCHAR(30),

    empresa VARCHAR(120),
    grupo VARCHAR(120),

    projeto_pai VARCHAR(128),
    projeto_pai_data_inicial DATETIME,
    projeto_pai_data_final DATETIME,
    projeto_pai_responsavel VARCHAR(60),
    projeto_pai_versao VARCHAR(60),

    projeto VARCHAR(128),

    cliente VARCHAR(120),

    tarefa VARCHAR(128),
    tarefa_data_inicial DATETIME,
    tarefa_data_final DATETIME,
    frequencia VARCHAR(60),
    estado VARCHAR(20),
    estagio VARCHAR(64),
    sequencia INTEGER,
    data_limite DATETIME,
    atribuido VARCHAR(60)
);
"""


SQL_DADOS = """
select
    cast(coalesce(c.name, '') as varchar(120)) as empresa,
    cast(coalesce(cc.name, '') as varchar(120)) as grupo,

    cast(coalesce(aap.name, '') as varchar(128)) as projeto_pai,
    aap.date_start as projeto_pai_data_inicial,
    aap.date as projeto_pai_data_final,
    cast(coalesce(ppu.name, '') as varchar(60)) as projeto_pai_responsavel,
    cast(coalesce(pp.versao, '') as varchar(60)) as projeto_pai_versao,

    cast(coalesce(aa.name, '') as varchar(128)) as projeto,

    cast(coalesce(cli.name, coalesce(clip.name, '')) as varchar(120)) as cliente,

    cast(coalesce(t.name, '') as varchar(128)) as tarefa,
    t.date_start as tarefa_data_inicial,
    t.date_end as tarefa_data_final,
    cast(coalesce(t.frequencia, '') as varchar(60)) as frequencia,
    case
        when t.state = 'draft' then 'Nova'
        when t.state = 'open' then 'Em andamento'
        when t.state = 'pending' then 'Pendente'
        when t.state = 'done' then 'Concluída'
        when t.state = 'cancelled' then 'Cancelada'
        else ''
    end as estado,
    cast(coalesce(e.name, '') as varchar(64)) as estagio,
    coalesce(t.sequence, 0) as sequencia,
    t.date_deadline as data_limite,
    cast(coalesce(u.name, '') as varchar(60)) as atribuido

from
    project_task t

    join project_project p on t.project_id = p.id
    join account_analytic_account aa on aa.id = p.analytic_account_id
    left join account_analytic_account aap on aap.id = aa.parent_id
    left join project_project pp on pp.analytic_account_id = aa.parent_id

    left join res_partner cli on cli.id = aa.partner_id
    left join res_partner clip on clip.id = aap.partner_id

    left join project_task_type e on e.id = t.type_id

    left join res_users u on u.id = t.user_id
    left join res_users ppu on ppu.id = aap.user_id

    left join res_company c on c.id = t.company_id
    left join res_company cc on cc.id = c.parent_id

--where
--    e.tipo = 'O';
"""


SQL_INSERE = u"""
insert into eytanmagal
    (cliente_integra, empresa, grupo,
    projeto_pai, projeto_pai_data_inicial, projeto_pai_data_final, projeto_pai_responsavel, projeto_pai_versao,
    projeto,
    cliente,
    tarefa, tarefa_data_inicial, tarefa_data_final,
    frequencia, estado, estagio, sequencia, data_limite, atribuido)
    values ('{banco}', '{empresa}', '{grupo}',
    '{projeto_pai}', {projeto_pai_data_inicial}, {projeto_pai_data_final}, '{projeto_pai_responsavel}', '{projeto_pai_versao}',
    '{projeto}',
    '{cliente}',
    '{tarefa}', {tarefa_data_inicial}, {tarefa_data_final},
    '{frequencia}', '{estado}', '{estagio}', {sequencia}, {data_limite}, '{atribuido}');
"""


class project_task(osv.Model):
    _inherit = 'project.task'
    _name = 'project.task'

    _columns = {
        'frequencia': fields.char(u'Frequência', size=60),
    }

    def bi_eytanmagal(self, cr, uid, ids=[], context={}):
        conn = pymssql.connect('sqlcloud.ascentservicos.com.br', 'USR_DW_ntegra_00185', '731064866', 'DW_ntegra_00185', port=1500)
        #cursor = conn.cursor(as_dict=True)
        cursor = conn.cursor()

        banco = cr.dbname.lower()

        cursor.execute(SQL_CREATE_BI_EYTANMAGAL)
        cursor.execute(u"delete from eytanmagal where cliente_integra = '{banco}';".format(banco=banco))
        #cursor.execute(u"delete from eytanmagal;".format(banco=banco))

        sql = SQL_DADOS.format(banco=banco)
        cr.execute(sql)
        dados = cr.fetchall()

        for empresa, grupo, \
            projeto_pai, projeto_pai_data_inicial, projeto_pai_data_final, projeto_pai_responsavel, projeto_pai_versao, \
            projeto, \
            cliente, \
            tarefa, tarefa_data_inicial, tarefa_data_final, \
            frequencia, estado, estagio, sequencia, data_limite, atribuido in dados:
            filtro = {
                'banco': banco,
                'empresa': empresa,
                'grupo': grupo,

                'projeto_pai': projeto_pai,
                'projeto_pai_data_inicial': "'" + projeto_pai_data_inicial.replace('-', '') + "'" if projeto_pai_data_inicial else 'null',
                'projeto_pai_data_final': "'" + projeto_pai_data_final.replace('-', '') + "'" if projeto_pai_data_final else 'null',
                'projeto_pai_responsavel': projeto_pai_responsavel,
                'projeto_pai_versao': projeto_pai_versao,

                'projeto': projeto,

                'cliente': cliente,

                'tarefa': tarefa,
                'tarefa_data_inicial': "'" + tarefa_data_inicial.replace('-', '') + "'" if tarefa_data_inicial else 'null',
                'tarefa_data_final': "'" + tarefa_data_final.replace('-', '') + "'" if tarefa_data_final else 'null',

                'frequencia': frequencia,
                'estado': estado,
                'estagio': estagio,
                'sequencia': sequencia,
                'data_limite': "'" + data_limite.replace('-', '') + "'" if data_limite else 'null',
                'atribuido': atribuido,
            }
            sql = SQL_INSERE.format(**filtro)
            print(sql.encode('utf-8'))
            cursor.execute(sql.encode('utf-8'))

        conn.commit()
        conn.close()


project_task()
