# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_cancelamento_nota
from ....base import ConexaoWebService

conexao = ConexaoWebService()
conexao.servidor = 'isscuritiba.curitiba.pr.gov.br'
conexao.codificacao = 'ascii'
conexao.namespace_soap = 'http://schemas.xmlsoap.org/soap/envelope/'

#MODELO_SOAP_ENVELOPE_HOMOLOGACAO = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><TesteEnvioLoteRPSRequest xmlns="http://www.blumenau.sc.gov.br/nfse"><VersaoSchema>1</VersaoSchema><MensagemXML>{body}</MensagemXML></TesteEnvioLoteRPSRequest></soap:Body></soap:Envelope>'

#
# Muito cuidado aqui, essa PRODAM faz o webservice
# em .NET, ou seja, padrão XML não existe...
# Se o Envelope SOAP não for enviado com as quebras de linha
# e os espaços de identação, o webservice não processa a requisição...
#

MODELO_SOAP_ENVELOPE_CANCELAMENTO = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <CancelarLoteRps xmlns="http://www.e-governeapps2.com.br/">
    {body}
    </CancelarLoteRps>
  </soap:Body>
</soap:Envelope>'''


def cancela_nota(nfse, certificado, producao=False):
    cancelamento = gera_cancelamento_nota(nfse, certificado)
    
    print(cancelamento)

    conexao.certificado = certificado
    conexao.url = 'Iss.NfseWebService/nfsews.asmx'
    conexao.certificado = certificado
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }
    conexao.metodo = 'CancelarLoteRpsEnvio'
    conexao.modelo_header['SOAPAction'] = 'http://www.e-governeapps2.com.br/RecepcionarLoteRps'
    conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE_CANCELAMENTO

    conexao.conectar_servico(conteudo=cancelamento)

    return conexao.resposta.Envelope.Body
