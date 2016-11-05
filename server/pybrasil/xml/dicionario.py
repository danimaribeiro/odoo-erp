# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from lxml import etree
from ..base import DicionarioBrasil, UnicodeBrasil


def _xml_para_dicionario(noh_xml):
    dicionario = DicionarioBrasil()

    ##
    ## O nó tem itens, definir esses itens
    ##
    #if len(noh_xml.items()) > 0:
        #for k, v in noh_xml.items():
            #dicionario[k] = v

    #
    # O nó tem atributos, definir os atributos
    #
    if noh_xml.attrib:
        for k, v in noh_xml.attrib.items():
            dicionario['__' + k] = v

    #
    # Adiciona recursivamente os elementos filhos
    #
    for noh_filho in noh_xml:
        novo_item = _xml_para_dicionario(noh_filho)

        #
        # Tem namespace
        #
        if b'}' in noh_filho.tag:
            tag = ''.join(noh_filho.tag.split(b'}')[1:])
        else:
            tag = noh_filho.tag

        #
        # Tem mais de uma tag com o mesmo nome, gerar
        # uma lista
        #
        if tag in dicionario:
            if isinstance(dicionario[tag], list):
                dicionario[tag].append(novo_item)

            else:
                dicionario[tag] = [dicionario[tag], novo_item]
        else:
            dicionario[tag] = novo_item

    if noh_xml.text is None:
        texto = ''
    else:
        texto = noh_xml.text.strip()

    if len(dicionario) > 0:
        #
        # Caso a tag tenha itens, adiciona o texto como __texto
        #
        if texto:
            dicionario['_texto'] = texto

    else:
        return UnicodeBrasil(texto)

    return dicionario


def xml_para_dicionario(arquivo_xml):
    if b'<' in arquivo_xml:
        if isinstance(arquivo_xml, str):
            arquivo_xml = arquivo_xml.decode('utf-8')
        raiz = etree.fromstring(arquivo_xml.encode('utf-8'))
    else:
        raiz = etree.parse(arquivo_xml).getroot()

    if b'}' in raiz.tag:
        tag = ''.join(raiz.tag.split(b'}')[1:])
    else:
        tag = raiz.tag

    return DicionarioBrasil({tag: _xml_para_dicionario(raiz)})


def _dicionario_para_xml(noh_xml, item):
    print(noh_xml, item, type(item))
    if isinstance(item, dict):
        for tag, valor in item.iteritems():
            if tag == '_texto':
                noh_xml.text = valor

            elif tag.startswith('__'):
                noh_xml.attrib[tag.replace('__', '')] = valor

            elif isinstance(valor, (list, tuple)):
                for item_filho in valor:
                    noh_filho = etree.Element(tag)
                    noh_xml.append(noh_filho)
                    _dicionario_para_xml(noh_filho, item_filho)
            else:
                noh_filho = etree.Element(tag)
                noh_xml.append(noh_filho)
                _dicionario_para_xml(noh_filho, valor)

    else:
        noh_xml.text = item


def dicionario_para_xml(dicionario):
    tag_raiz = dicionario.keys()[0]
    raiz = etree.Element(tag_raiz)
    _dicionario_para_xml(raiz, dicionario[tag_raiz])
    return raiz

##def _ConvertDictToXmlRecurse(parent, dictitem):
    ##assert type(dictitem) is not type([])

    ##if isinstance(dictitem, dict):
        ##for (tag, child) in dictitem.iteritems():
            ##if str(tag) == '_text':
                ##parent.text = str(child)
            ##elif type(child) is type([]):
                ### iterate through the array and convert
                ##for listchild in child:
                    ##elem = ElementTree.Element(tag)
                    ##parent.append(elem)
                    ##_ConvertDictToXmlRecurse(elem, listchild)
            ##else:
                ##elem = ElementTree.Element(tag)
                ##parent.append(elem)
                ##_ConvertDictToXmlRecurse(elem, child)
    ##else:
        ##parent.text = str(dictitem)

##def ConvertDictToXml(xmldict):
    ##"""
    ##Converts a dictionary to an XML ElementTree Element
    ##"""

    ##roottag = xmldict.keys()[0]
    ##root = ElementTree.Element(roottag)
    ##_ConvertDictToXmlRecurse(root, xmldict[roottag])
    ##return root


def teste():
    d = DicionarioBrasil()
    d['raiz'] = DicionarioBrasil()
    d.raiz['tag_caracter'] = 'áéíóú'
    d.raiz['__versao'] = 'áéíóú'
    d.raiz['__xmlns'] = 'http://www.betha.com.br/e-nota-contribuinte-ws'
    xml = dicionario_para_xml(d)
    xml_texto = etree.tostring(xml, xml_declaration=True, pretty_print=False, encoding='utf-8').replace(b'\n', b'')
    open('/home/ari/teste.xml', 'wb').write(xml_texto)

    d = xml_para_dicionario('/home/ari/teste.xml')

    return xml, xml_texto, d
