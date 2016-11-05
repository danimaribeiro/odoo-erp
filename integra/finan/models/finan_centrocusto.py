# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


# from datetime import datetime
from copy import copy
from osv import orm, fields, osv
#from sped.models.fields import CampoPorcentagem
from pybrasil.valor.decimal import Decimal as D


TIPO = (
    ('C', 'Centro de custo'),
    ('R', 'Rateio por centro de custo'),
)

TIPO_CONTA = (
    ('D', u'Despesa'),
    ('C', u'Custo'),
)


class CampoPorcentagem(fields.float):
    def __init__(self, *args, **kwargs):
        kwargs['digits'] = (5, 2)
        super(CampoPorcentagem, self).__init__(*args, **kwargs)

class finan_centrocusto(orm.Model):
    _description = u'Centro de custo'
    _name = 'finan.centrocusto'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'codigo, nome'
    _order = 'parent_left'
    _rec_name = 'nome_completo'

    def monta_nome(self, cr, uid, id):
        conta_obj = self.browse(cr, uid, id)

        nome = conta_obj.nome

        if conta_obj.parent_id:
            nome = self.monta_nome(cr, uid, conta_obj.parent_id.id) + ' / ' + nome

        return nome

    def nome_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for id in ids:
            res.append((id, self.monta_nome(cr, uid, id)))

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.nome_get(cr, uid, ids, context=context)
        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

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
            cr.execute("select max(codigo) from finan_centrocusto where tipo = 'C' and parent_id = " + str(conta_obj.parent_id.id) + ';')
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

    _columns = {
        'nome': fields.char(u'Descrição', size=60, required=True, select=True),
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Nome', fnct_search=_procura_nome, store=True),
        'tipo': fields.selection(TIPO, u'Tipo'),
        'rateio_ids': fields.one2many('finan.rateio', 'centrocusto_pai_id', u'Itens do rateio'),
        'parent_id': fields.many2one('finan.centrocusto', u'Centro de custo pai', select=True, ondelete='cascade'),
        'centrocusto_filhos_ids': fields.one2many('finan.centrocusto', 'parent_id', string='Centros de custo filhos'),
        'sintetico': fields.boolean(u'Sintético', select=True),
        'parent_left': fields.integer(u'Conta à esquerda', select=1),
        'parent_right': fields.integer(u'Conta a direita', select=1),
        'codigo': fields.integer(u'Código no grupo', select=True),
        'codigo_completo': fields.function(_get_codigo_funcao, type='char', string=u'Código completo', store=True),
        'company_id': fields.many2one('res.company', u'Empresa/unidade'),
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),
        'data': fields.date(u'Data'),           
        'create_date': fields.datetime( u'Data de Criação'),
        'write_date': fields.datetime( u'Data Ultima Alteração'),        
    }

    _defaults = {
        'tipo': 'C',
        'sintetico': False,
        'data': fields.datetime.now,        
    }

    def rateia_valor(self, cr, uid, centrocusto_id, valor):
        centrocusto_obj = self.browse(cr, uid, centrocusto_id)

        valor = D(str(valor))

        if centrocusto_obj.tipo == 'C':
            return {centrocusto_id: valor}

        ret = {}
        soma = D('0')
        ultimo_item = None
        for item in centrocusto_obj.rateio_ids:
            valor_rateado = valor * D(str(item.porcentagem)) / D('100.00')
            valor_rateado = valor_rateado.quantize(D('0.01'))
            ret[item.centrocusto_id.id] = valor_rateado
            soma += valor_rateado
            ultimo_item = item.centrocusto_id.id

        #
        # Ajusta o último item rateado para que o total seja exato
        #
        diferenca = valor - soma
        if ultimo_item:
            ret[ultimo_item] += diferenca

        return ret

    def verifica_porcentagem(self, cr, uid, ids, vals, context=None):
        if 'rateio_ids' not in vals or not vals['rateio_ids']:
            return

        rateios = vals['rateio_ids']
        rateios_alterados = []

        total = D('0')
        for operacao, rateio_id, valores in rateios:
            #
            # Cada lanc_item tem o seguinte formato
            # [operacao, id_original, valores_dos_campos]
            #
            # operacao pode ser:
            # 0 - criar novo registro (no caso aqui, vai ser ignorado)
            # 1 - alterar o registro
            # 2 - excluir o registro (também vai ser ignorado)
            # 3 - desvincula o registro (no caso aqui, seria setar o res_partner_bank_id para outro id)
            # 4 - vincular a um registro existente
            #

            if operacao == 2:
                rateios_alterados += [rateio_id]

            if operacao in [0, 1] and valores and 'porcentagem' in valores:
                if operacao == 1:
                    rateios_alterados += [rateio_id]

                total += D(str(valores['porcentagem']))

        #
        # Ajusta com os possíveis não alterados
        #
        rateio_ids = []
        if ids and ids[0]:
            rateio_ids = self.pool.get('finan.rateio').search(cr, uid, [('centrocusto_pai_id', '=', ids[0]), ('id', 'not in', rateios_alterados)])

            for rateio_obj in self.pool.get('finan.rateio').browse(cr, uid, rateio_ids):
                total += D(str(rateio_obj.porcentagem))

        #if total != D('100'):
            #raise osv.except_osv((u'Inválido !'), (u'A soma das porcentagens deve ser 100%'))

    def _verifica_recursiva(self, cr, uid, ids, context=None):
        nivel_recursao = 100

        while len(ids):
            cr.execute('select distinct parent_id from finan_centrocusto where id in %s', (tuple(ids),))

            ids = filter(None, map(lambda x: x[0], cr.fetchall()))

            if not nivel_recursao:
                return False

            nivel_recursao -= 1

        return True

    _constraints = [
        (_verifica_recursiva, u'Erro! Não é possível criar centros de custo recursivos', ['parent_id'])
    ]

    def create(self, cr, uid, dados, context={}):
        self.verifica_porcentagem(cr, uid, [], dados)

        res = super(finan_centrocusto, self).create(cr, uid, dados, context)

        if 'tipo' in dados and dados['tipo'] == 'C':
            self.pool.get('finan.rateio').create(cr, uid, {'centrocusto_pai_id': res, 'centrocusto_id': res, 'porcentagem': 100})

        return res

    def write(self, cr, uid, ids, dados, context={}):
        self.verifica_porcentagem(cr, uid, ids, dados)

        res = super(finan_centrocusto, self).write(cr, uid, ids, dados, context=context)

        return res

    def unlink(self, cr, uid, ids, context={}):
        for cc_obj in self.pool.get('finan.centrocusto').browse(cr, uid, ids, context=context):
            for rateio_obj in cc_obj.rateio_ids:
                rateio_obj.unlink()

        res = super(finan_centrocusto, self).unlink(cr, uid, ids, context=context)

        return res

    def copy(self, cr, uid, id, default={}, context={}):
        cc_pool = self.pool.get('finan.centrocusto')
        default.update({'centrocusto_filhos_ids': False})

        cc_obj = cc_pool.browse(cr, uid, id, context=context)

        if cc_obj.tipo == 'C':
            default.update({'rateio_ids': False})

        res = super(finan_centrocusto, self).copy(cr, uid, id, default, context=context)

        if cc_obj.tipo == 'C':
            cr.execute("delete from finan_rateio where centrocusto_pai_id = " + str(res) + ";")
            self.pool.get('finan.rateio').create(cr, uid, {'centrocusto_pai_id': res, 'centrocusto_id': res, 'porcentagem': 100})

        return res

    def recalcula_ordem_parent_left_parent_right(self, cr, uid, ids, context):
        for obj in self.browse(cr, uid, self.search(cr, uid, [])):
            self.write(cr, uid, obj.id, {'nome': obj.nome + ' '})

        for obj in self.browse(cr, uid, self.search(cr, uid, [])):
            self.write(cr, uid, obj.id, {'nome': obj.nome.strip()})

    def campos_rateio(self, cr, uid):
        #rateio_pool = self.pool.get('finan.rateio')
        rateio_pool = self.pool.get('finan.lancamento.rateio')
        campos = ['company_id', 'conta_id', 'centrocusto_id']

        for nome_campo in rateio_pool._all_columns:
            coluna = rateio_pool._columns[nome_campo]
            #if isinstance(coluna, fields.many2one) and nome_campo != 'centrocusto_pai_id' and nome_campo not in campos:
            if isinstance(coluna, fields.many2one) and nome_campo != 'lancamento_id' and nome_campo not in campos:
                campos.append(nome_campo)

        return campos

    def _realiza_rateio(self, valor, porcentagem, campos, padrao, rateio):
        r = rateio

        for campo in campos:
            chave = padrao.get(campo, False)

            if isinstance(chave, (list, tuple)):
                chave = chave[1][False]

            if chave not in r:
                if campo == campos[-1]:
                    r[chave] = D(0)

                else:
                    r[chave] = {}

            if isinstance(r, dict) and campo != campos[-1]:
                r = r[chave]

        vr = D(valor) * D(porcentagem) / D(100)
        vr = vr.quantize(D('0.01'))
        r[chave] += vr
        return vr

    def monta_dados(self, rateio, campos=[], nivel=0, dados={}, lista_dados=[], valor=0, forcar_valor=0):
        for id in rateio:
            dados[campos[nivel]] = id

            if isinstance(rateio[id], dict):
                self.monta_dados(rateio[id], campos, nivel=nivel+1, dados=dados, lista_dados=lista_dados)

            else:
                dados['valor_documento'] = rateio[id]

            if nivel == len(campos) - 1:
                lista_dados.append(copy(dados))

        #
        # Ajusta as porcentagens e valores conforme o valor total informado
        #
        if valor > 0:
            total_valor = 0
            total_porcentagem = 0
            maior_valor = 0
            rateio_maior_valor = None
            for d in lista_dados:
                vr_doc = D(d['valor_documento'])
                porcentagem = vr_doc / D(valor) * D(100)
                porcentagem = porcentagem.quantize(D('0.01'))
                d['porcentagem'] = porcentagem
                total_porcentagem += porcentagem

                if forcar_valor:
                    vr_doc = D(forcar_valor) * porcentagem / D(100)
                    vr_doc = vr_doc.quantize(D('0.01'))
                    d['valor_documento'] = vr_doc

                total_valor += vr_doc

                if vr_doc > maior_valor:
                    maior_valor = vr_doc
                    rateio_maior_valor = d

            #
            # Ajusta a diferença de centavos no maior valor rateado
            #
            if rateio_maior_valor:
                if forcar_valor:
                    rateio_maior_valor['valor_documento'] += forcar_valor - total_valor

                else:
                    rateio_maior_valor['valor_documento'] += valor - total_valor

                rateio_maior_valor['porcentagem'] += 100 - total_porcentagem

        #print(lista_dados)
        return lista_dados

    def ajusta_valor_padrao(self, padrao, rateio_obj):
        #
        # Para os casos em que a escolha do valor padrão
        # depende de um outro campo estabelecido no rateio.
        # Esses casos são especificados assim:
        # ['campo_teste', {campo_teste_valor: padrao, campo_teste_valor: padrao...}]
        #
        for campo in padrao:
            if isinstance(padrao[campo], (list, tuple)):
                campo_teste = padrao[campo][0]
                campo_teste_valor = getattr(rateio_obj, campo_teste, False)
                if campo_teste_valor in padrao[campo][1]:
                    novo_valor = padrao[campo][1][campo_teste_valor]
                else:
                    novo_valor = False

                padrao[campo] = novo_valor

        return padrao

    def realiza_rateio(self, cr, uid, ids, context={}, valor=0, campos=[], padrao={}, rateio={}, tabela_pool=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        if len(ids) and not ids[0]:
            ids[0] = self.pool.get('finan.centrocusto').search(cr, uid, [('codigo', '=', '99999')])[0]

        conta_pool = self.pool.get('finan.conta')

        if not campos:
            campos = self.campos_rateio(cr, uid)

        if tabela_pool is None:
            tabela_pool = self.pool.get('finan.centrocusto')

        for cc_obj in tabela_pool.browse(cr, uid, ids):
            p = copy(padrao)
            if hasattr(cc_obj, 'tipo') and cc_obj.tipo == 'C':
                if cc_obj.id > 0:
                    p['centrocusto_id'] = cc_obj.id
                self._realiza_rateio(valor, 100, campos, p, rateio)

            else:
                dif = 0
                for r_obj in cc_obj.rateio_ids:
                    for campo in campos:
                        if getattr(r_obj, campo, False):
                            p[campo] = getattr(r_obj, campo, False).id

                        #
                        # Ajusta as contas de custo e despesa de acordo com o rateio
                        #
                        if campo == 'conta_id' and p['conta_id']:
                            conta_obj = conta_pool.browse(cr, 1, p['conta_id'])
                            if hasattr(r_obj, 'tipo_conta'):
                                if r_obj.tipo_conta and r_obj.tipo_conta == 'C' and conta_obj.tipo == 'D':
                                    if conta_obj.conta_complementar_custo_id:
                                        p['conta_id'] = conta_obj.conta_complementar_custo_id.id
                                elif r_obj.tipo_conta and r_obj.tipo_conta == 'D' and conta_obj.tipo == 'C':
                                    if conta_obj.conta_complementar_despesa_id:
                                        p['conta_id'] = conta_obj.conta_complementar_despesa_id.id

                        p = self.ajusta_valor_padrao(p, r_obj)

                    dif += self._realiza_rateio(valor, r_obj.porcentagem, campos, p, rateio)

                if dif != valor:
                    self._realiza_rateio(valor - dif, 100, campos, p, rateio)

        return rateio


finan_centrocusto()


class finan_rateio(orm.Model):
    _description = u'Rateio entre centros de custo'
    _name = 'finan.rateio'

    _columns = {
        'centrocusto_pai_id': fields.many2one('finan.centrocusto', u'Centro de custo pai', ondelete='cascade', select=True),
        'company_id': fields.many2one('res.company', u'Empresa/Unidade de negócio', select=True, ondelete='restrict'),
        'tipo_conta': fields.selection(TIPO_CONTA, u'Tipo', select=True),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira', select=True, ondelete='restrict'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', domain=[('tipo', '=', 'C')], select=True, ondelete='restrict'),
        'porcentagem': CampoPorcentagem(u'Porcentagem'),
    }

    _defaults = {
        'tipo_conta': 'D',
    }

    #_sql_constraints = [
        #('rateio_centrocusto_unique', 'unique(centrocusto_pai_id, centrocusto_id, company_id, conta_id)',
            #u'Não é permitido repetir um mesmo centro de custo!'),
    #]


finan_rateio()
