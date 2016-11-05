# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv


TIPO_CONTA_ATIVO = 'A'
TIPO_CONTA_PASSIVO = 'P'
TIPO_CONTA_TRANSFERENCIA = 'T'
TIPO_CONTA_RECEITA = 'R'
TIPO_CONTA_DESPESA = 'D'
TIPO_CONTA_CUSTO = 'C'
TIPO_CONTA_OUTRAS = 'O'
TIPO_CONTA_PATRIMONIO = 'PL'
TIPO_CONTA_COMPENSACAO = 'CP'
#TIPO_CONTA_RATEIO_RECEITA = 'RR'
#TIPO_CONTA_RATEIO_DESPESA = 'RD'


TIPO_RECEITA_DESPESA = (
    (TIPO_CONTA_ATIVO, u'Ativo'),
    (TIPO_CONTA_PASSIVO, u'Passivo'),    
    (TIPO_CONTA_RECEITA, u'Receita'),
    (TIPO_CONTA_DESPESA, u'Despesa'),
    (TIPO_CONTA_CUSTO, u'Custo'),
    (TIPO_CONTA_TRANSFERENCIA, u'Transferência'),
    (TIPO_CONTA_OUTRAS, u'Outras'),
    (TIPO_CONTA_PATRIMONIO, u'Patrimonio Líquido'),
    (TIPO_CONTA_COMPENSACAO, u'Compensação'),
    #(TIPO_CONTA_RATEIO_RECEITA, u'Rateio de receitas'),
    #(TIPO_CONTA_RATEIO_DESPESA, u'Rateio de despesas'),
)

TIPO_CONTA_DIC = dict(TIPO_RECEITA_DESPESA)

SQL_ARVORE = """
    SELECT
        c1.id AS conta_pai_id,
        c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
        1 as nivel
    FROM finan_conta c1
    WHERE coalesce(c1.sintetica, False) = false
    UNION ALL
    SELECT c2.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        2 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
    WHERE coalesce(c1.sintetica, False) = false
    UNION ALL
    SELECT c3.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        3 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
    WHERE coalesce(c1.sintetica, False) = false
    UNION ALL
    SELECT c4.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        4 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
        JOIN finan_conta c4 ON c4.id = c3.parent_id
    WHERE coalesce(c1.sintetica, False) = false
    UNION ALL
    SELECT c5.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        5 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
        JOIN finan_conta c4 ON c4.id = c3.parent_id
        JOIN finan_conta c5 ON c5.id = c4.parent_id
    WHERE coalesce(c1.sintetica, False) = false
    UNION ALL
    SELECT c6.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        6 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
        JOIN finan_conta c4 ON c4.id = c3.parent_id
        JOIN finan_conta c5 ON c5.id = c4.parent_id
        JOIN finan_conta c6 ON c6.id = c5.parent_id
    WHERE coalesce(c1.sintetica, False) = false
    UNION ALL
    SELECT c7.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        7 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
        JOIN finan_conta c4 ON c4.id = c3.parent_id
        JOIN finan_conta c5 ON c5.id = c4.parent_id
        JOIN finan_conta c6 ON c6.id = c5.parent_id
        JOIN finan_conta c7 ON c7.id = c6.parent_id
    WHERE coalesce(c1.sintetica, False) = false

    UNION ALL
    SELECT c8.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        8 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
        JOIN finan_conta c4 ON c4.id = c3.parent_id
        JOIN finan_conta c5 ON c5.id = c4.parent_id
        JOIN finan_conta c6 ON c6.id = c5.parent_id
        JOIN finan_conta c7 ON c7.id = c6.parent_id
        JOIN finan_conta c8 ON c8.id = c7.parent_id
    WHERE coalesce(c1.sintetica, False) = false

    UNION ALL
    SELECT c9.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        9 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
        JOIN finan_conta c4 ON c4.id = c3.parent_id
        JOIN finan_conta c5 ON c5.id = c4.parent_id
        JOIN finan_conta c6 ON c6.id = c5.parent_id
        JOIN finan_conta c7 ON c7.id = c6.parent_id
        JOIN finan_conta c8 ON c8.id = c7.parent_id
        JOIN finan_conta c9 ON c9.id = c8.parent_id
    WHERE coalesce(c1.sintetica, False) = false

    UNION ALL
    SELECT c10.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        10 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
        JOIN finan_conta c4 ON c4.id = c3.parent_id
        JOIN finan_conta c5 ON c5.id = c4.parent_id
        JOIN finan_conta c6 ON c6.id = c5.parent_id
        JOIN finan_conta c7 ON c7.id = c6.parent_id
        JOIN finan_conta c8 ON c8.id = c7.parent_id
        JOIN finan_conta c9 ON c9.id = c8.parent_id
        JOIN finan_conta c10 ON c10.id = c9.parent_id
    WHERE coalesce(c1.sintetica, False) = false

    UNION ALL
    SELECT c11.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        11 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
        JOIN finan_conta c4 ON c4.id = c3.parent_id
        JOIN finan_conta c5 ON c5.id = c4.parent_id
        JOIN finan_conta c6 ON c6.id = c5.parent_id
        JOIN finan_conta c7 ON c7.id = c6.parent_id
        JOIN finan_conta c8 ON c8.id = c7.parent_id
        JOIN finan_conta c9 ON c9.id = c8.parent_id
        JOIN finan_conta c10 ON c10.id = c9.parent_id
        JOIN finan_conta c11 ON c11.id = c10.parent_id
    WHERE coalesce(c1.sintetica, False) = false


    UNION ALL
    SELECT c12.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        12 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
        JOIN finan_conta c4 ON c4.id = c3.parent_id
        JOIN finan_conta c5 ON c5.id = c4.parent_id
        JOIN finan_conta c6 ON c6.id = c5.parent_id
        JOIN finan_conta c7 ON c7.id = c6.parent_id
        JOIN finan_conta c8 ON c8.id = c7.parent_id
        JOIN finan_conta c9 ON c9.id = c8.parent_id
        JOIN finan_conta c10 ON c10.id = c9.parent_id
        JOIN finan_conta c11 ON c11.id = c10.parent_id
        JOIN finan_conta c12 ON c12.id = c11.parent_id
    WHERE coalesce(c1.sintetica, False) = false

    UNION ALL
    SELECT c13.id AS conta_pai_id,
        c1.id AS conta_id,
            CASE
                WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
                ELSE 1
            END AS redutora,
        13 as nivel
    FROM finan_conta c1
        JOIN finan_conta c2 ON c2.id = c1.parent_id
        JOIN finan_conta c3 ON c3.id = c2.parent_id
        JOIN finan_conta c4 ON c4.id = c3.parent_id
        JOIN finan_conta c5 ON c5.id = c4.parent_id
        JOIN finan_conta c6 ON c6.id = c5.parent_id
        JOIN finan_conta c7 ON c7.id = c6.parent_id
        JOIN finan_conta c8 ON c8.id = c7.parent_id
        JOIN finan_conta c9 ON c9.id = c8.parent_id
        JOIN finan_conta c10 ON c10.id = c9.parent_id
        JOIN finan_conta c11 ON c11.id = c10.parent_id
        JOIN finan_conta c12 ON c12.id = c11.parent_id
        JOIN finan_conta c13 ON c13.id = c12.parent_id
    WHERE coalesce(c1.sintetica, False) = false;
"""

SQL_ARVORE_GERAL = """
SELECT
    c1.id AS conta_pai_id,
    c1.id AS conta_id,
    CASE
        WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
        ELSE 1
    END AS redutora,
    1 as nivel
FROM finan_conta c1

UNION ALL
SELECT c2.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    2 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id

UNION ALL
SELECT c3.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    3 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id

UNION ALL
SELECT c4.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    4 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id
    JOIN finan_conta c4 ON c4.id = c3.parent_id

UNION ALL
SELECT c5.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    5 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id
    JOIN finan_conta c4 ON c4.id = c3.parent_id
    JOIN finan_conta c5 ON c5.id = c4.parent_id

UNION ALL
SELECT c6.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    6 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id
    JOIN finan_conta c4 ON c4.id = c3.parent_id
    JOIN finan_conta c5 ON c5.id = c4.parent_id
    JOIN finan_conta c6 ON c6.id = c5.parent_id

UNION ALL
SELECT c7.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    7 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id
    JOIN finan_conta c4 ON c4.id = c3.parent_id
    JOIN finan_conta c5 ON c5.id = c4.parent_id
    JOIN finan_conta c6 ON c6.id = c5.parent_id
    JOIN finan_conta c7 ON c7.id = c6.parent_id


UNION ALL
SELECT c8.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    8 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id
    JOIN finan_conta c4 ON c4.id = c3.parent_id
    JOIN finan_conta c5 ON c5.id = c4.parent_id
    JOIN finan_conta c6 ON c6.id = c5.parent_id
    JOIN finan_conta c7 ON c7.id = c6.parent_id
    JOIN finan_conta c8 ON c8.id = c7.parent_id


UNION ALL
SELECT c9.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    9 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id
    JOIN finan_conta c4 ON c4.id = c3.parent_id
    JOIN finan_conta c5 ON c5.id = c4.parent_id
    JOIN finan_conta c6 ON c6.id = c5.parent_id
    JOIN finan_conta c7 ON c7.id = c6.parent_id
    JOIN finan_conta c8 ON c8.id = c7.parent_id
    JOIN finan_conta c9 ON c9.id = c8.parent_id


UNION ALL
SELECT c10.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    10 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id
    JOIN finan_conta c4 ON c4.id = c3.parent_id
    JOIN finan_conta c5 ON c5.id = c4.parent_id
    JOIN finan_conta c6 ON c6.id = c5.parent_id
    JOIN finan_conta c7 ON c7.id = c6.parent_id
    JOIN finan_conta c8 ON c8.id = c7.parent_id
    JOIN finan_conta c9 ON c9.id = c8.parent_id
    JOIN finan_conta c10 ON c10.id = c9.parent_id

UNION ALL
SELECT c11.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    11 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id
    JOIN finan_conta c4 ON c4.id = c3.parent_id
    JOIN finan_conta c5 ON c5.id = c4.parent_id
    JOIN finan_conta c6 ON c6.id = c5.parent_id
    JOIN finan_conta c7 ON c7.id = c6.parent_id
    JOIN finan_conta c8 ON c8.id = c7.parent_id
    JOIN finan_conta c9 ON c9.id = c8.parent_id
    JOIN finan_conta c10 ON c10.id = c9.parent_id
    JOIN finan_conta c11 ON c11.id = c10.parent_id



UNION ALL
SELECT c12.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    12 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id
    JOIN finan_conta c4 ON c4.id = c3.parent_id
    JOIN finan_conta c5 ON c5.id = c4.parent_id
    JOIN finan_conta c6 ON c6.id = c5.parent_id
    JOIN finan_conta c7 ON c7.id = c6.parent_id
    JOIN finan_conta c8 ON c8.id = c7.parent_id
    JOIN finan_conta c9 ON c9.id = c8.parent_id
    JOIN finan_conta c10 ON c10.id = c9.parent_id
    JOIN finan_conta c11 ON c11.id = c10.parent_id
    JOIN finan_conta c12 ON c12.id = c11.parent_id


UNION ALL
SELECT c13.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    13 as nivel
FROM finan_conta c1
    JOIN finan_conta c2 ON c2.id = c1.parent_id
    JOIN finan_conta c3 ON c3.id = c2.parent_id
    JOIN finan_conta c4 ON c4.id = c3.parent_id
    JOIN finan_conta c5 ON c5.id = c4.parent_id
    JOIN finan_conta c6 ON c6.id = c5.parent_id
    JOIN finan_conta c7 ON c7.id = c6.parent_id
    JOIN finan_conta c8 ON c8.id = c7.parent_id
    JOIN finan_conta c9 ON c9.id = c8.parent_id
    JOIN finan_conta c10 ON c10.id = c9.parent_id
    JOIN finan_conta c11 ON c11.id = c10.parent_id
    JOIN finan_conta c12 ON c12.id = c11.parent_id
    JOIN finan_conta c13 ON c13.id = c12.parent_id;
"""

SQL_CRIA_ARVORE = """
    drop table if exists finan_conta_arvore cascade;

    create table finan_conta_arvore as
""" + SQL_ARVORE


SQL_AJUSTA_ARVORE = """
    delete from finan_conta_arvore;

    insert into finan_conta_arvore
    (conta_pai_id, conta_id, redutora, nivel)
""" + SQL_ARVORE

SQL_CRIA_ARVORE_GERAL = """
    drop table if exists finan_conta_arvore_geral cascade;

    create table finan_conta_arvore_geral as
""" + SQL_ARVORE_GERAL

SQL_AJUSTA_ARVORE_GERAL = """
    delete from finan_conta_arvore_geral;

    insert into finan_conta_arvore_geral
    (conta_pai_id, conta_id, redutora, nivel)
""" + SQL_ARVORE_GERAL

class finan_conta(orm.Model):
    _name = 'finan.conta'
    _description = 'Conta Financeira'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'codigo_completo'
    _order = 'parent_left'
    _rec_name = 'nome_simples'

    def monta_nome(self, cr, uid, id, context={}):

        conta_obj = self.browse(cr, uid, id)

        nome = conta_obj.nome

        if not context.get('conta_simples'):
            if conta_obj.parent_id:
                nome = self.monta_nome(cr, uid, conta_obj.parent_id.id) + u' / ' + nome

        return nome

    def nome_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []

        for obj in self.browse(cr, uid, ids):
            res.append((obj.id, '[' + str(obj.codigo) + '] ' + obj.codigo_completo + ' - ' + self.monta_nome(cr, uid, obj.id, context=context)))

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):

        res = self.nome_get(cr, uid, ids, context=context)
        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        conta_reduzida = 0
        try:
            conta_reduzida = int(texto)
        except:
            pass

        if conta_reduzida:
            procura = [
                '|', '|',
                ('nome_completo', 'ilike', texto),
                ('codigo_completo', 'ilike', texto),
                ('codigo', '=', conta_reduzida)
            ]

        else:
            procura = [
                '|',
                ('nome_completo', 'ilike', texto),
                ('codigo_completo', 'ilike', texto)
            ]

        return procura

    def monta_codigo(self, cr, uid, id):
        conta_obj = self.browse(cr, uid, id)

        tamanho_maximo = 1

        if conta_obj.parent_id:
            cr.execute('select max(codigo) from finan_conta where parent_id = ' + str(conta_obj.parent_id.id) + ';')
            res = cr.fetchall()[0][0]
            tamanho_maximo = len(str(res))

        codigo = str(conta_obj.codigo).zfill(tamanho_maximo)

        if conta_obj.parent_id:
            codigo = self.monta_codigo(cr, uid, conta_obj.parent_id.id) + '.' + codigo

        return codigo

    def get_codigo(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for id in ids:
            res += [(id, self.monta_codigo(cr, uid, id))]

        return res

    def _get_codigo_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_codigo(cr, uid, ids, context=context)
        return dict(res)
    
    def _get_nivel(self, cr, uid, ids, nome_campo, arg, context=None):
        if not len(ids):
            return {}

        res = {}
        for id in ids:
            sql = """
            select max(nivel)
            from finan_conta_arvore_geral
            where 
            conta_id = """ + str(id)
            
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) > 0:
                res[id] = dados[0][0]  
            else:   
                res[id] = False
             
        return res
    
    _columns = {
        'nome': fields.char(u'Nome', size=64, required=True, select=True),
        'codigo': fields.integer(u'Conta reduzida', select=True, required=False),
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Descrição', fnct_search=_procura_nome, store=True, select=True),
        'nome_simples': fields.function(_get_nome_funcao, type='char', string=u'Descrição', fnct_search=_procura_nome),
        #'codigo_completo': fields.function(_get_codigo_funcao, type='char', string=u'Código completo', store=True),
        'codigo_completo': fields.char(u'Código completo', size=64, select=True),
        'parent_id': fields.many2one('finan.conta', u'Conta pai', select=True, ondelete='cascade'),
        'contas_filhas_ids': fields.one2many('finan.conta', 'parent_id', string=u'Contas filhas'),
        'tipo': fields.selection(TIPO_RECEITA_DESPESA, u'Tipo', select=True),
        'sintetica': fields.boolean(u'Sintética', select=True),
        'parent_left': fields.integer(u'Conta à esquerda', select=1),
        'parent_right': fields.integer(u'Conta a direita', select=1),
        'exige_centro_custo': fields.boolean(u'Exige centro de custo/rateio?'),
        'historico': fields.text(u'Histórico'),
        'account_account_id': fields.many2one('account.account', u'Conta contábil', ondelete='cascade'),
        'conta_complementar_despesa_id': fields.many2one('finan.conta', u'Conta complementar de despesa'),
        'conta_complementar_custo_id': fields.many2one('finan.conta', u'Conta complementar de custo'),
        'conta_custo_revenda_id': fields.many2one('finan.conta', u'Conta de custo de compra para revenda'),
        'conta_custo_ativo_id': fields.many2one('finan.conta', u'Conta de custo de compra para ativo'),
        'conta_receita_ativo_id': fields.many2one('finan.conta', u'Conte de receita não operacional (ativo)'),
        'hr_department_id': fields.integer(u'Departamento/posto', select=True),
        'nivel_conta': fields.function(_get_nivel, type='char', string=u'Nivel Conta', store=False, select=True), 
        'data': fields.date(u'Data'),                
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),        
        'write_date': fields.datetime( u'Data Ultima Alteração'),
        'inativa': fields.boolean( u'Inativar?'),             
        'data_inativacao': fields.date(u'Data Inativação'),  
    }

    _defaults = {
        'tipo': 'D',
        'sintetica': False,
        'exige_centro_custo': True,
        'data': fields.datetime.now,
    }

    _sql_constraints = [
        ('codigo_completo_unique', 'unique(codigo_completo)',
            u'O código não pode se repetir!'),
    ]

    def _verifica_recursiva(self, cr, uid, ids, context={}):
        nivel_recursao = 100

        while len(ids):
            cr.execute('select distinct parent_id from finan_conta where id in %s', (tuple(ids),))

            ids = filter(None, map(lambda x: x[0], cr.fetchall()))

            if not nivel_recursao:
                return False

            nivel_recursao -= 1

        return True

    def _verifica_grupos(self, cr, uid, ids, context={}):

        for conta_obj in self.browse(cr, uid, ids):
            if conta_obj.parent_id:
                conta_pai = conta_obj.parent_id.codigo_completo

                if not conta_obj.codigo_completo.startswith(conta_pai + '.'):
                    return False

                codigo = conta_obj.codigo_completo.replace(conta_pai + '.', '')

                if '.' in codigo:
                    return False

        return True

    _constraints = [
        (_verifica_recursiva, u'Erro! Não é possível criar contas recursivas', ['parent_id']),
        #(_verifica_grupos, u'Erro! O código da conta deve conter o código da conta pai', ['codigo_completo'])
    ]

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)',
         u'O Código reduzido ja existente!'),
    ]


    def child_get(self, cr, uid, ids):
        return [ids]

    def valida_contas(self, cr, uid, ids, vals):
        if ids:
            if isinstance(ids, (int, long)):
                conta_obj = self.browse(cr, uid, ids)
            else:
                conta_obj = self.browse(cr, uid, ids[0])
        else:
            conta_obj = None

        parent_obj = None
        if 'parent_id' in vals and vals['parent_id']:
            parent_obj = self.browse(cr, uid, vals['parent_id'])
        elif conta_obj:
            parent_obj = getattr(conta_obj, 'parent_id', None)

        sintetica = False
        if 'sintetica' in vals:
            sintetica = vals['sintetica']
        elif conta_obj:
            sintetica = getattr(conta_obj, 'sintetica', False)

        tipo = 'O'
        if 'tipo' in vals:
            tipo = vals['tipo']
        elif conta_obj:
            tipo = getattr(conta_obj, 'tipo', 'O')

        receita = tipo == TIPO_CONTA_RECEITA
        despesa = tipo == TIPO_CONTA_DESPESA

        if (not sintetica) and (not parent_obj):
            if conta_obj:
                raise osv.except_osv((u'Inválido !'), (u'Conta analítica %s deve ter obrigatoriamente uma conta pai.' % conta_obj.codigo_completo))

            else:
                raise osv.except_osv((u'Inválido !'), (u'Conta analítica deve ter obrigatoriamente uma conta pai.'))

        if parent_obj:
            if parent_obj.tipo != tipo and parent_obj.tipo != 'O' and parent_obj.tipo != 'PL':
                tipo_desc = TIPO_CONTA_DIC[tipo]
                tipo_desc_pai = TIPO_CONTA_DIC[parent_obj.tipo]
                raise osv.except_osv(u'Inválido !', u'Conta de {tipo_desc} não pode ter uma conta pai de {tipo_desc_pai}.'.format(tipo_desc=tipo_desc, tipo_desc_pai=tipo_desc_pai))

        return True

    def create(self, cr, user, vals, context={}):
        self.valida_contas(cr, user, [], vals)

        res = super(finan_conta, self).create(cr, user, vals, context)

        self.sincroniza_contabil(cr, user, [res], context=context)

        cr.execute(SQL_AJUSTA_ARVORE)
        cr.execute(SQL_AJUSTA_ARVORE_GERAL)

        return res

    def write(self, cr, user, ids, vals, context={}):
        self.valida_contas(cr, user, ids, vals)

        res = super(finan_conta, self).write(cr, user, ids, vals, context=context)

        self.sincroniza_contabil(cr, user, ids, context=context)

        cr.execute(SQL_AJUSTA_ARVORE)
        cr.execute(SQL_AJUSTA_ARVORE_GERAL)

        return res

    def unlink(self, cr, uid, ids, context={}):
        res = super(finan_conta, self).unlink(cr, uid, ids, context=context)

        cr.execute(SQL_AJUSTA_ARVORE)
        cr.execute(SQL_AJUSTA_ARVORE_GERAL)

        return res

    def recalcula_ordem_parent_left_parent_right(self, cr, uid, ids, context):
        cr.execute('update account_account set parent_id = null;')
        conta_pool = self.pool.get('finan.conta')

        cr.commit()
        for obj in conta_pool.browse(cr, uid, self.search(cr, uid, [])):
            conta_pool.write(cr, uid, obj.id, {'nome': obj.nome + ' '}, context={'ajusta_contabil': False})
            cr.commit()

        for obj in conta_pool.browse(cr, uid, self.search(cr, uid, [])):
            conta_pool.write(cr, uid, obj.id, {'nome': obj.nome.strip()})
            cr.commit()

    def onchange_parent_id(self, cr, uid, ids, parent_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not parent_id:
            return res

        pai_obj = self.browse(cr, uid, parent_id)
        valores['codigo_completo'] = pai_obj.codigo_completo + '.'
        valores['tipo'] = pai_obj.tipo

        return res

    def sincroniza_contabil(self, cr, uid, ids, context={}):
        conta_pool = self.pool.get('finan.conta')

        ajusta_contabil = context.get('ajusta_contabil', True)

        if not ajusta_contabil:
            return

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for obj in conta_pool.browse(cr, uid, ids, context=context):
            dados_conta = {
                'code': obj.codigo_completo,
                'name': obj.nome,
                #'company_id': 1,
                'active': True,
                'user_type': 1,
                'reconcile': False,
            }

            if obj.sintetica:
                dados_conta['type'] = 'view'
            elif obj.tipo == 'D':
                dados_conta['type'] = 'payable'
            elif obj.tipo == 'R':
                dados_conta['type'] = 'receivable'
            else:
                dados_conta['type'] = 'other'

            if obj.parent_id and obj.parent_id.account_account_id:
                dados_conta['parent_id'] = obj.parent_id.account_account_id.id
            else:
                dados_conta['parent_id'] = False

            if not obj.account_account_id:
                aa_pool = self.pool.get('account.account')
                aa_ids = aa_pool.search(cr, uid, [('code', '=', obj.codigo_completo)])

                if len(aa_ids):
                    aa_id = aa_ids[0]
                    print('ajustou ja tinha', aa_ids)
                else:
                    print('vai criar', dados_conta)
                    aa_id = self.pool.get('account.account').create(cr, uid, dados_conta)

                cr.execute('update finan_conta set account_account_id = %s where id = %s', (aa_id, obj.id))
                print('vai atualizar', dados_conta)
                aa_pool.write(cr, uid, [aa_id], dados_conta)

            else:
                print('ja tinha, vai atualizar', dados_conta)
                obj.account_account_id.write(dados_conta)

    def importa_plano(self, cr, uid, ids, context={}):
        conta_pool = self.pool.get('finan.conta')
        arq = open('/home/di_distribuidora/plano_contas.csv', 'r')

        cr.execute('update finan_conta set sintetica = True, parent_id = null;')
        cr.commit;
        cr.execute('update finan_conta set account_account_id = null;')
        cr.commit;
        cr.execute('update account_account set finan_conta_id = null;')
        cr.commit;
        cr.execute('delete from account_account where finan_conta_id is null;')
        cr.commit;

        for linha in arq.readlines():
            linha = linha.decode('utf-8')
            linha = linha.replace('\n', '')
            linha = linha.replace('\r', '')
            codigo_completo, nome = linha.split('|')

            conta_ids = conta_pool.search(cr, uid, [('codigo_completo', '=', codigo_completo)])

            dados = {
                'codigo_completo': codigo_completo,
                'nome': nome,
                'sintetica': True,
                'tipo': 'O',
                'exige_centro_custo': False,
            }

            if conta_ids:
                conta_pool.write(cr, uid, conta_ids, dados)
            else:
                conta_pool.create(cr, uid, dados)

        arq.close()
        cr.commit()

        cr.execute('update finan_conta set sintetica = False, parent_id = null;')
        cr.commit;

        conta_ids = conta_pool.search(cr, uid, [(1, '=', 1)], order='codigo_completo')

        for conta_obj in conta_pool.browse(cr, uid, conta_ids):
            codigo_completo = conta_obj.codigo_completo

            if '.' not in codigo_completo:
                sql = 'update finan_conta set sintetica = True where id = {id};'
                sql = sql.format(id=conta_obj.id)
                cr.execute(sql)
                continue

            grupos = codigo_completo.split('.')[:-1]
            codigo_pai = '.'.join(grupos)
            conta_pai_ids = conta_pool.search(cr, uid, [['codigo_completo', '=', codigo_pai]])

            if conta_pai_ids:
                sql = 'update finan_conta set parent_id = {pai_id} where id = {id};'
                sql = sql.format(pai_id=conta_pai_ids[0], id=conta_obj.id)
                cr.execute(sql)

            if len(conta_obj.contas_filhas_ids):
                sql = 'update finan_conta set sintetica = True where id = {id};'
                sql = sql.format(id=conta_obj.id)
                cr.execute(sql)


finan_conta()


###class account_account(osv.Model):
    ###_name = 'account.account'
    ###_inherit = 'account.account'
    ###_rec_name = 'nome_completo'

    ###def _busca_conta(self, cr, uid, ids, nome_campo, args=None, context={}):
        ###res = {}

        ###conta_pool = self.pool.get('finan.conta')

        ###for conta_obj in self.browse(cr, uid, ids):
            ###res[conta_obj.id] = False

            ###conta_ids = conta_pool.search(cr, uid, [('account_account_id', '=', conta_obj.id)])

            ###if conta_ids:
                ###res[conta_obj.id] = conta_ids[0]

        ###return res

    ###_columns = {
        ###'finan_conta_id': fields.function(_busca_conta, type='many2one', relation='finan.conta', store=True, method=True, select=True, string=u'Conta financeira'),
        ###'nome_completo': fields.related('finan_conta_id', 'nome_completo', type='char', store=True, select=True),
        ###'nome': fields.related('finan_conta_id', 'nome', type='char', store=True, select=True),
        ###'codigo': fields.related('finan_conta_id', 'codigo', type='char', store=True, select=True),
        ###'codigo_completo': fields.related('finan_conta_id', 'codigo_completo', type='char', store=True, select=True),
        ###'tipo': fields.related('finan_conta_id', 'tipo', type='char', store=True, select=True),
        ###'sintetica': fields.related('finan_conta_id', 'sintetica', type='boolean', store=True, select=True),
    ###}


###account_account()
