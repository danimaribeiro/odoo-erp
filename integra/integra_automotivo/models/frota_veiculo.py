# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields

COMBUSTIVEL = (
    ('FLEX', 'Gasolina/etanol - FLEX'),
    ('GASOLINA', u'Gasolina'),
    ('ETANOL', u'Etanol'),
    ('DIESEL', u'Diesel'),
    ('GLP', 'GLP'),
    ('ELETRICO', 'Eletricidade')
)

DIRECAO = (
    ('M', u'Mecânica'),
    ('H', u'Hidráulica'),
    ('E', u'Elétrica'),
)

CAMBIO = (
    ('M', u'Manual'),
    ('A', u'Automático'),
)

FREIO = (
    ('D', u'Disco'),
    ('A', u'ABS'),
    ('B', u'Bosch'),
    ('G', u'Girling'),
    ('T', u'Teves'),
    ('V', u'Varga'),
)

MOTOR =(
    ('AP', u'AP'),
    ('AT', u'AT'),
    ('CHT', u'CHT'),
    ('Cummins', u'Cummins'),
    ('MWM', u'MWM'),
    ('Perkins', u'Perkins'),
    ('Scania 124', u'Scania 124'),
    ('Zetec', u'Zetec'),
)

TIPO_USO = (
    ('U', u'Urbano'),
    ('R', u'Rodoviário'),
    ('L', u'Rural'),
    ('M', u'Misto'),
)


class frota_veiculo(osv.Model):
    _name = 'frota.veiculo'
    _inherit = 'frota.veiculo'

    _columns = {
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'direcao': fields.selection(DIRECAO, u'Direção'),
        'cambio': fields.selection(DIRECAO, u'Câmbio'),
        'freio': fields.selection(FREIO, u'Freio'),
        'motor': fields.selection(MOTOR, u'Motor'),
        'tipo_uso': fields.selection(TIPO_USO, u'Uso'),
        'vidro_eletrico': fields.boolean(u'Vidro elétrico?'),
        'trava_eletrica': fields.boolean(u'Trava elétrica?'),
        'air_bag': fields.boolean(u'Air-bag?'),
        'ar_quente': fields.boolean(u'Ar quente?'),
        'desembacador': fields.boolean(u'Desembaçador?'),
    }

    _defaults = {
        'combustivel': 'FLEX',
        'direcao': 'H',
        'freio': 'A',
        'cambio': 'M',
        'tipo_uso': 'U',
    }


frota_veiculo()
