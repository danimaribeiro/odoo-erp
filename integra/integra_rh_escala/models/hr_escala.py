#-*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_datetime
from datetime import date
from osv import fields, osv


MESES = (
    ('1', u'janeiro'),
    ('2', u'fevereiro'),
    ('3', u'março'),
    ('4', u'abril'),
    ('5', u'maio'),
    ('6', u'junho'),
    ('7', u'julho'),
    ('8', u'agosto'),
    ('9', u'setembro'),
    ('10', u'outubro'),
    ('11', u'novembro'),
    ('12', u'dezembro'),
)

MESES_DIC = dict(MESES)


def mes_atual():
    hoje = parse_datetime(fields.date.today())
    return hoje.year, hoje.month


def mes_seguinte():
    hoje = parse_datetime(fields.date.today())
    mes_passado = hoje + relativedelta(months=+1)
    return mes_passado.year, mes_passado.month


def mes_passado():
    hoje = parse_datetime(fields.date.today())
    mes_passado = hoje + relativedelta(months=-1)
    return mes_passado.year, mes_passado.month


def primeiro_ultimo_dia_mes(ano, mes):
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = primeiro_dia + relativedelta(months=+1, days=-1)
    return str(primeiro_dia)[:10], str(ultimo_dia)[:10]


class hr_escala(osv.Model):
    _name = 'hr.escala'
    _description = u'Escalas de funcionários'
    _order = 'data_final desc, data_inicial desc, contract_id'
    _rec_name = 'contract_id'

    _columns = {
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'contract_id': fields.many2one('hr.contract', u'Funcionário'),
        'item_ids': fields.one2many('hr.escala.item', 'escala_id', u'Itens'),
        'primeiro_dia_trabalho': fields.date(u'Primeiro dia de trabalho'),
        #'dias_trabalho': fields.function(_get_dias, string=u'Dias trabalhados', method=True, type='float'),
        #'dias_descanso': fields.function(_get_dias, string=u'Dias trabalhados', method=True, type='float'),
        #'dias_falta': fields.function(_get_dias, string=u'Dias trabalhados', method=True, type='float'),
        #'dias_afastado': fields.function(_get_dias, string=u'Dias trabalhados', method=True, type='float'),
        #'dias_ferias': fields.function(_get_dias, string=u'Dias trabalhados', method=True, type='float'),
    }

    #_defaults = {
        #'ano': lambda *args, **kwargs: mes_passado()[0],
        #'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        #'rubricas_similares': True,
        #'data_inicial': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[0],
        #'data_final': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[1],
        #'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'hr.payslip', context=c),
    #}

    def onchange_ano_mes(self, cr, uid, ids, ano, mes, context={}):
        valores = {}
        retorno = {'value': valores}

        if not ano or not mes:
            return retorno

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')

        data_inicial, data_final = primeiro_ultimo_dia_mes(ano, int(mes))

        valores['data_inicial'] = data_inicial
        valores['data_final'] = data_final
        valores['primeiro_dia_trabalho'] = data_inicial

        return retorno

    def monta_escala(self, cr, uid, ids, context={}):
        if not ids:
            return

        item_pool = self.pool.get('hr.escala.item')

        for escala_obj in self.browse(cr, uid, ids):
            for item_obj in escala_obj.item_ids:
                item_obj.unlink()

            dados = {
                'escala_id': escala_obj.id,
                'jornada_id': escala_obj.contract_id.jornada_escala_id.id,
                'lotacao_id': escala_obj.contract_id.lotacao_id.id,
            }

            primeiro_dia_trabalho = parse_datetime(escala_obj.primeiro_dia_trabalho).date()
            data = parse_datetime(escala_obj.data_inicial).date()
            data_final = parse_datetime(escala_obj.data_final).date()

            dias_trabalho = 1
            if escala_obj.contract_id.jornada_escala == '1':
                dias_folga = 1
            elif escala_obj.contract_id.jornada_escala == '2':
                dias_folga = 3
            elif escala_obj.contract_id.jornada_escala == '3':
                dias_folga = 0

            folga = 0
            while data <= data_final:
                if folga > dias_folga: ## or dias_folga != 0:
                    folga = 0

                dados['data'] = str(data)[:10]
                print(data, folga)

                if folga or data < primeiro_dia_trabalho:
                    dados['situacao'] = 'D'
                    dados['jornada_id'] = False
                    dados['lotacao_id'] = False

                else:
                    dados['situacao'] = 'T'
                    dados['jornada_id'] = escala_obj.contract_id.jornada_escala_id.id
                    dados['lotacao_id'] = escala_obj.contract_id.lotacao_id.id

                item_pool.create(cr, uid, dados)

                data += relativedelta(days=+1)

                if data > primeiro_dia_trabalho:
                    folga += 1

        return {}


hr_escala()


class hr_escala_item(osv.Model):
    _name = 'hr.escala.item'
    _description = u'Item de escalas de funcionários'
    _order = 'escala_id, data'

    _columns = {
        'escala_id': fields.many2one('hr.escala', u'Escala'),
        'data': fields.date(u'Data', select=True),
        'jornada_id': fields.many2one('hr.jornada', u'Jornada'),
        'lotacao_id': fields.many2one('res.partner', u'Lotação'),
        'situacao': fields.selection([['T', u'Trabalhou'], ['F', u'Faltou'], ['D', u'Descansou'], ['A', u'Afastado'], ['V', u'Férias']], u'Situação', select=True),
        #'data_hora_entrada_prevista': fields.datetime(u'Data entrada prevista'),
        #'data_hora_entrada_real': fields.datetime(u'Data entrada real'),
        #'data_hora_entrada_prevista': fields.datetime(u'Data entrada prevista'),
    }

    _defaults = {
        'situacao': 'T',
    }


hr_escala_item()
