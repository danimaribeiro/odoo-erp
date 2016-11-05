# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from random import randint

#FILTRO_DATA = [
    #('data_quitacao', u'Data de quitação'),
    #('data_vencimento', u'Data de vencimento'),
    #('data_documento', u'Data do documento/emissão'),
    #('data', u'Data de conciliação'),
#]

OPCOES_CAIXA = [
     ('1', 'Realizado'), #data quitação
     ('2', 'Comprometido(realizado + realizar)'),
     ('3', 'A realizar'), #data vencimento
]

CAMPOS = [
    ['valor_documento', u'Valor do documento'],
    #['valor_desconto', u'Valor do desconto (global)'],
    #['valor_juros_multa', u'Valor de juros/multa (global)'],
    #['valor', u'Valor líquido'],
    ['valor_desconto_recebido', u'Valor do desconto (recebido de forn.)'],
    ['valor_juros_multa_recebido', u'Valor de juros/multa (recebido)'],
    ['valor_desconto_pago', u'Valor do desconto (concedido a cli.)'],
    ['valor_juros_multa_pago', u'Valor de juros/multa (pago)'],
]


class econo_conta(orm.Model):
    _name = 'econo.conta'
    _description = u'Conta Econômica'
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
            cr.execute('select max(codigo) from econo_conta where parent_id = ' + str(conta_obj.parent_id.id) + ';')
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
            elif nome_campo == 'filtro_contract_ids':
                lista = conta_obj.contract_ids
            elif nome_campo == 'filtro_contract_exclui_ids':
                lista = conta_obj.contract_exclui_ids

            filtro = '|'

            for item_obj in lista:
                filtro += str(item_obj.id) + '|'

            res[conta_obj.id] = filtro

        return res

    _columns = {
        'nome': fields.char(u'Nome', size=64, required=True, select=True),
        'codigo': fields.integer(u'Conta reduzida', select=True, required=False),
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Descrição', fnct_search=_procura_nome, store=True, select=True),
        'codigo_completo': fields.char(u'Código completo', size=64, select=True),
        'parent_id': fields.many2one('econo.conta', u'Conta pai', select=True, ondelete='cascade'),
        'contas_filhas_ids': fields.one2many('econo.conta', 'parent_id', string=u'Contas filhas'),
        'sintetica': fields.boolean(u'Sintética', select=True),
        'parent_left': fields.integer(u'Conta à esquerda', select=1),
        'parent_right': fields.integer(u'Conta a direita', select=1),
        'company_ids': fields.many2many('res.company', 'econo_conta_company', 'conta_id', 'company_id', u'Empresas'),
        'conta_ids': fields.many2many('finan.conta', 'econo_conta_finan_conta', 'conta_id', 'finan_conta_id', u'Contas financeiras'),
        'centrocusto_ids': fields.many2many('finan.centrocusto', 'econo_conta_centrocusto', 'conta_id', 'centrocusto_id', u'Centros de custo'),
        'contract_ids': fields.many2many('hr.contract', 'econo_conta_contract', 'conta_id', 'contract_id', u'Funcionários'),
        'contract_exclui_ids': fields.many2many('hr.contract', 'econo_conta_contract_exclui', 'conta_id', 'contract_id', u'Funcionários excluídos'),
        #'filtro_data': fields.selection(FILTRO_DATA, u'Tipo de data'),
        'opcoes_caixa': fields.selection(OPCOES_CAIXA, u'Opções de caixa'),
        'campo': fields.selection(CAMPOS, u'Campo a acumular'),

        'forca_gravacao': fields.integer(u'Força gravação do filtro'),

        'copia_padrao_id': fields.many2one('econo.conta', u'Conta de configuração padrão'),

        'filtro_company_ids': fields.function(_get_filtro, type='text', string=u'Filtro empresas', store=True, select=True),
        'filtro_conta_ids': fields.function(_get_filtro, type='text', string=u'Filtro contas', store=True, select=True),
        'filtro_centrocusto_ids': fields.function(_get_filtro, type='text', string=u'Filtro centros de custo', store=True, select=True),
        'filtro_contract_ids': fields.function(_get_filtro, type='text', string=u'Filtro funcionários', store=True, select=True),
        'filtro_contract_exclui_ids': fields.function(_get_filtro, type='text', string=u'Filtro funcionários excluídos', store=True, select=True),

        'resumida': fields.boolean(u'Resumida?'),
        'resumida_soma': fields.many2many('econo.conta', 'econo_conta_soma', 'conta_id', 'conta_soma_id', u'Contas a somar'),
        'resumida_subtrai': fields.many2many('econo.conta', 'econo_conta_subtrai', 'conta_id', 'conta_subtrai_id', u'Contas a subtrair'),
    }

    _defaults = {
        'sintetica': False,
        #'filtro_data': 'data_quitacao',
        'opcoes_caixa': '1',
        'campo': 'valor_documento',
    }

    _sql_constraints = [
        ('codigo_completo_unique', 'unique(codigo_completo)',
            u'O código não pode se repetir!'),
    ]

    def _verifica_recursiva(self, cr, uid, ids, context={}):
        nivel_recursao = 100

        while len(ids):
            cr.execute('select distinct parent_id from econo_conta where id in %s', (tuple(ids),))

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

        #tipo = 'O'
        #if 'tipo' in vals:
            #tipo = vals['tipo']
        #elif conta_obj:
            #tipo = getattr(conta_obj, 'tipo', 'O')

        #receita = tipo == TIPO_CONTA_RECEITA
        #despesa = tipo == TIPO_CONTA_DESPESA

        if (not sintetica) and (not parent_obj):
            if conta_obj:
                raise osv.except_osv((u'Inválido !'), (u'Conta analítica %s deve ter obrigatoriamente uma conta pai.' % conta_obj.codigo_completo))

            else:
                raise osv.except_osv((u'Inválido !'), (u'Conta analítica deve ter obrigatoriamente uma conta pai.'))

        ##if parent_obj:
            ##if parent_obj.tipo != tipo and parent_obj.tipo != 'O':
                ##tipo_desc = TIPO_CONTA_DIC[tipo]
                ##tipo_desc_pai = TIPO_CONTA_DIC[parent_obj.tipo]
                ##raise osv.except_osv(u'Inválido !', u'Conta de {tipo_desc} não pode ter uma conta pai de {tipo_desc_pai}.'.format(tipo_desc=tipo_desc, tipo_desc_pai=tipo_desc_pai))

        return True

    def create(self, cr, uid, vals, context={}):
        self.valida_contas(cr, uid, [], vals)

        res = super(econo_conta, self).create(cr, uid, vals, context)

        return res

    def write(self, cr, uid, ids, vals, context={}):
        self.valida_contas(cr, uid, ids, vals)

        vals['forca_gravacao'] = randint(0, 100)

        res = super(econo_conta, self).write(cr, uid, ids, vals, context=context)

        if not context.get('nao_replica', False):
            self.ajusta_copia_padrao(cr, uid, ids, context=context)

        return res

    def ajusta_copia_padrao(self, cr, uid, ids, context={}):
        conta_pool = self.pool.get('econo.conta')

        for padrao_obj in conta_pool.browse(cr, uid, ids):
            #
            # Busca as contas relacionadas no padrão
            #
            conta_ids = conta_pool.search(cr, uid, [('copia_padrao_id', '=', padrao_obj.id)])

            if len(conta_ids):
                valores = {}

                cc_ids = []
                for cc_obj in padrao_obj.centrocusto_ids:
                    cc_ids.append(cc_obj.id)

                valores['centrocusto_ids'] = cc_ids

                c_ids = []
                for c_obj in padrao_obj.contract_ids:
                    c_ids.append(c_obj.id)

                valores['contract_ids'] = c_ids

                ce_ids = []
                for ce_obj in padrao_obj.contract_exclui_ids:
                    ce_ids.append(ce_obj.id)

                valores['contract_exclui_ids'] = ce_ids

                for replica_id in conta_ids:
                    conta_pool.write(cr, uid, [replica_id], valores, context={'nao_replica': True})

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
        #valores['tipo'] = pai_obj.tipo

        return res

    def onchange_copia_padrao_id(self, cr, uid, ids, copia_padrao_id, centrocusto_ids, contract_ids, contract_exclui_ids, context={}):
        if not copia_padrao_id:
            return {}

        conta_pool = self.pool.get('econo.conta')
        padrao_obj = conta_pool.browse(cr, uid, copia_padrao_id)

        res = {}
        valores = {}
        res['value'] = valores

        cc_ids = []
        for cc_obj in padrao_obj.centrocusto_ids:
            cc_ids.append(cc_obj.id)

        if not len(cc_ids):
            valores['centrocusto_ids'] = [[6, False, []]]
        else:
            valores['centrocusto_ids'] = [[6, False, cc_ids]]

        c_ids = []
        for c_obj in padrao_obj.contract_ids:
            c_ids.append(c_obj.id)

        if not len(c_ids):
            valores['contract_ids'] = [[6, False, []]]
        else:
            valores['contract_ids'] = [[6, False, c_ids]]

        ce_ids = []
        for ce_obj in padrao_obj.contract_exclui_ids:
            ce_ids.append(ce_obj.id)

        if not len(ce_ids):
            valores['contract_exclui_ids'] = [[6, False, []]]
        else:
            valores['contract_exclui_ids'] = [[6, False, ce_ids]]

        return res

    def apropria_conta(self, cr, uid, ids, context={}):
        cr.execute('delete from finan_rateio_economico_bi;') # where econo_conta_id = ' + str(conta_obj.id) + ';')

        for conta_obj in self.browse(cr, uid, ids, context=context):
            if conta_obj.codigo_completo not in [
                '2.2.01.01',
                '2.2.02.01',
                '2.2.02.30',
                '2.2.03.01',
                '2.2.05.01',
                '2.2.06.01',
                '2.2.07.01',
                '2.3.02.02',
                '4.4.01.01',
                '4.4.01.08',
                '4.4.01.18',
                '4.4.01.28',
                '4.4.02.01',
                '4.4.02.11',
                '4.4.02.22',
                '4.4.03.01',
                '4.4.03.11',
                '4.4.03.21',
                '4.4.02.04',
                ]:
                continue

            if conta_obj.sintetica:
                continue

            vai_fazer = False
            vai_fazer = vai_fazer or len(conta_obj.company_ids) > 0
            vai_fazer = vai_fazer or len(conta_obj.conta_ids) > 0
            vai_fazer = vai_fazer or len(conta_obj.centrocusto_ids) > 0
            vai_fazer = vai_fazer or len(conta_obj.contract_ids) > 0

            if not vai_fazer:
                continue

            sql = '''
                select
                    pr.id as pr_id,
                    pr.lancamento_id,
                    pr.tipo,
                    pr.data_quitacao,
                    pr.data_vencimento,
                    pr.company_id,
                    pr.conta_id,
                    pr.centrocusto_id,
                    pr.hr_contract_id,
                    pr.porcentagem,
                    pr.valor_documento,
                        CASE
                            WHEN pr.tipo = 'P' OR pr.tipo = 'S' OR pr.tipo = 'PP' OR pr.tipo = 'LP' THEN pr.valor * -1
                            ELSE pr.valor
                        END AS valor,
                    pr.valor_original,
                    pr.valor_documento_original,
                    pr.saldo_original,
                    c.parent_id AS grupo_id

                from
                    finan_pagamento_rateio_folha pr
                    join res_company c on c.id = pr.company_id
            '''

            #where = "pr.data_quitacao is not null"
            where = "pr.data_quitacao is not null and pr.data_quitacao between '2015-01-01' and '2015-01-31' and pr.tipo = 'S'"

            if len(conta_obj.company_ids):
                if len(where):
                    where += ' and '

                where += '('
                for f_obj in conta_obj.company_ids:
                    were += 'or pr.company_id = ' + str(f_obj.id) + ' '
                where = where.replace('(or', '(')
                where += ')'

            if len(conta_obj.conta_ids):
                if len(where):
                    where += ' and '

                where += '('
                for f_obj in conta_obj.conta_ids:
                    where += 'or pr.conta_id = ' + str(f_obj.id) + ' '
                where = where.replace('(or', '(')
                where += ')'

            if len(conta_obj.centrocusto_ids):
                if len(where):
                    where += ' and '

                where += '('
                for f_obj in conta_obj.centrocusto_ids:
                    where += 'or pr.centrocusto_id = ' + str(f_obj.id) + ' '
                where = where.replace('(or', '(')
                where += ')'

            if len(conta_obj.contract_ids):
                if len(where):
                    where += ' and '

                where += '('
                for f_obj in conta_obj.contract_ids:
                    where += 'or pr.hr_contract_id = ' + str(f_obj.id) + ' '
                where = where.replace('(or', '(')
                where += ')'

            if len(conta_obj.contract_exclui_ids):
                if len(where):
                    where += ' and '

                where += '('
                for f_obj in conta_obj.contract_ids:
                    where += 'and pr.hr_contract_id != ' + str(f_obj.id) + ' '
                where = where.replace('(and', '(')
                where += ')'

            if len(where):
                sql += ' where ' + where

            #print(sql)

            cr.execute(sql)
            dados = cr.fetchall()

            for pr_id, lancamento_id, tipo, data_quitacao, data_vencimento, company_id, conta_id, centrocusto_id, hr_contract_id, porcentagem, valor_documento, valor, valor_original, valor_documento_original, saldo_original, grupo_id in dados:
                if pr_id > 0:
                    apro_dados = {
                        'econo_conta_id': conta_obj.id,
                        'rateio_id': pr_id,
                        'lancamento_id': lancamento_id,
                        'tipo': tipo,
                        'data_quitacao': data_quitacao,
                        'data_vencimento': data_vencimento,
                        'company_id': company_id,
                        'conta_id': conta_id,
                        'centrocusto_id': centrocusto_id,
                        'hr_contract_id': hr_contract_id,
                        'porcentagem': porcentagem,
                        'valor_documento': valor_documento,
                        'valor': valor,
                        'valor_original': valor_original,
                        'valor_documento_original': valor_documento_original,
                        'saldo_original': saldo_original,
                        'grupo_id': grupo_id,
                    }
                else:
                    apro_dados = {
                        'econo_conta_id': conta_obj.id,
                        'rateio_id': False,
                        'lancamento_id': lancamento_id,
                        'tipo': tipo,
                        'data_quitacao': data_quitacao,
                        'data_vencimento': data_vencimento,
                        'company_id': company_id,
                        'conta_id': conta_id,
                        'centrocusto_id': centrocusto_id,
                        'hr_contract_id': hr_contract_id,
                        'porcentagem': porcentagem,
                        'valor_documento': valor_documento,
                        'valor': valor,
                        'valor_original': valor_original,
                        'valor_documento_original': valor_documento_original,
                        'saldo_original': saldo_original,
                        'grupo_id': grupo_id,
                    }
                self.pool.get('finan.rateio.economico.bi').create(cr, uid, apro_dados)

        #
        # Agora, pega os itens do rateio que não foram apropriados em lugar
        # nenhum
        #
        sql = '''
            select
                pr.id as pr_id,
                pr.lancamento_id,
                pr.tipo,
                pr.data_quitacao,
                pr.data_vencimento,
                pr.company_id,
                pr.conta_id,
                pr.centrocusto_id,
                pr.hr_contract_id,
                pr.porcentagem,
                pr.valor_documento,
                    CASE
                        WHEN pr.tipo = 'P' OR pr.tipo = 'S' OR pr.tipo = 'PP' OR pr.tipo = 'LP' THEN pr.valor * -1
                        ELSE pr.valor
                    END AS valor,
                pr.valor_original,
                pr.valor_documento_original,
                pr.saldo_original,
                c.parent_id AS grupo_id

            from
                finan_pagamento_rateio_folha pr
                join res_company c on c.id = pr.company_id
                left join finan_rateio_economico_bi bi on (pr.id is not null and bi.rateio_id = pr.id) or (pr.id is null and pr.lancamento_id = bi.lancamento_id)

            where
                pr.data_quitacao is not null
                and bi.id is null
        and pr.data_quitacao between '2015-01-01' and '2015-01-31' and pr.tipo = 'S'
        '''
        cr.execute(sql)
        dados = cr.fetchall()

        for pr_id, lancamento_id, tipo, data_quitacao, data_vencimento, company_id, conta_id, centrocusto_id, hr_contract_id, porcentagem, valor_documento, valor, valor_original, valor_documento_original, saldo_original, grupo_id in dados:
            if pr_id > 0:
                apro_dados = {
                    'econo_conta_id': False,
                    'rateio_id': pr_id,
                    'lancamento_id': lancamento_id,
                    'tipo': tipo,
                    'data_quitacao': data_quitacao,
                    'data_vencimento': data_vencimento,
                    'company_id': company_id,
                    'conta_id': conta_id,
                    'centrocusto_id': centrocusto_id,
                    'hr_contract_id': hr_contract_id,
                    'porcentagem': porcentagem,
                    'valor_documento': valor_documento,
                    'valor': valor,
                    'valor_original': valor_original,
                    'valor_documento_original': valor_documento_original,
                    'saldo_original': saldo_original,
                    'grupo_id': grupo_id,
                }
            else:
                apro_dados = {
                    'econo_conta_id': False,
                    'rateio_id': False,
                    'lancamento_id': lancamento_id,
                    'tipo': tipo,
                    'data_quitacao': data_quitacao,
                    'data_vencimento': data_vencimento,
                    'company_id': company_id,
                    'conta_id': conta_id,
                    'centrocusto_id': centrocusto_id,
                    'hr_contract_id': hr_contract_id,
                    'porcentagem': porcentagem,
                    'valor_documento': valor_documento,
                    'valor': valor,
                    'valor_original': valor_original,
                    'valor_documento_original': valor_documento_original,
                    'saldo_original': saldo_original,
                    'grupo_id': grupo_id,
                }
            self.pool.get('finan.rateio.economico.bi').create(cr, uid, apro_dados)

    def apropria_todas(self, cr, uid, ids, context={}):
        ids = self.pool.get('econo.conta').search(cr, uid, [])
        self.apropria_conta(cr, uid, ids, context=context)


econo_conta()
