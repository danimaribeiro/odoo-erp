# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields, osv
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.data import parse_datetime, formata_data, agora, hoje
from pybrasil.valor import formata_valor
import base64
import os
from finan.wizard.relatorio import *
from pybrasil.valor.decimal import Decimal as D


NIVEL = [
    ('1', u'1'),
    ('2', u'2'),
    ('3', u'3'),
    ('4', u'4'),
]

ESTRUTURA = [    
    ('DREG', u'Demonstração do Resultado do Exercício Gerencial'),    
]


class finan_estrutura_demonstrativo(osv.Model):
    _name = 'finan.estrutura.demonstrativo'
    _description = u'Estrutura dos Demonstrativos Gerencial'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'codigo_completo'
    _order = 'parent_left'
    _rec_name = 'nome_completo'

    def monta_nome(self, cr, uid, id):
        conta_obj = self.browse(cr, uid, id)

        nome = conta_obj.nome

        if conta_obj.parent_id:
            nome = self.monta_nome(cr, uid, conta_obj.parent_id.id) + u' / ' + nome

        return nome

    def nome_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for obj in self.browse(cr, uid, ids):
            res.append((obj.id, obj.codigo_completo + ' - ' + self.monta_nome(cr, uid, obj.id)))

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
                ('codigo_completo', 'ilike', texto)
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
            cr.execute('select max(codigo) from finan_estrutura_demonstrativo where parent_id = ' + str(conta_obj.parent_id.id) + ';')
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

    def _get_filtro(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for conta_obj in self.browse(cr, uid, ids):
            if nome_campo == 'filtro_conta_ids':
                lista = conta_obj.conta_ids
            elif nome_campo == 'filtro_company_ids':
                lista = conta_obj.company_ids
            elif nome_campo == 'filtro_centrocusto_ids':
                lista = conta_obj.centrocusto_ids
            elif nome_campo == 'filtro_department_ids':
                lista = conta_obj.hr_department_ids
            elif nome_campo == 'filtro_partner_category_ids':
                lista = conta_obj.partner_category_ids

            filtro = '|'

            for item_obj in lista:
                filtro += str(item_obj.id) + '|'

            res[conta_obj.id] = filtro

        return res

    _columns = {
        'tipo_demonstrativo': fields.selection(ESTRUTURA, u'Tipo de demonstrativo'),
        'gerencial': fields.boolean(u'Demonstrativo gerencial?'),
        'nivel_estrutura': fields.selection(NIVEL, u'Nível'),
        'nome': fields.char(u'Nome', size=64, required=True, select=True),
        'codigo': fields.integer(u'Conta reduzida', select=True, required=False),
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Descrição', fnct_search=_procura_nome, store=True, select=True),
        'codigo_completo': fields.char(u'Código completo', size=64, select=True),
        'parent_id': fields.many2one('finan.estrutura.demonstrativo', u'Conta pai', select=True, ondelete='cascade'),
        'contas_filhas_ids': fields.one2many('finan.estrutura.demonstrativo', 'parent_id', string=u'Contas filhas'),
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_date': fields.datetime( u'Data Alteração'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),

        'sintetica': fields.boolean(u'Sintética', select=True),
        'parent_left': fields.integer(u'Conta à esquerda', select=1),
        'parent_right': fields.integer(u'Conta a direita', select=1),
        'company_ids': fields.many2many('res.company', 'finan_estrutura_demonstrativo_company', 'estrutura_id', 'company_id', u'Empresas'),
        'conta_ids': fields.many2many('finan.conta', 'finan_estrutura_demonstrativo_finan_conta', 'estrutura_id', 'finan_conta_id', u'Contas financeiras'),
        'centrocusto_ids': fields.many2many('finan.centrocusto', 'finan_estrutura_demonstrativo_centrocusto', 'estrutura_id', 'centrocusto_id', u'Centros de custo'),
        'hr_department_ids': fields.many2many('hr.department', 'finan_estrutura_demonstrativo_departamento', 'estrutura_id', 'department_id', u'Departamentos/postos'),
        'partner_category_ids': fields.many2many('res.partner.category', 'finan_estrutura_demonstrativo_categoria_cliente', 'estrutura_id', 'categoria_id', u'Categorias de clientes'),

        'filtro_company_ids': fields.function(_get_filtro, type='text', string=u'Filtro empresas', store=True, select=True),
        'filtro_conta_ids': fields.function(_get_filtro, type='text', string=u'Filtro contas', store=True, select=True),
        'filtro_centrocusto_ids': fields.function(_get_filtro, type='text', string=u'Filtro centros de custo', store=True, select=True),
        'filtro_department_ids': fields.function(_get_filtro, type='text', string=u'Filtro departamentos', store=True, select=True),
        'filtro_partner_category_ids': fields.function(_get_filtro, type='text', string=u'Filtro categorias', store=True, select=True),

        'resumida': fields.boolean(u'Resumida?'),
        'resumida_soma': fields.many2many('finan.estrutura.demonstrativo', 'finan_estrutura_demonstrativo_soma', 'estrutura_id', 'conta_soma_id', u'Contas a somar'),
        'resumida_subtrai': fields.many2many('finan.estrutura.demonstrativo', 'finan_estrutura_demonstrativo_subtrai', 'estrutura_id', 'conta_subtrai_id', u'Contas a subtrair'),
    }

    _defaults = {
        'sintetica': False,
        'nivel_estrutura': '1',
    }

    _sql_constraints = [
        ('codigo_completo_unique', 'unique(codigo_completo)',
            u'O código não pode se repetir!'),
    ]

    def _verifica_recursiva(self, cr, uid, ids, context={}):
        nivel_recursao = 100

        while len(ids):
            cr.execute('select distinct parent_id from finan_estrutura_demonstrativo where id in %s', (tuple(ids),))

            ids = filter(None, map(lambda x: x[0], cr.fetchall()))

            if not nivel_recursao:
                return False

            nivel_recursao -= 1

        return True

    #def _verifica_grupos(self, cr, uid, ids, context={}):

        #for conta_obj in self.browse(cr, uid, ids):
            #if conta_obj.parent_id:
                #conta_pai = conta_obj.parent_id.codigo_completo

                #if not conta_obj.codigo_completo.startswith(conta_pai + '.'):
                    #return False

                #codigo = conta_obj.codigo_completo.replace(conta_pai + '.', '')

                #if '.' in codigo:
                    #return False

        #return True

    _constraints = [
        (_verifica_recursiva, u'Erro! Não é possível criar contas recursivas', ['parent_id']),
        #(_verifica_grupos, u'Erro! O código da conta deve conter o código da conta pai', ['codigo_completo'])
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

        if (not sintetica) and (not parent_obj):
            if conta_obj:
                raise osv.except_osv((u'Inválido !'), (u'Conta analítica %s deve ter obrigatoriamente uma conta pai.' % conta_obj.codigo_completo))

            else:
                raise osv.except_osv((u'Inválido !'), (u'Conta analítica deve ter obrigatoriamente uma conta pai.'))

        return True

    def create(self, cr, uid, vals, context={}):
        self.valida_contas(cr, uid, [], vals)

        res = super(finan_estrutura_demonstrativo, self).create(cr, uid, vals, context)

        return res

    def write(self, cr, uid, ids, vals, context={}):
        self.valida_contas(cr, uid, ids, vals)

        res = super(finan_estrutura_demonstrativo, self).write(cr, uid, ids, vals, context=context)
        return res
    
    def onchange_parent_id(self, cr, uid, ids, parent_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not parent_id:
            return res

        pai_obj = self.browse(cr, uid, parent_id)
        valores['codigo_completo'] = pai_obj.codigo_completo + '.'
        #valores['tipo'] = pai_obj.tipo

        return res
   
finan_estrutura_demonstrativo()

