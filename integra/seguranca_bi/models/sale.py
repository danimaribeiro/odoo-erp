# -*- encoding: utf-8 -*-


from openerp.osv import osv, fields
import pymssql


SQL_CREATE_BI_SEGURANCA_OS = """
CREATE TABLE dbo.seguranca_os
(
  cliente_integra VARCHAR(30)
, empresa VARCHAR(120)
, grupo VARCHAR(120)
, "DATA" DATETIME
, cliente VARCHAR(60)
, vendedor VARCHAR(30)
, tecnico VARCHAR(30)
, numero VARCHAR(20)
, prioridade VARCHAR(20)
, etapa VARCHAR(180)
);
"""


SQL_DADOS = """
select
    cast(c.name as varchar(120)) as empresa,
    cast(cc.name as varchar(120)) as grupo,
    cast(s.date_order as date) as data,
    cast(coalesce(rp.name, '') as varchar(60)) as cliente,
    cast(coalesce(v.name, '') as varchar(30)) as vendedor,
    cast(coalesce(t.name, '') as varchar(30)) as tecnico,
    cast(coalesce(s.name, '') as varchar(20)) as numero,
    cast(coalesce(p.nome, '') as varchar(20)) as prioridade,
    cast(coalesce(e.nome, '') as varchar(180)) as etapa

from
    sale_order s
    join res_company c on c.id = s.company_id
    left join res_company cc on cc.id = c.parent_id
    left join res_partner rp on rp.id = s.partner_id
    left join res_users v on v.id = s.user_id
    left join res_users t on t.id = s.tecnico_id
    left join sale_prioridade_os p on p.id = s.prioridade_id
    left join sale_etapa e on e.id = s.etapa_id

where
    e.tipo = 'O';
"""


SQL_INSERE = u"""
insert into seguranca_os
    (cliente_integra, empresa, grupo, "DATA", cliente, vendedor, tecnico, numero, prioridade, etapa)
    values ('{banco}', '{empresa}', '{grupo}', '{data}', '{cliente}', '{vendedor}', '{tecnico}', '{numero}', '{prioridade}', '{etapa}');
"""


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    def bi_seguranca_os(self, cr, uid, ids=[], context={}):
        conn = pymssql.connect('sqlcloud.ascentservicos.com.br', 'USR_DW_ntegra_00185', '731064866', 'DW_ntegra_00185', port=1500)
        #cursor = conn.cursor(as_dict=True)
        cursor = conn.cursor()

        banco = cr.dbname.lower()

        #cursor.execute(SQL_CREATE_BI_SEGURANCA_OS)
        #cursor.execute(u"delete from seguranca_os where cliente_integra = '{banco}';".format(banco=banco))
        cursor.execute(u"delete from seguranca_os;".format(banco=banco))

        sql = SQL_DADOS.format(banco=banco)
        cr.execute(sql)
        dados = cr.fetchall()

        for empresa, grupo, data, cliente, vendedor, tecnico, numero, prioridade, etapa in dados:
            sql = SQL_INSERE.format(banco=banco, empresa=empresa, grupo=grupo, data=data.replace('-', ''), cliente=cliente, vendedor=vendedor, tecnico=tecnico, numero=numero, prioridade=prioridade, etapa=etapa)
            print(sql.encode('utf-8'))
            cursor.execute(sql.encode('utf-8'))

        conn.commit()
        conn.close()


sale_order()
