# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields
from decimal import Decimal as D
from pybrasil.data import parse_datetime, data_hora_horario_brasilia, data_hora, hoje


TIPO = (
    ('P', u'Prospecto'),
    ('V', u'Venda/orçamento'),
    ('O', u'Ordem de serviço'),
)

SITUACAO_ETAPA = (
    ('V', u'Venda'),
    ('L', u'Locação'),
)


class sale_etapa(osv.Model):
    _description = u'Etapa da OS'
    _name = 'sale.etapa'
    _rec_name = 'nome'
    _order = 'ordem'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for os_obj in self.browse(cr, uid, ids):
            res[os_obj.id] = os_obj.tipo + '-' + str(os_obj.id).zfill(4)

        return res

    def _ordem(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for os_obj in self.browse(cr, uid, ids):
            if os_obj.tipo == 'P':
                ordem = 1000000
            elif os_obj.tipo == 'V':
                ordem = 2000000
            elif os_obj.tipo == 'O':
                ordem = 3000000

            res[os_obj.id] = ordem + os_obj.id

        return res

    def _filtro(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for etapa_obj in self.browse(cr, uid, ids):
            retorno = u''
            for etapa_seguinte_obj in etapa_obj.etapa_seguinte_ids:
                retorno += str(etapa_seguinte_obj.id).zfill(4) + '|'

            res[etapa_obj.id] = retorno

        return res

    _columns = {
        'tipo': fields.selection(TIPO, string=u'Tipo', select=True),
        'ordem': fields.function(_ordem, type='integer', method=True, string=u'Ordem', store=True, select=True),
        'codigo': fields.function(_codigo, type='char', method=True, string=u'Código', size=20, store=False, select=True),
        'filtro_etapa': fields.function(_filtro, type='char', method=True, string=u'Código', size=280, store=True, select=True),
        'nome': fields.char(u'Nome', size=180),
        'etapa_seguinte_ids': fields.many2many('sale.etapa','sale_etapa_seguinte', 'etapa_id', 'etapa_seguinte_id', u'Etapa Seguinte'),
        'alimenta_estoque': fields.boolean(u'Alimenta estoque?'),
        'trava_comercial': fields.boolean(u'Trava comercial?'),
        'trava_tecnico': fields.boolean(u'Trava técnico?'),
        'libera_faturamento_contrato': fields.boolean(u'Libera o faturamento/contrato?'),
        'libera_monitoramento': fields.boolean(u'Libera o monitoramento?'),
        'situacao_etapa': fields.selection(SITUACAO_ETAPA, u'Situação em que a etapa ocorre'),
        'desconto_a_autorizar': fields.boolean(u'Desconto a autorizar?'),
        'tipo_os_id': fields.many2one('sale.tipo.os', u'Tipo da OS'),
    }

    def verifica_etapa(self, cr, uid, ids, dados, context=None):
        if 'etapa_seguinte_ids' not in dados or not dados['etapa_seguinte_ids']:
            return
        etapa_seguinte_ids = dados['etapa_seguinte_ids']

        for id in ids:

            if id in etapa_seguinte_ids[0][2]:
                raise osv.except_osv(u'Inválido !', u'Etapa seguinte deve ser diferente da atual!')

    def create(self, cr, uid, dados, context={}):
        res = super(sale_etapa, self).create(cr, uid, dados, context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        self.verifica_etapa(cr, uid, ids, dados)
        res = super(sale_etapa, self).write(cr, uid, ids, dados, context)

        return res

    def unlink(self, cr, uid, ids, context={}):
        if 1 == ids or 1 in ids:
            raise osv.except_osv(u'Inválido !', u'A etapa código P-0001 não pode ser excluída!')
        if 2 == ids or 2 in ids:
            raise osv.except_osv(u'Inválido !', u'A etapa código V-0002 não pode ser excluída!')
        if 3 == ids or 3 in ids:
            raise osv.except_osv(u'Inválido !', u'A etapa código O-0003 não pode ser excluída!')

        return super(sale_etapa, self).unlink(cr, uid, ids, context=context)


sale_etapa()
