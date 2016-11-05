# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class sped_servico(orm.Model):
    _description = u'sped_servico'
    _name = 'sped.servico'

    def monta_nome(self, cr, uid, id):
        servico_obj = self.browse(cr, uid, id)

        nome = servico_obj.codigo[:2] + '.' + servico_obj.codigo[2:] + ' - ' + servico_obj.descricao

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
            ('codigo', 'ilike', texto),
            ('descricao', 'ilike', texto)
        ]

        return procura

    _columns = {
        'codigo': fields.char(u'Código', size=4, required=True),
        'descricao': fields.char(u'Descrição', size=400, required=True),
        'al_ibpt_nacional': fields.float(u'Alíquota do IBPT'),
        'al_ibpt_internacional': fields.float(u'Alíquota do IBPT internacional'),
        'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', fnct_search=_procura_nome, store=False),
        'codigo_servico_municipio': fields.char(u'Código Serviço do Municipío', size=9),
    }

    _rec_name = 'nome'
    _order = 'codigo'

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', u'O código não pode se repetir!'),
    ]

    def atualiza_ibpt(self, cr, uid, ids, context):
        from pybrasil.ncm import SERVICOS_CODIGO

        for codigo in SERVICOS_CODIGO:
            servico = SERVICOS_CODIGO[codigo]
            print(codigo, servico)

            servico_id = self.search(cr, uid, [('codigo', '=', codigo.zfill(4))])

            dados = {
                'al_ibpt_nacional': servico.al_ibpt_nacional,
                'al_ibpt_internacional': servico.al_ibpt_internacional,
            }

            if len(servico_id):
                self.write(cr, uid, servico_id, dados)

            else:
                #
                # Vamos criar
                #
                dados['codigo'] = codigo.zfill(4)
                dados['descricao'] = servico.descricao[:400]
                self.create(cr, uid, dados)


sped_servico()
