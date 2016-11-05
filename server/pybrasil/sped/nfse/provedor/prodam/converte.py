# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from StringIO import StringIO
#from ....base import gera_assinatura, tira_abertura
from ...nfse import *
#from .servico_enviar_lote_rps_envio_v01 import *
#from .servico_enviar_lote_rps_envio_v01 import parseString as parse_lote_rps
#from .servico_consultar_lote_rps_envio_v01 import parseString as parse_lote_nfse
from decimal import Decimal as D
from ....participante import REGIME_TRIBUTARIO_SIMPLES
from .....base import DicionarioBrasil, dicionario_para_xml, xml_para_dicionario, UnicodeBrasil, tira_acentos
from ....base import Signature, gera_assinatura
from .....valor import formata_valor
from pybrasil.sped.nfse.nfse import RPS


def assinatura_extra(nota, certificado):
    assinatura = nota.prestador.im.zfill(8)[:8]
    assinatura += nota.rps.serie.upper().strip().ljust(5)[:5]
    assinatura += unicode(nota.rps.numero).zfill(12)[:12]
    assinatura += nota.rps.data_emissao_iso.replace('-', '')

    if nota.natureza_operacao == NAT_OP_TRIBUTADA_NO_MUNICIPIO:
        assinatura += 'T'
    elif nota.natureza_operacao == NAT_OP_TRIBUTADA_FORA_MUNICIPIO:
        assinatura += 'F'
    elif nota.natureza_operacao == NAT_OP_ISENTA:
        assinatura += 'I'
    elif nota.natureza_operacao == NAT_OP_SUSPENSA_DECISAO_JUDICIAL:
        assinatura += 'J'

    assinatura += 'C' if nota.cancelada else 'N'
    assinatura += 'S' if nota.valor.retido.iss != 0 else 'N'
    assinatura += str(int(D(nota.valor.servico * 100))).zfill(15)
    assinatura += str(int(D(nota.valor.deducao * 100))).zfill(15)
    assinatura += nota.servico_municipio.zfill(5)

    if nota.tomador.tipo_pessoa == 'PF':
        assinatura += '1'
    elif nota.tomador.tipo_pessoa == 'PJ':
        assinatura += '2'
    else:
        assinatura += '3'

    assinatura += nota.tomador.cnpj_cpf_numero.zfill(14)[:14]

    print(assinatura)
    print('344036981    00000000000120160613TNN00000000003000000000000000000007285203792376000174')
    assinatura = certificado.assina_texto(assinatura.upper().encode('utf-8'))
    return assinatura



def gera_rps(lista_notas, numero_lote, certificado=None):
    prestador = lista_notas[0].prestador

    nota = lista_notas[0]

    rps = DicionarioBrasil()
    rps['__xmlns'] = ''
    rps['Assinatura'] = assinatura_extra(nota, certificado)

    chaverps = DicionarioBrasil()
    chaverps['InscricaoPrestador'] = nota.prestador.im or '0'
    chaverps['SerieRPS'] = nota.rps.serie
    chaverps['NumeroRPS'] = str(nota.rps.numero)
    rps['ChaveRPS'] = chaverps

    rps['TipoRPS'] = 'RPS'
    rps['DataEmissao'] = nota.rps.data_emissao_iso
    rps['StatusRPS'] = 'C' if nota.cancelada else 'N'

    if nota.natureza_operacao == NAT_OP_TRIBUTADA_NO_MUNICIPIO:
        rps['TributacaoRPS'] = 'T'
    elif nota.natureza_operacao == NAT_OP_TRIBUTADA_FORA_MUNICIPIO:
        rps['TributacaoRPS'] = 'F'
    elif nota.natureza_operacao == NAT_OP_ISENTA:
        rps['TributacaoRPS'] = 'I'
    elif nota.natureza_operacao == NAT_OP_SUSPENSA_DECISAO_JUDICIAL:
        rps['TributacaoRPS'] = 'J'

    #if nota.prestador.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
        #rps['OpcaoSimples'] = '4'  # SIMPLES Nacional
    #else:
        #rps['OpcaoSimples'] = '0'

    rps['ValorServicos'] = nota.valor.servico or 0
    rps['ValorDeducoes'] = nota.valor.deducao or 0

    rps['ValorPIS'] = nota.valor.retido.pis or None
    rps['ValorCOFINS'] = nota.valor.retido.cofins or None
    rps['ValorINSS'] = nota.valor.retido.inss or None
    rps['ValorIR'] = nota.valor.retido.ir or None
    rps['ValorCSLL'] = nota.valor.retido.csll or None
    rps['CodigoServico'] = nota.servico_municipio.zfill(5) 
    rps['AliquotaServicos'] = nota.valor.al_iss / 100 or 0
    rps['ISSRetido'] = 'true' if nota.valor.retido.iss != 0 else 'false'

    CPFCNPJTomador = DicionarioBrasil()
    if nota.tomador.tipo_pessoa == 'PJ':
        CPFCNPJTomador['CNPJ'] = nota.tomador.cnpj_cpf_numero
    else:
        CPFCNPJTomador['CPF'] = nota.tomador.cnpj_cpf_numero
    rps['CPFCNPJTomador'] = CPFCNPJTomador

    #if nota.natureza_operacao == NAT_OP_TRIBUTADA_NO_MUNICIPIO:
        #rps['InscricaoMunicipalTomador'] = nota.tomador.im_numero or None

    #if nota.tomador.ie:
       #rps['InscricaoEstatualTomador'] = nota.tomador.ie_numero or None

    rps['RazaoSocialTomador'] = nota.tomador.nome.strip()[:75]

    EnderecoTomador = DicionarioBrasil()
    EnderecoTomador['TipoLogradouro'] = 'R'
    EnderecoTomador['Logradouro'] = nota.tomador.endereco.strip()[:50]
    EnderecoTomador['NumeroEndereco'] = nota.tomador.numero.strip()[:10]
    EnderecoTomador['ComplementoEndereco'] = nota.tomador.complemento.strip()[:30]
    EnderecoTomador['Bairro'] = nota.tomador.bairro.strip()[:30]
    EnderecoTomador['Cidade'] = nota.tomador.municipio.codigo_ibge
    EnderecoTomador['UF'] = nota.tomador.estado.uf
    EnderecoTomador['CEP'] = nota.tomador.cep_numero.strip()

    rps['EnderecoTomador'] = EnderecoTomador
    rps['EmailTomador'] = nota.tomador.email.strip()[:75] or None
    rps['Discriminacao'] = nota.descricao.replace('\n', ';').strip()[:2000]

    cabecalho = DicionarioBrasil()
    cabecalhocnpj = DicionarioBrasil()
    cabecalho['__Versao'] = '1'
    cabecalho['__xmlns'] = ''
    cabecalho['CPFCNPJRemetente'] = cabecalhocnpj
    cabecalhocnpj['CNPJ'] = nota.prestador.cnpj_cpf_numero
    cabecalho['transacao'] = 'false'
    cabecalho['dtInicio'] = nota.rps.data_emissao_iso
    cabecalho['dtFim'] = nota.rps.data_emissao_iso
    cabecalho['QtdRPS'] = 1
    cabecalho['ValorTotalServicos'] = nota.valor.servico or 0
    cabecalho['ValorTotalDeducoes'] = nota.valor.deducao or 0

    raiz = DicionarioBrasil()
    raiz['PedidoEnvioLoteRPS'] = DicionarioBrasil()
    enviarrpsenvio = raiz.PedidoEnvioLoteRPS
    enviarrpsenvio['__xmlns:xsd'] = 'http://www.w3.org/2001/XMLSchema'
    enviarrpsenvio['__xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
    enviarrpsenvio['__xmlns'] = 'http://www.prefeitura.sp.gov.br/nfe'
    enviarrpsenvio['Cabecalho'] = cabecalho
    enviarrpsenvio['RPS'] = rps
    enviarrpsenvio['Signature'] = gera_assinatura(URI='', ignora_uri=True)

    xml_a_assinar = tira_acentos(raiz.como_xml_em_texto)
    certificado.ignora_doctype = True
    rps_assinado = certificado.assina_xml(xml_a_assinar)
    certificado.ignora_doctype = False

    return rps_assinado


def gera_consulta_situacao_rps(protocolo, prestador):
    raiz = DicionarioBrasil()
    raiz['ConsultarSituacaoLoteRpsEnvio'] = DicionarioBrasil()
    consultarps = raiz.ConsultarSituacaoLoteRpsEnvio
    consultarps['__xmlns:e'] = 'http://www.betha.com.br/e-nota-contribuinte-ws'
    consultarps['Prestador'] = DicionarioBrasil()
    consultarps.Prestador['Cnpj'] = prestador.cnpj_cpf_numero
    consultarps['Protocolo'] = protocolo

    return raiz.como_xml_em_texto


def gera_consulta_rps(protocolo, prestador):
    raiz = DicionarioBrasil()
    raiz['ConsultarLoteRpsEnvio'] = DicionarioBrasil()
    consultarps = raiz.ConsultarLoteRpsEnvio
    consultarps['__xmlns:e'] = 'http://www.betha.com.br/e-nota-contribuinte-ws'
    consultarps['Prestador'] = DicionarioBrasil()
    consultarps.Prestador['Cnpj'] = prestador.cnpj_cpf_numero
    consultarps['Protocolo'] = protocolo

    return raiz.como_xml_em_texto


def le_envio_lote_rps(xml):
    envio_lote_rps = xml_para_dicionario(xml)
    lote_rps = envio_lote_rps.EnviarLoteRpsEnvio.LoteRps
    numero_lote = lote_rps.NumeroLote

    if isinstance(lote_rps.ListaRps, DicionarioBrasil):
        lote_rps.ListaRps = [lote_rps.ListaRps]

    lista_notas = []
    for item_rps in lote_rps.ListaRps:
        rps = item_rps.Rps

        nota = NFSe()
        Prestador = rps.InfRps.Prestador
        Tomador = rps.InfRps.Tomador

        #
        # Prestador
        #
        nota.prestador.cnpj_cpf = unicode(getattr(Prestador, 'Cnpj', '') or '') or unicode(getattr(Prestador, 'Cpf', '') or '')
        nota.prestador.im = unicode(getattr(Prestador, 'InscricaoMunicipal', '') or '')

        if getattr(rps.InfRps, 'OptanteSimplesNacional', 2) == 1:
            nota.prestador.regime_tributario = REGIME_TRIBUTARIO_SIMPLES

        nota.prestador.incentivador_cultural = getattr(rps.InfRps, 'IncentivadorCultural', 2) == 1

        #
        # Tomador
        #
        if hasattr(Tomador, 'IdentificacaoTomador') and hasattr(Tomador.IdentificacaoTomador, 'CpfCnpj'):
            nota.tomador.cnpj_cpf = unicode(getattr(Tomador.IdentificacaoTomador.CpfCnpj, 'Cnpj', '') or '') or unicode(getattr(Tomador.IdentificacaoTomador.CpfCnpj, 'Cpf', '') or '')

        nota.tomador.nome = unicode(getattr(Tomador, 'RazaoSocial', '') or '')

        if hasattr(Tomador, 'Endereco'):
            nota.tomador.endereco = unicode(getattr(Tomador.Endereco, 'Endereco', '') or '')
            nota.tomador.numero = unicode(getattr(Tomador.Endereco, 'Numero', '') or '')
            nota.tomador.complemento = unicode(getattr(Tomador.Endereco, 'Complemento', '') or '')
            nota.tomador.bairro = unicode(getattr(Tomador.Endereco, 'Bairro', ''))
            nota.tomador.estado = unicode(getattr(Tomador.Endereco, 'Uf', ''))
            nota.tomador.municipio = unicode(getattr(Tomador.Endereco, 'CodigoMunicipio', '')).zfill(7)
            nota.tomador.cep = unicode(getattr(Tomador.Endereco, 'Cep', ''))

        if hasattr(Tomador, 'Contato'):
            nota.tomador.fone = unicode(getattr(Tomador.Contato, 'Telefone', ''))
            nota.tomador.email = unicode(getattr(Tomador.Contato, 'Email', ''))

        #
        # Dados do RPS/Nota
        #
        if hasattr(rps.InfRps, 'IdentificacaoRps'):
            nota.rps.numero = getattr(rps.InfRps.IdentificacaoRps, 'Numero', 0)
            nota.rps.serie = unicode(getattr(rps.InfRps.IdentificacaoRps, 'Serie', ''))
            nota.rps.tipo = (getattr(rps.InfRps.IdentificacaoRps, 'Tipo', UnicodeBrasil('1')).inteiro - 1) or 0

        nota.rps.data_hora_emissao = getattr(rps.InfRps, 'DataEmissao', None)
        nota.natureza_operacao = (getattr(rps.InfRps, 'NaturezaOperacao', UnicodeBrasil('1')).inteiro - 1) or 0
        #rps.InfRps.RegimeEspecialTributacao =
        nota.cancelada = getattr(rps.InfRps, 'Status', '2') == '1'
        #rps.InfRps.OutrasInformacoes =

        if hasattr(rps.InfRps, 'RpsSubstituido'):
            nota.nfse_substituida.numero = getattr(rps.InfRps.RpsSubstituido, 'Numero', UnicodeBrasil('0')).inteiro
            nota.nfse_substituida.serie = unicode(getattr(rps.InfRps.RpsSubstituido, 'Serie', ''))
            nota.nfse_substituida.tipo = (getattr(rps.InfRps.RpsSubstituido, 'Tipo', UnicodeBrasil('1')).inteiro - 1) or 0

        #
        # Serviço
        #
        Servico = rps.InfRps.Servico
        nota.valor.servico = D(getattr(Servico.Valores, 'ValorServicos', '0'))
        nota.valor.deducao = D(getattr(Servico.Valores, 'ValorDeducoes', '0'))
        nota.valor.desconto_incondicionado = D(getattr(Servico.Valores, 'DescontoIncondicionado', '0'))
        nota.valor.bc_iss = D(getattr(Servico.Valores, 'BaseCalculo', '0'))
        nota.valor.al_iss = D(getattr(Servico.Valores, 'Aliquota', '0')) * 100
        nota.valor.vr_iss = D(getattr(Servico.Valores, 'ValorIss', '0'))
        nota.valor.retido.iss = D(getattr(Servico.Valores, 'ValorIssRetido', '0'))
        nota.valor.retido.pis = D(getattr(Servico.Valores, 'ValorPis', '0'))
        nota.valor.retido.cofins = D(getattr(Servico.Valores, 'ValorCofins', '0'))
        nota.valor.retido.inss = D(getattr(Servico.Valores, 'ValorInss', '0'))
        nota.valor.retido.ir = D(getattr(Servico.Valores, 'ValorIr', '0'))
        nota.valor.retido.csll = D(getattr(Servico.Valores, 'ValorCsll', '0'))
        nota.valor.retido.outras = D(getattr(Servico.Valores, 'OutrasRetencoes', '0'))
        nota.valor.desconto_condicionado = D(getattr(Servico.Valores, 'DescontoCondicionado', '0'))
        nota.valor.liquido = D(getattr(Servico.Valores, 'ValorLiquidoNfse', '0'))

        nota.servico = unicode(getattr(Servico, 'ItemListaServico', '') or '')
        #rps.InfRps.Servico.CodigoCnae = nota.servico.codigo
        #rps.InfRps.Servico.CodigoTributacaoMunicipio = nota.servico.codigo
        nota.descricao = unicode(getattr(Servico, 'Discriminacao', '') or '')
        nota.municipio_fato_gerador = unicode(getattr(Servico, 'CodigoMunicipio', '') or '').zfill(7)

        lista_notas.append(nota)

    return lista_notas, numero_lote

def gera_cancelamento_nota(nota, certificado):
    raiz = DicionarioBrasil()
    raiz['CancelarNfseEnvio'] = DicionarioBrasil()
    cancelanota = raiz.CancelarNfseEnvio
    cancelanota['__xmlns:e'] = 'http://www.betha.com.br/e-nota-contribuinte-ws'
    cancelanota['Pedido'] = DicionarioBrasil()
    pedcanc = cancelanota.Pedido
    pedcanc['InfPedidoCancelamento'] = DicionarioBrasil()
    pedcanc.InfPedidoCancelamento['__Id'] = 'L' + str(nota.numero)
    pedcanc.InfPedidoCancelamento['IdentificacaoNfse'] = DicionarioBrasil()
    pedcanc.InfPedidoCancelamento.IdentificacaoNfse['Numero'] = str(nota.numero)
    pedcanc.InfPedidoCancelamento.IdentificacaoNfse['Cnpj'] = nota.prestador.cnpj_cpf_numero
    pedcanc.InfPedidoCancelamento.IdentificacaoNfse['InscricaoMunicipal'] = nota.prestador.im or '0'
    pedcanc.InfPedidoCancelamento.IdentificacaoNfse['CodigoMunicipio'] = nota.prestador.municipio.codigo_ibge
    pedcanc.InfPedidoCancelamento['CodigoCancelamento'] = '1'

    assinatura = gera_assinatura(URI='#' + pedcanc.InfPedidoCancelamento.__Id)
    pedcanc['Signature'] = assinatura

    if certificado:
        certificado.doctype = '<!DOCTYPE Pedido [<!ATTLIST InfPedidoCancelamento Id ID #IMPLIED>]>'
        raiz = certificado.assina_xml(raiz)
        #print(raiz.como_xml_em_texto)

    return raiz.como_xml_em_texto
