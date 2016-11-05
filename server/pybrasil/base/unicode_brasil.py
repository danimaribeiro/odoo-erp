# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from collections import OrderedDict
from lxml import etree
from decimal import Decimal as DecimalOriginal
from ..valor import formata_valor, valor_por_extenso, valor_por_extenso_unidade
from pytz import datetime, UTC, timezone, tzinfo
from dateutil.parser import parse as parse_datetime
from ..data import ParserInfoBrasil
from .primeira_maiuscula import primeira_maiuscula
#from ..xml import dicionario_para_xml


class InteiroBrasil(int):
    def __init__(self, *args, **kwargs):
        super(InteiroBrasil, self).__init__(*args, **kwargs)
        self.unidade = None
        self.genero_unidade_masculino = True

    @property
    def formatado(self):
        return formata_valor(self, casas_decimais=0)

    @property
    def extenso(self):
        if isinstance(self.unidade, (list, tuple)):
            return valor_por_extenso_unidade(numero=self, unidade=self.unidade, genero_unidade_masculino=self.genero_unidade_masculino)
        else:
            return valor_por_extenso(self)


class DecimalBrasil(DecimalOriginal):
    def __init__(self, *args, **kwargs):
        super(DecimalBrasil, self).__init__(*args, **kwargs)
        self.unidade = None
        self.genero_unidade_masculino = True
        self.unidade_decimal = None
        self.genero_unidade_decimal_masculino = True
        self.precisao_decimal = 2

    @property
    def formatado(self):
        return formata_valor(self, casas_decimais=self.precisao_decimal)

    @property
    def extenso(self):
        if isinstance(self.unidade, (list, tuple)):
            return valor_por_extenso_unidade(numero=self, unidade=self.unidade, genero_unidade_masculino=self.genero_unidade_masculino, unidade_decimal=self.unidade_decimal, genero_unidade_decimal_masculino=self.genero_unidade_decimal_masculino, precisao_decimal=self.precisao_decimal)
        else:
            return valor_por_extenso(self)


class DataHoraUTCBrasil(datetime.datetime):
    def __init__(self, *args, **kwargs):
        super(DataHoraUTCBrasil, self).__init__(*args, **kwargs)

    @property
    def formatado(self):
        return self.strftime(b'%d/%m/%Y %H:%M:%S %z')


class DataHoraBrasil(datetime.datetime):
    def __init__(self, *args, **kwargs):
        super(DataHoraBrasil, self).__init__(*args, **kwargs)

    @property
    def formatado(self):
        return self.strftime(b'%d/%m/%Y %H:%M:%S')


class DataBrasil(datetime.date):
    def __init__(self, *args, **kwargs):
        super(DataBrasil, self).__init__(*args, **kwargs)

    @property
    def formatado(self):
        return self.strftime(b'%d/%m/%Y')


class HoraBrasil(datetime.time):
    def __init__(self, *args, **kwargs):
        super(HoraBrasil, self).__init__(*args, **kwargs)

    @property
    def formatado(self):
        return self.strftime(b'%H:%M:%S')


class UnicodeBrasil(unicode):
    def __init__(self, *args, **kwargs):
        super(UnicodeBrasil, self).__init__(*args, **kwargs)
        self.unidade = None
        self.genero_unidade_masculino = True
        self.unidade_decimal = None
        self.genero_unidade_decimal_masculino = True
        self.precisao_decimal = 2
        self.fuso_horario = 'America/Sao_Paulo'

    @property
    def fuso_horario(self):
        return self._fuso_horario

    @fuso_horario.setter
    def fuso_horario(self, valor):
        if isinstance(valor, tzinfo.tzinfo):
            self._fuso_horario = valor

        elif isinstance(valor, basestring):
            try:
                self.fuso_horario = timezone(valor)
            except:
                pass

    @property
    def inteiro(self):
        try:
            inteiro = InteiroBrasil(self)
        except:
            inteiro = InteiroBrasil()
        inteiro.unidade = self.unidade
        inteiro.genero_unidade_masculino = self.genero_unidade_masculino
        return inteiro

    @property
    def decimal(self):
        try:
            decimal = DecimalBrasil(self)
        except:
            decimal = DecimalBrasil()

        decimal.unidade = self.unidade
        decimal.genero_unidade_masculino = self.genero_unidade_masculino
        decimal.unidade_decimal = self.unidade_decimal
        decimal.genero_unidade_decimal_masculino = self.genero_unidade_decimal_masculino
        decimal.precisao_decimal = self.precisao_decimal
        return decimal

    @property
    def data_hora_utc(self):
        try:
            data_hora = parse_datetime(self)
        except:
            try:
                data_hora = parse_datetime(self, ParserInfoBrasil())
            except:
                data_hora = None

        if data_hora:
            if not data_hora.tzinfo:
                data_hora = self.fuso_horario.localize(data_hora)

            data_hora = UTC.normalize(data_hora)
            data_hora = self.fuso_horario.normalize(data_hora)
            return DataHoraUTCBrasil(year=data_hora.year, month=data_hora.month, day=data_hora.day, hour=data_hora.hour, minute=data_hora.minute, second=data_hora.second, microsecond=data_hora.microsecond, tzinfo=data_hora.tzinfo)

        return None

    @property
    def data_hora(self):
        data_hora = self.data_hora_utc

        if data_hora:
            return DataHoraBrasil(year=data_hora.year, month=data_hora.month, day=data_hora.day, hour=data_hora.hour, minute=data_hora.minute, second=data_hora.second, microsecond=data_hora.microsecond, tzinfo=data_hora.tzinfo)

        return None

    @property
    def data(self):
        data_hora = self.data_hora_utc

        if data_hora:
            return DataBrasil(year=data_hora.year, month=data_hora.month, day=data_hora.day)

        return None

    @property
    def hora(self):
        data_hora = self.data_hora_utc

        if data_hora:
            return HoraBrasil(hour=data_hora.hour, minute=data_hora.minute, second=data_hora.second, microsecond=data_hora.microsecond, tzinfo=data_hora.tzinfo)

        return None

    @property
    def primeira_maiuscula(self):
        return primeira_maiuscula(self)


class DicionarioBrasil(OrderedDict):
    '''
    Adiciona acesso aos itens do dicionario
    como atributos de uma instancia
    '''

    def __init__(self, *args, **kwargs):
        if len(args):
            if isinstance(args[0], dict):
                args = (sorted(args[0].items(), key=lambda item: item[0]),)
        else:
            args = ([],)

        for k, v in args[0]:
            if isinstance(v, dict):
                self.__dict__[k] = DicionarioBrasil(v)

            else:
                self.__dict__[k] = v

        super(DicionarioBrasil, self).__init__(*args, **kwargs)

    def __setitem__(self, chave, valor, dict_setitem=dict.__setitem__, faz_set_attr=True):
        if isinstance(valor, basestring):
            valor = UnicodeBrasil(valor)

        if '__DOISPONTOS__' in chave:
            chave = chave.replace('__DOISPONTOS__', ':')

        super(DicionarioBrasil, self).__setitem__(chave, valor, dict_setitem=dict_setitem)

        if faz_set_attr:
            self.__setattr__(chave, valor, faz_set_item=False)

    def __setattr__(self, item, valor, faz_set_item=True):
        if isinstance(valor, basestring):
            valor = UnicodeBrasil(valor)

        if ':' in item:
            item = item.replace(':', '__DOISPONTOS__')

        super(DicionarioBrasil, self).__setattr__(item, valor)

        if faz_set_item and item in self:
            self.__setitem__(item, valor, dict_setitem=dict.__setitem__, faz_set_attr=False)

    def __unicode__(self):
        if '__texto' in self:
            return self.__getitem__('__texto')
        else:
            return ''

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    @property
    def como_xml(self):
        return dicionario_para_xml(self)

    @property
    def como_xml_em_texto(self):
        return etree.tostring(self.como_xml, pretty_print=False, encoding='utf-8').decode('utf-8')

    @property
    def como_xml_em_texto_iso_8859_1(self):
        return etree.tostring(self.como_xml, pretty_print=False, encoding='iso-8859-1', xml_declaration=False)


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

    if noh_xml.prefix:
        dicionario['__xmlns:' + noh_xml.prefix] = noh_xml.nsmap[noh_xml.prefix]

    elif b'}' in noh_xml.tag:
        namespace = noh_xml.tag.split(b'}')[0]
        namespace = namespace.replace(b'{', '').replace(b'}', '')

        #
        # Não repete o namespace se for igual ao do nó pai
        #
        noh_pai = noh_xml.getparent()
        if noh_pai is not None and b'}' in noh_pai.tag:
                namespace_pai = noh_pai.tag.split(b'}')[0]
                namespace_pai = namespace_pai.replace(b'{', '').replace(b'}', '')

                if namespace_pai == namespace:
                    namespace = ''

        if namespace:
            dicionario['__xmlns'] = namespace

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


def _busca_namespaces(dicionario, recursivo=False):
    if not isinstance(dicionario, dict):
        return {}

    nsmap = {}

    for k, v in dicionario.items():
        if '__xmlns:' in k:
            nsmap[k.replace('__xmlns:', '').encode('utf-8')] = unicode(v)

        elif recursivo and isinstance(v, dict):
            nsmap.update(_busca_namespaces(v))

    return nsmap


def _gera_nome_tag(tag, dicionario):
    if not isinstance(dicionario, dict):
        return tag

    ns = _busca_namespaces(dicionario[tag])
    if len(ns) > 0 and ns.keys()[0] not in [b'xsi', b'xsd']:
        tag = '{' + ns.values()[0] + '}' + tag

    return tag


def _dicionario_para_xml(noh_xml, item, nsmap_geral):
    if isinstance(item, dict):
        for tag, valor in item.iteritems():
            if valor is None:
                continue

            elif tag == '_texto':
                noh_xml.text = unicode(valor)

            elif tag.startswith('__'):
                atributo = tag.replace('__', '')

                if 'xmlns' not in atributo:
                    noh_xml.set(atributo, unicode(valor))
                elif atributo == 'xmlns':
                    noh_xml.set(atributo, valor)

            elif isinstance(valor, (list, tuple)):
                for item_filho in valor:
                    noh_filho = etree.Element(tag, nsmap=nsmap_geral)
                    noh_xml.append(noh_filho)
                    _dicionario_para_xml(noh_filho, item_filho, nsmap_geral)
            else:
                noh_filho = etree.Element(_gera_nome_tag(tag, item), nsmap=nsmap_geral)
                noh_xml.append(noh_filho)
                _dicionario_para_xml(noh_filho, valor, nsmap_geral)

    else:
        noh_xml.text = unicode(item)


def dicionario_para_xml(dicionario):
    for k in dicionario.keys():
        if not k.startswith('__'):
            tag_raiz = k

    nsmap_geral = _busca_namespaces(dicionario[tag_raiz], recursivo=True)

    raiz = etree.Element(_gera_nome_tag(tag_raiz, dicionario), nsmap=nsmap_geral)
    _dicionario_para_xml(raiz, dicionario[tag_raiz], nsmap_geral)
    return raiz
