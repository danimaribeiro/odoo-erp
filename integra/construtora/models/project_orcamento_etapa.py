# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class project_orcamento_etapa(osv.Model):
    _name = 'project.orcamento.etapa'
    _description = u'Etapas do orçamento do projeto'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'orcamento_id, codigo_completo'
    _order = 'parent_left'
    _rec_name = 'nome_completo'

    def monta_nome(self, cr, uid, id):
        etapa_obj = self.browse(cr, uid, id)

        #nome = etapa_obj.nome
        if etapa_obj.etapa_id and etapa_obj.etapa_id.nome:
            nome = etapa_obj.etapa_id.nome
        else:
            nome = ''

        if etapa_obj.parent_id:
            nome = self.monta_nome(cr, uid, etapa_obj.parent_id.id) + u' / ' + nome

        return nome

    def nome_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for obj in self.browse(cr, uid, ids):
            nome = obj.codigo_completo or ''
            nome += ' - '
            nome += self.monta_nome(cr, uid, obj.id) or ''
            res.append((obj.id, nome))

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.nome_get(cr, uid, ids, context=context)
        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        codigo = 0
        try:
            codigo = int(texto)
        except:
            pass

        if codigo:
            procura = [
                '|', '|',
                ('nome_completo', 'ilike', texto),
                ('codigo_completo', 'ilike', texto),
                ('codigo', '=', codigo)
            ]

        else:
            procura = [
                '|',
                ('nome_completo', 'ilike', texto),
                ('codigo_completo', 'ilike', texto)
            ]

        return procura

    def monta_codigo(self, cr, uid, id):
        etapa_obj = self.browse(cr, uid, id)

        #cr.execute('select max(codigo) from project_orcamento_etapa;')
        #res = cr.fetchall()[0][0]
        #tamanho_maximo = len(str(res))
        tamanho_maximo = 2

        codigo = str(etapa_obj.codigo).zfill(tamanho_maximo)

        if etapa_obj.parent_id:
            codigo = self.monta_codigo(cr, uid, etapa_obj.parent_id.id) + '.' + codigo

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
        'orcamento_id': fields.many2one('project.orcamento', u'Orçamento', ondelete='cascade'),
        #'phase_id': fields.many2one('project.phase', u'Fase', ondelete='restrict'),
        'etapa_id': fields.many2one('project.etapa', u'Etapa', ondelete='restrict', required=True),
        #'nome': fields.char(u'Nome', size=64, required=True, select=True),
        'codigo': fields.integer(u'Ordem', select=True, required=True),
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Descrição', fnct_search=_procura_nome, store=True, select=True),
        'codigo_completo': fields.function(_get_codigo_funcao, type='char', string=u'Código completo', store=True),
        'parent_id': fields.many2one('project.orcamento.etapa', u'Etapa superior', select=True, ondelete='restrict'),
        'contas_filhas_ids': fields.one2many('project.orcamento.etapa', 'parent_id', string=u'Etapas filhas'),
        'sintetica': fields.boolean(u'Sintética', select=True),
        'parent_left': fields.integer(u'Etapa à esquerda', select=1),
        'parent_right': fields.integer(u'Etapa à direita', select=1),
    }
    
    #def copy(self, cr, uid, ids, dados, context={}):
        
    #    return super(project_orcamento_etapa, self).copy(cr, uid, ids, dados, context)



project_orcamento_etapa()
