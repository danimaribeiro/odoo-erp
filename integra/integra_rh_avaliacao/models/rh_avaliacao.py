# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class rh_avaliacao(orm.Model):
    _name = 'rh.avaliacao'
    _description = 'Avaliação'
    _order = 'nome'
    _rec_name = 'nome'

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        if not len(ids):
            return {}

        res = []
        for id in ids:
            carteira_obj = self.browse(cr, uid, id)
            if carteira_obj.res_partner_bank_id:
                texto = carteira_obj.res_partner_bank_id.nome or ''
            else:
                texto = ''

            texto += ' - ' + carteira_obj.carteira or ''

            res += [(id, texto)]

        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('res_partner_bank_id', 'like', texto),
            ('res_partner_bank_id.carteira', 'like', texto),
        ]

        return procura

    _columns = {
        'nome': fields.char(u'Nome', size=60),
        'data_inicio': fields.date(u'Data de início'),
        'data_termino': fields.date(u'Data de término'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'descricao': fields.text(u'Descrição'),
        'avaliacao_item_ids': fields.one2many('rh.avaliacao_item', 'avaliacao_id', u'Eventos/avaliações'),
        'avaliacao_participante_ids': fields.many2many('hr.contract', 'rh_avaliacao_participante', 'avaliacao_id', 'contract_id', u'Participantes'),
    }


rh_avaliacao()


class rh_avaliacao_item(orm.Model):
    _name = 'rh.avaliacao_item'
    _description = 'Ítens de Avaliação'
    _order = 'avaliacao_id'
    _rec_name = 'avaliacao_id'

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        if not len(ids):
            return {}

        res = []
        for id in ids:
            carteira_obj = self.browse(cr, uid, id)
            if carteira_obj.res_partner_bank_id:
                texto = carteira_obj.res_partner_bank_id.nome or ''
            else:
                texto = ''

            texto += ' - ' + carteira_obj.carteira or ''

            res += [(id, texto)]

        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('res_partner_bank_id', 'like', texto),
            ('res_partner_bank_id.carteira', 'like', texto),
        ]

        return procura

    _columns = {
        'avaliacao_id': fields.many2one('rh.avaliacao', u'Campanha/Avaliação'),
        'data': fields.date(u'Data'),
        'tipo_id': fields.many2one('rh.tipoavaliacao', u'Tipo'),
        'tipo': fields.related('tipo_id', 'tipo', type='char', string='+/-', store=True),
        'pontos': fields.related('tipo_id', 'pontos', type='integer', string='Pontos', store=True),
        'tratamento': fields.related('tipo_id', 'tratamento', type='char', string='Tratamento', store=False),
        'company_id': fields.related('avaliacao_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa', store=True, select=True, readonly=True),
        'employee_id': fields.many2one('hr.employee', u'Funcionário'),
        'supervisor_id': fields.many2one('hr.employee', u'Supervisor'),
        'jornada_id': fields.many2one('hr.jornada', u'Turno'),

        'descricao': fields.char(u'Descrição', size=60),
        #
        # Projeto
        #
        'o_que': fields.text(u'O quê?'),
        'por_que': fields.text(u'Por quê?'),
        'como': fields.text(u'Como?'),
        'quem': fields.text(u'Quem?'),
        'quando': fields.text(u'Quando?'),
        'data_quando': fields.date(u'Data'),
        'quanto': fields.text(u'Quanto?'),

        #
        # Correção
        #
        'incidente': fields.text(u'Incidente'),  # o_que
        'motivo': fields.text(u'Motivo'),  # por_que
        'acoes_corretivas': fields.text(u'Ações corretivas'),  # como
        'responsavel': fields.text(u'Responsável'),  # quem

        'obs': fields.text(u'Observações'),
    }


rh_avaliacao_item()


class rh_avaliacao_participante(orm.Model):
    _name = 'rh.avaliacao_participante'
    _description = 'Participantes de Avaliação'
    _order = 'avaliacao_id'
    _rec_name = 'avaliacao_id'

    _columns = {
        'avaliacao_id': fields.many2one('rh.avaliacao', u'Campanha/Avaliação'),
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'employee_id': fields.related('contract_id', 'employee_id', type='many2one', string=u'Funcionário', relation='hr.employee', store=True, select=True, readonly=True),
        'job_id': fields.related('contract_id', 'job_id', type='many2one', string=u'Cargo', relation='hr.job', store=True, select=True, readonly=True),
    }


rh_avaliacao_participante()
