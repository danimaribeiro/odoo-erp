# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from dateutil.relativedelta import relativedelta
from ...base import DicionarioBrasil, dicionario_para_xml, xml_para_dicionario
from ...sped.base import ConexaoWebService
from ...data import hoje, formata_data, parse_datetime
from ...valor.decimal import Decimal as D
from .constantes import *


class ConexaoWebServiceBancoCentral(ConexaoWebService):
    def __init__(self, *args, **kwargs):
        super(ConexaoWebServiceBancoCentral, self).__init__(*args, **kwargs)
        self.servidor = b'www3.bcb.gov.br'
        #self.url = b'sgspub/JSP/sgsgeral/FachadaWSSGS.wsdl'
        self.url = b'wssgs/services/FachadaWSSGS'
        self.modelo_soap_envelope = b'<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:apachesoap="http://xml.apache.org/xml-soap" xmlns:impl="https://www3.bcb.gov.br/wssgs/services/FachadaWSSGS" xmlns:intf="https://www3.bcb.gov.br/wssgs/services/FachadaWSSGS" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:tns1="http://DefaultNamespace" xmlns:tns2="http://comum.ws.casosdeuso.sgs.pec.bcb.gov.br" xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/" xmlns:wsdlsoap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><SOAP-ENV:Body>{body}</SOAP-ENV:Body></SOAP-ENV:Envelope>'
        self.modelo_header = {
            b'content-type': b'application/soap+xml; charset=utf-8',
            b'Accept': b'application/soap+xml; charset=utf-8',
            b'SOAPAction': b'',
        }


def _get_valor(certificado, data=hoje(), indice=WS_BC_DOLAR):
    ws = ConexaoWebServiceBancoCentral()
    ws.metodo = b'getValor'
    ws.acao = b''
    ws.certificado = certificado
    
    #
    # Não atualiza os valores no sábado e domingo, pega
    # o da sexta-feira anterior
    #
    data = parse_datetime(data).date()
    if data.weekday() == 5:
        data += relativedelta(days=-1)
    elif data.weekday() == 6:
        data += relativedelta(days=-2)
    
    mensagem = b'<mns:getValor xmlns:mns="http://publico.ws.casosdeuso.sgs.pec.bcb.gov.br" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><in0 xsi:type="xsd:long">{indice}</in0><in1 xsi:type="xsd:string">{data}</in1></mns:getValor>'
    
    dados = {
        'indice': indice,
        'data': formata_data(data),
    }
    ws.conectar_servico(conteudo=mensagem.format(**dados))
    
    valor = D(0)
    
    #print()
    #print(ws.xml_resposta)
    #print()
    if 'getValorResponse' in ws.xml_resposta and 'multiRef' in ws.xml_resposta:
        valor = ws.resposta.Envelope.Body.multiRef._texto
        valor = D(valor)
    
    return valor


def cotacao_dolar(certificado, data=hoje()):
    return _get_valor(certificado, data=data, indice=WS_BC_DOLAR)

def cotacao_euro(certificado, data=hoje()):
    return _get_valor(certificado, data=data, indice=WS_BC_EURO_VENDA)

def cotacao_igpm(certificado, data=hoje()):
    return _get_valor(certificado, data=data, indice=WS_BC_IGPM)


def _get_valores_series(certificado, data_inicial=hoje(), data_final=hoje(), indice=WS_BC_DOLAR):
    ws = ConexaoWebServiceBancoCentral()
    ws.metodo = b'getValoresSeriesXML'
    ws.acao = b''
    ws.certificado = certificado
    
    mensagem = b'<mns:getValor xmlns:mns="http://publico.ws.casosdeuso.sgs.pec.bcb.gov.br" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><in0 xsi:type="xsd:long">{indice}</in0><in1 xsi:type="xsd:string">{data}</in1></mns:getValor>'
    mensagem = b'<mns:getValoresSeriesXML xmlns:mns="http://publico.ws.casosdeuso.sgs.pec.bcb.gov.br" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><in0 xsi:type="soapenc:Array" soapenc:arrayType="xsd:long[1]"><item soapenc:position="[0]" xsi:type="xsd:long">{indice}</item></in0><in1 soapenc:position="[1]" xsi:type="xsd:string">{data_inicial}</in1><in2 soapenc:position="[1]" xsi:type="xsd:string">{data_final}</in2></mns:getValoresSeriesXML>'
    
    dados = {
        'indice': indice,
        'data_inicial': formata_data(data_inicial),
        'data_final': formata_data(data_final),
    }
    ws.conectar_servico(conteudo=mensagem.format(**dados))
    
    valores = {}

    #
    # Tratamento especial do XML que vem embutido na resposta
    #

    #print()
    #print(ws.xml_resposta)
    #print()
    if 'getValoresSeriesXMLResponse' in ws.xml_resposta and 'getValoresSeriesXMLReturn' in ws.xml_resposta:
        xml_itens = xml_para_dicionario(ws.resposta.Envelope.Body.getValoresSeriesXMLResponse.getValoresSeriesXMLReturn._texto)

        for item in xml_itens.SERIES.SERIE.ITEM:
            valores[item.DATA] = D(item.VALOR)
    
    return valores

def cotacao_dolar_periodo(certificado, data_inicial=hoje(), data_final=hoje()):
    return _get_valores_series(certificado, data_inicial=data_inicial, data_final=data_final, indice=WS_BC_DOLAR)

def cotacao_euro_periodo(certificado, data_inicial=hoje(), data_final=hoje()):
    return _get_valores_series(certificado, data_inicial=data_inicial, data_final=data_final, indice=WS_BC_EURO_VENDA)

def cotacao_igpm_periodo(certificado, data_inicial=hoje(), data_final=hoje()):
    return _get_valores_series(certificado, data_inicial=data_inicial, data_final=data_final, indice=WS_BC_IGPM)


   
def teste():
    import pybrasil
    c = pybrasil.sped.base.certificado.Certificado()
    c.arquivo = b'/home/ari/Downloads/ASPSEG.pfx'
    c.senha = b'aspseg@2015'
    
    #print(cotacao_dolar(c, data='01/11/2014'))
    #print(cotacao_dolar(c, data='02/11/2014'))
    #print(cotacao_dolar(c, data='14/11/2014'))

    #print(cotacao_euro(c, data='01/11/2014'))
    #print(cotacao_euro(c, data='02/11/2014'))
    #print(cotacao_euro(c, data='14/11/2014'))
    
    print(cotacao_igpm_periodo(c, '01/01/2014', '13/11/2014'))
    return cotacao_igpm_periodo(c, '01/01/2014', '13/11/2014')