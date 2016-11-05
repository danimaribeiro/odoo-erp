# -*- coding: utf-8 -*-

# from __future__ import division, print_function, unicode_literals

from py3o.template import Template
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
import pybrasil


#t.set_image_path('staticimage.logo', 'images/new_logo.png')


linhas = []

#
# Títulos
#
item1 = DicionarioBrasil()
item1.campo1 = u'Campo 1'
item1.campo2 = u'Campo 2'
item1.campo3 = u'Campo 3'
#item1.Currency = 'EUR'
#item1.Amount = '12345.35'
#item1.InvoiceRef = '#1234'
#linhas.append(item1)

total = D(0)
for i in xrange(100):
    item = DicionarioBrasil()
    item.campo1 = u'Valor %s ex. campo 1' % i
    item.campo2 = u'Valor %s ex. campo 2' % i
    item.campo3 = u'Valor %s ex. campo 3' % i
    valor = D(i) * D('1234567.89')
    total += valor
    item.campo4 = pybrasil.valor.formata_valor(valor)
    item.campo5 = pybrasil.data.formata_data(pybrasil.data.parse_datetime('2016-06-20').date(), '%d/%m/%Y')
    item.campo6 = 'Sim' if i % 2 == 0 else u'Não'
    item.campo7 = i
    item.cor_sim = i % 2 == 0
    item.cor_nao = i % 2 != 0
    #item.Currency = 'EUR'
    #item.Amount = '6666.77'
    #item.InvoiceRef = 'Reference #%04d' % i
    linhas.append(item)


linha_total = DicionarioBrasil()
linha_total.campo4 = pybrasil.valor.formata_valor(total)
#document = Item()
#document.total = '9999999999999.999'

#data = dict(items=items, document=document)

relatorio = DicionarioBrasil()
relatorio['titulo'] = u'Orçado × Realizado (compras)'

dados = {
    'items': linhas,
    'linhas': linhas,
    'total': linha_total,
    'hoje': pybrasil.data.formata_data(pybrasil.data.hoje(), '%d/%m/%Y'),
    'agora': pybrasil.data.formata_data(pybrasil.data.agora(), '%d/%m/%Y %H:%M:%S'),
    'relatorio': relatorio,
}

t = Template("/home/william/relatorio_teste/relatorio_teste.ods", "/home/william/relatorio_teste/saida.ods")
t.render(dados)

t = Template("/home/william/relatorio_teste/relatorio_teste.odt", "/home/willaim/relatorio_teste/saida.odt")
t.render(dados)
