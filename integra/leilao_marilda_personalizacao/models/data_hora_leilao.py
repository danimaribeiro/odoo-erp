# -*- encoding: utf-8 -*-


from osv import osv, fields
from pybrasil.data import parse_datetime, formata_data


def float_time(tempo):
    hora = int(tempo)
    tempo -= hora

    if hora == 24:
        hora = 0

    tempo *= 60.0
    minuto = round(tempo)
    tempo -= minuto
    tempo *= 60.0
    segundo = round(tempo)
    tempo -= segundo
    return '%02d:%02d:%02d.%d' % (hora, minuto, segundo, tempo)


class data_hora_leilao(osv.osv):
    _name = 'data.hora.leilao'
    _description = 'data.hora.leilao'
    _rec_name = 'descricao'



    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for registro in self.browse(cursor, user_id, ids):
            txt = u''
            data = parse_datetime(registro.data)
            txt += formata_data(data) + ' ' + float_time(registro.hora)[:5]

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):

        texto = args[0][2]

        procura = [
            ('data', 'like', texto)
        ]
        return procura

    _columns = {
        #'data': fields.date(u'Data'),
        #'hora': fields.float(u'Hora', widget='float_time'),
        #'descricao': fields.function(_descricao, u'Descrição', method=True, type='char', fnct_search=_procura_descricao, store=True),
        'descricao': fields.char(u'Descrição', size=64),
        'order_ids': fields.one2many('sale.order','data_hora_id', u'Data Hora'),
      }

    _defaults = {
        #'data': fields.date.today,
    }


data_hora_leilao()