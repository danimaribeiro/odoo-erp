# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals, absolute_import)

import re
import os
import shutil
from lxml import etree

from pysped.nfe.leiaute import *
from pysped.cte.leiaute import *
from pysped.xml_sped import XMLNFe, tira_abertura
from pysped.xml_sped.certificado import Certificado
from pysped.nfe.processador_nfe import ProcessadorNFe
from pysped.nfe.webservices_flags import CODIGO_UF


MAPA_ESQUEMAS = {}

for tipo in dir():
    if type(eval(tipo)) == type and issubclass(eval(tipo), XMLNFe) and eval(tipo + '().arquivo_esquema'):
            MAPA_ESQUEMAS[tipo] = os.path.join(eval(tipo + '().caminho_esquema'), eval(tipo + '().arquivo_esquema'))

LIMPA_ESPACO_ENTRE_TAGS = re.compile(r'(>)\s+(<)')


def valida_codificacao(arq_xml):
    try:
        xml = open(arq_xml).read()
        xml = xml.decode('utf-8')

        #
        # Remove caracteres desnecessários
        #
        xml = xml.replace('\r', '')
        xml = xml.replace('\n', '')

        #
        # Remove espaços entre as tags
        #
        xml = LIMPA_ESPACO_ENTRE_TAGS.sub(r'\1\2', xml)

        #
        # Tira tag de abertura com a codificação
        #
        xml = tira_abertura(xml)
    except:
        return ''

    return xml


def correcoes_xml(xml):
    CORRECOES = [
        #
        # Corrige falta de versão no CT-e
        #
        ('<cteProc xmlns="http://www.portalfiscal.inf.br/cte" versao="">', '<cteProc xmlns="http://www.portalfiscal.inf.br/cte" versao="1.04">'),
        ('<cteProc versao="1.04" xmlns="http://www.portalfiscal.inf.br/cte" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.portalfiscal.inf.br/cte procCTe_v1.04.xsd">', '<cteProc xmlns="http://www.portalfiscal.inf.br/cte" versao="1.04">'),

        #
        # Corrige schema da assinatura no lugar errado
        #
        ('<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.portalfiscal.inf.br/nfe procNFe_v2.00.xsd" versao="2.00">', '<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">'),

        ('<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance&quot;">', '<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">'),

        ('<nfeProc versao="2.00" xmlns:ns2="http://www.w3.org/2000/09/xmldsig#" xmlns="http://www.portalfiscal.inf.br/nfe">', '<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">'),

        ('<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" versao="2.00">', '<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">'),

        ('<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.portalfiscal.inf.br/nfe procNFe_v2.00.xsd">', '<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">'),

        ('<nfeProc xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">', '<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">'),

        ('<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" versao="2.00">', '<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">'),

        ('<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">', '<nfeProc versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">'),
    ]

    for errado, certo in CORRECOES:
        if errado in xml:
            xml = xml.replace(errado, certo)

    return xml


def valida_esquema(xml, tipo):
    arquivo_esquema = MAPA_ESQUEMAS[tipo]
    #print(arquivo_esquema)
    esquema = etree.XMLSchema(etree.parse(arquivo_esquema))

    try:
        esquema.validate(etree.fromstring(xml.encode('utf-8')))
        erros = esquema.error_log
    except:
        return [False]

    #print(erros)
    return erros


def identifica_xml(xml, cria_instancia=False):
    tipos = []

    #
    # A SEFAZ-MG está aceitando arquivos inválidos...
    # entre uma tag e outra, estão injetando o caracter "|"...
    # tenta corrigir isso aqui...
    #
    xml = xml.replace(u'>|<', u'><')
    xml = xml.replace(u'>| <', u'><')
    xml = xml.replace(u'> | <', u'><')
    xml = xml.replace(u'> |<', u'><')

    for tipo in MAPA_ESQUEMAS:
        erros = valida_esquema(xml, tipo)

        if len(erros) == 0:
            #
            # Tenta identificar o tipo exato do evento
            #
            if issubclass(eval(tipo), EnvEvento_100):
                if not tipo == 'EnvEvento_100':
                    #if valida_esquema.evento[0].infEvento.tpEvento.xml in arq:
                    tipos += [tipo]

            elif issubclass(eval(tipo), RetEnvEvento_100):
                if not tipo == 'RetEnvEvento_100':
                    #if valida_esquema.retEvento[0].infEvento.tpEvento.xml in arq:
                    tipos += [tipo]

            elif issubclass(eval(tipo), Evento_100):
                if not tipo == 'Evento_100':
                    #if valida_esquema.infEvento.tpEvento.xml in arq:
                    tipos += [tipo]

            elif issubclass(eval(tipo), RetEvento_100):
                if not tipo == 'RetEvento_100':
                    #if valida_esquema.infEvento.tpEvento.xml in arq:
                    tipos += [tipo]

            elif issubclass(eval(tipo), ProcEvento_100):
                if not tipo == 'ProcEvento_100':
                    #if valida_esquema.evento.infEvento.tpEvento.xml in arq:
                    tipos += [tipo]

            elif issubclass(eval(tipo), NFCe_310):
                if '<mod>55</mod>' in xml:
                    tipo = 'NFe_310'

                tipos += [tipo]

            else:
                tipos += [tipo]

    #print(tipos)

    if cria_instancia:
        if len(tipos):
            instancia = eval(tipos[0] + '()')
            instancia.xml = xml
            return instancia, tipos[0]

        return None, tipos

    return tipos


def valida_assinatura(xml, arq_xml, tipo):
    if tipo not in ('NFe_110', 'CancNFe_107', 'InutNFe_107', 'ProcNFe_110', 'EnviNFe_110',
                    'NFe_200', 'CancNFe_200', 'InutNFe_200', 'ProcNFe_200', 'EnviNFe_200',
                    'NFe_310', 'InutNFe_310', 'ProcNFe_310', 'EnviNFe_310',
                    'CTe_104', 'CancCTe_104', 'InutCTe_104', 'ProcCTe_104', 'EnviCTe_104',
                    'Evento_100', 'EnvEvento_100', 'ProcEvento_100',
                    'EventoCCe_100', 'EnvEventoCCe_100', 'ProcEventoCCe_100',
                    'EventoCancNFe_100', 'EnvEventoCancNFe_100', 'ProcEventoCancNFe_100',
                    'EventoConfRecebimento_100', 'EnvEventoConfRecebimento_100', 'ProcEventoConfRecebimento_100'):
        return True

    assinatura_valida = False
    try:
        c = Certificado()
        assinatura_valida = c.verifica_assinatura_xml(xml)
    except:
        pass

    if not assinatura_valida:
        try:
            assinatura_valida = c.verifica_assinatura_arquivo(arq_xml)
        except:
            pass

    return assinatura_valida


def remove_motivo(nome_arquivo):
    motivos = [
        'codificacao_incorreta',
        'tipo_desconhecido_ou_incorreto',
        'documento_nao_autorizado',
        'assinatura_invalida',
        'arquivo_ilegivel',
        'filial_invalida',
        'falha_na_importacao',
    ]

    for motivo in motivos:
        while motivo + '-' in nome_arquivo:
            nome_arquivo = nome_arquivo.replace(motivo + '-', '')

        while '-' + motivo in nome_arquivo:
            nome_arquivo = nome_arquivo.replace('-' + motivo, '')

    return nome_arquivo


def consulta_sefaz(xml, tipo):
    if tipo not in ('NFe_110', 'ProcNFe_110', 'NFe_200', 'ProcNFe_200', 'NFe_310', 'ProcNFe_310'):
        return '100'

    nfe = eval(tipo + '()')
    nfe.xml = xml

    if tipo in ('ProcNFe_110', 'ProcNFe_200', 'ProcNFe_310'):
        nfe = nfe.NFe

    nfe.monta_chave()

    p = ProcessadorNFe()
    p.salvar_arquivos = False
    #p.versao = unicode(nfe.infNFe.versao.valor)
    p.versao = '3.10'
    p.estado = CODIGO_UF[int(nfe.chave[:2])]
    p.ambiente = nfe.infNFe.ide.tpAmb.valor
    p.certificado.arquivo = os.path.expanduser('~/sped/certificado-portal.pfx')
    p.certificado.senha = 'pctlw-,.hx'

    processo = p.consultar_nota(chave_nfe=nfe.chave)

    return processo.resposta.cStat.valor


def valida_filial(xml, tipo):
    for cnpj in EMPRESAS_CNPJ.keys():
        if '>' + cnpj + '<' in xml:
            return cnpj

    return False


def importa_pasta_email_xml():
    arquivos = os.listdir(HOME_EMAIL_XML)
    arquivos.sort()
    mkdir_p(os.path.join(HOME_XML_VALIDADO))
    mkdir_p(os.path.join(HOME_XML_REJEITADO))
    mkdir_p(os.path.join(HOME_XML_IMPORTADO))

    #print('aqui', arquivos, HOME_EMAIL_XML)
    for nome_arq in arquivos:
        #print('nome do arquivo ', remove_motivo(nome_arq))

        if nome_arq[0] == '.':
            continue

        nome_arquivo = os.path.join(HOME_EMAIL_XML, nome_arq)
        nome_arq = remove_motivo(nome_arq)

        xml = valida_codificacao(nome_arquivo)

        if xml == '':
            shutil.move(nome_arquivo, os.path.join(HOME_XML_REJEITADO, 'codificacao_incorreta-' + nome_arq))
            continue

        xml = correcoes_xml(xml)
        tipo_xml = identifica_xml(xml)

        if not tipo_xml:
            shutil.move(nome_arquivo, os.path.join(HOME_XML_REJEITADO, 'tipo_desconhecido_ou_incorreto-' + nome_arq))
            continue

        if not tipo_xml[0]:
            shutil.move(nome_arquivo, os.path.join(HOME_XML_REJEITADO, 'arquivo_ilegivel-' + nome_arq))
            continue

        tipo_xml = tipo_xml[0]

        if not valida_assinatura(xml, nome_arquivo, tipo_xml):
            shutil.move(nome_arquivo, os.path.join(HOME_XML_REJEITADO, 'assinatura_invalida-' + nome_arq))
            continue

        #
        # Faz a validação no site da SEFAZ autorizadora
        #
        #if not consulta_sefaz(xml, tipo_xml) in ('100', '101', '151', '110', '301', '302'):
            #shutil.move(nome_arquivo, os.path.join(HOME_XML_REJEITADO, 'documento_nao_autorizado-' + nome_arq))
            #continue

        if not valida_filial(xml, tipo_xml):
            shutil.move(nome_arquivo, os.path.join(HOME_XML_REJEITADO, 'filial_invalida-' + nome_arq))
            continue

        shutil.move(nome_arquivo, os.path.join(HOME_XML_VALIDADO, nome_arq))
