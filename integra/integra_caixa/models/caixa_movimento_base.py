# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.data import parse_datetime, formata_data, data_hora_horario_brasilia

SALVA = True


class caixa_movimento_base(orm.AbstractModel):
    _name = 'caixa.movimento_base'

    def _get_data(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for mov_obj in self.browse(cr, uid, ids):
            if nome_campo in ['data_abertura', 'dia_abertura', 'mes_abertura', 'ano_abertura', 'dia_abertura_display', 'mes_abertura_display']:
                if mov_obj.data_hora_abertura:
                    data = parse_datetime(mov_obj.data_hora_abertura)
                    data = data_hora_horario_brasilia(data)

                    if nome_campo == 'dia_abertura_display':
                        data = formata_data(data, '%d/%m/%Y')

                    elif nome_campo == 'dia_abertura':
                        data = formata_data(data, '%d/%m/%Y')

                    elif nome_campo == 'mes_abertura_display':
                        data = formata_data(data, '%B de %Y')

                    elif nome_campo == 'mes_abertura':
                        data = formata_data(data, '%B de %Y')

                    elif nome_campo == 'ano_abertura':
                        data = formata_data(data, '%Y')

                else:
                    data = False

            elif nome_campo in ['data_fechamento', 'dia_fechamento', 'mes_fechamento', 'ano_fechamento', 'dia_fechamento_display', 'mes_fechamento_display']:
                if mov_obj.data_hora_fechamento:
                    data = parse_datetime(mov_obj.data_hora_fechamento)
                    data = data_hora_horario_brasilia(data)

                    if nome_campo == 'dia_fechamento_display':
                        data = formata_data(data, '%d/%m/%Y')

                    elif nome_campo == 'dia_fechamento':
                        data = formata_data(data, '%d/%m/%Y')

                    elif nome_campo == 'mes_fechamento_display':
                        data = formata_data(data, '%B de %Y')

                    elif nome_campo == 'mes_fechamento':
                        data = formata_data(data, '%B de %Y')

                    elif nome_campo == 'ano_fechamento':
                        data = formata_data(data, '%Y')

                else:
                    data = False


            res[mov_obj.id] = data

        return res

    _columns = {
        'data_hora_abertura': fields.datetime(u'Data de abertura', required=True, select=True),
        'data_abertura': fields.function(_get_data, type='date', string=u'Data de abertura', store=SALVA, select=True),
        'dia_abertura': fields.function(_get_data, type='char', string=u'Dia de abertura', store=SALVA, select=True),
        'mes_abertura': fields.function(_get_data, type='char', string=u'Mês de abertura', store=SALVA, select=True),
        'ano_abertura': fields.function(_get_data, type='char', string=u'Ano de abertura', store=SALVA, select=True),
        'data_hora_fechamento': fields.datetime(u'Data de fechamento', select=True),
        'data_fechamento': fields.function(_get_data, type='date', string=u'Data de fechamento', store=SALVA, select=True),
        'dia_fechamento': fields.function(_get_data, type='char', string=u'Dia de fechamento', store=SALVA, select=True),
        'mes_fechamento': fields.function(_get_data, type='char', string=u'Mês de fechamento', store=SALVA, select=True),
        'ano_fechamento': fields.function(_get_data, type='char', string=u'Ano de fechamento', store=SALVA, select=True),
    }

    _defaults = {
        'data_hora_abertura': fields.datetime.now,
    }


caixa_movimento_base()
