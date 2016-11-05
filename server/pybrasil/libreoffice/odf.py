# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from StringIO import StringIO
from zipfile import ZipFile
import sh


VARIAVEIS = {
    'EMPRESACAB': 'ESTE É O NOME DA EMPRESA',

}

TEMPLATE_CAMPO = '<text:database-display text:table-name="" text:table-type="table" text:column-name="%s">«%s»</text:database-display>'


def troca_campo(texto):
    for campo, valor in VARIAVEIS.iteritems():
        tag_campo = TEMPLATE_CAMPO % (campo, campo)
        texto = texto.replace(tag_campo, valor)

    return texto


if __name__ == '__main__':
    odt = file('/home/ari/relatorios_rh_patrimonial/RH-PEDIDO DE DEMISSAO.odt', 'r').read()
    arq = StringIO()
    arq.write(odt)
    arq.seek(0)
    z = ZipFile(arq, mode='r')

    #
    # Guarda o conteúdo de todos os arquivos no ODT
    #
    arquivos = {}
    for nome_arq in z.namelist():
        arquivos[nome_arq] = z.read(nome_arq)
    z.close()
    arq.close()

    #
    # Extrai o conteúdo do texto
    #
    texto = arquivos['content.xml'].decode('utf-8')
    texto = troca_campo(texto)
    arquivos['content.xml'] = texto.encode('utf-8')

    #
    # Recria o zip com o novo conteúdo
    #
    arq = StringIO()
    z = ZipFile(arq, mode='w')
    for nome_arq in arquivos:
        z.writestr(nome_arq, arquivos[nome_arq])
    z.close()
    arq.seek(0)
    file('/tmp/novo.odt', 'w').write(arq.read())
    arq.close()

    #
    # Converte para doc
    #
    sh.libreoffice('--headless', '--invisible', '--convert-to', 'doc', '/tmp/novo.odt')