#-*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_datetime
from datetime import date

from osv import fields, osv


MESES = (
    ('01', u'janeiro'),
    ('02', u'fevereiro'),
    ('03', u'março'),
    ('04', u'abril'),
    ('05', u'maio'),
    ('06', u'junho'),
    ('07', u'julho'),
    ('08', u'agosto'),
    ('09', u'setembro'),
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


class finan_fat_eventual_contrato(osv.osv_memory):
    _name = 'finan.fat.eventual.contrato'
    _description = u'Produtos do Comtrato'
    _order = 'mes, ano'

    def _set_input_ids(self, cr, uid, ids, nome_campo, valor_campo, arg, context=None):
        #
        # Salva manualmente as entradas
        #
        if not isinstance(ids, list):
            if ids:
                ids = [ids]
            else:
                ids = []

        if len(valor_campo) and len(ids):
            for variavel_obj in self.browse(cr, uid, ids):
                for operacao, entrada_id, valores in valor_campo:
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
                    if operacao == 1:
                        self.pool.get('finan.contrato_produto').write(cr, uid, [entrada_id], valores)
                    elif operacao == 0:
                        self.pool.get('finan.contrato_produto').create(cr, uid, valores)
                    elif operacao == 2:
                        self.pool.get('finan.contrato_produto').unlink(cr, uid, [entrada_id])

    def _get_input_ids(self, cr, uid, ids, nome_campo, args=None, context={}):
        for eventual_obj in self.browse(cr, uid, ids):
            busca = [('data', '>=', eventual_obj.data_inicial), ('data','<=', eventual_obj.data_final)]

            if eventual_obj.contrato_id:
                busca += [('contrato_id', '=', eventual_obj.contrato_id.id)]

            print(busca)

            input_ids = self.pool.get('finan.contrato_produto').search(cr, uid, busca)

            res = {}
            if ids:
                for id in ids:
                    res[id] = input_ids
            else:
                res = input_ids

        return res

    _columns = {
        'ano': fields.integer(u'Ano', required=True),
        'mes': fields.selection(MESES,  u'Mês', required=True),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete="cascade"),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'input_ids': fields.function(_get_input_ids, method=False, type='one2many', string=u'Contrato Produtos', relation='finan.contrato_produto', fnct_inv=_set_input_ids),
    }

    _defaults = {
        'ano': lambda *args, **kwargs: mes_atual()[0],
        'mes': lambda *args, **kwargs: str(mes_atual()[1]).zfill(2),
        'data_inicial': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_atual())[0],
        'data_final': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_atual())[1],
    }

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

        return retorno

    def busca_entradas(self, cr, uid, ids, context={}):
        valores = {}
        retorno = {'value': valores}

        if 'ano' not in context or 'mes' not in context:
            return retorno

        ano = context['ano']
        mes = context['mes']

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')

        data_inicial, data_final = primeiro_ultimo_dia_mes(ano, int(mes))

        valores['data_inicial'] = data_inicial
        valores['data_final'] = data_final

        valores['input_ids'] = self._get_input_ids(cr, uid, ids, 'input_ids', context=context)

        return retorno


finan_fat_eventual_contrato()
