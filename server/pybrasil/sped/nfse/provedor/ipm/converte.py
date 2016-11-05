# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from StringIO import StringIO
#from ....base import gera_assinatura, tira_abertura
from ...nfse import *
#from .servico_enviar_lote_rps_envio_v01 import *
#from .servico_enviar_lote_rps_envio_v01 import parseString as parse_lote_rps
#from .servico_consultar_lote_rps_envio_v01 import parseString as parse_lote_nfse
#from decimal import Decimal as D
from ....participante import REGIME_TRIBUTARIO_SIMPLES
from .....base import DicionarioBrasil, dicionario_para_xml, xml_para_dicionario, UnicodeBrasil, tira_acentos
from ....base import Signature, gera_assinatura
from .....valor import formata_valor


def gera_rps(lista_notas, numero_lote, certificado=None):
    prestador = lista_notas[0].prestador

    nota = lista_notas[0]
    rps = DicionarioBrasil()
    rps['nro_recibo_provisorio'] = str(nota.rps.numero)
    rps['serie_recibo_provisorio'] = nota.rps.serie
    rps['data_emissao_recibo_provisorio'] = nota.rps.data_emissao_formatada
    rps['hora_emissao_recibo_provisorio'] = nota.rps.hora_emissao_formatada

    nf = DicionarioBrasil()
    nf['valor_total'] = formata_valor(nota.valor.servico or 0).replace('.', '')
    nf['valor_desconto'] = formata_valor(nota.valor.desconto_incondicionado or 0).replace('.', '')
    nf['valor_ir'] = formata_valor(nota.valor.retido.ir or 0).replace('.', '')
    nf['valor_inss'] =  formata_valor(nota.valor.retido.inss or 0).replace('.', '')
    nf['valor_contribuicao_social'] = formata_valor(nota.valor.retido.csll or 0).replace('.', '')
    #
    # RPS aqui significa Retenção da Previdência Social
    #
    #nf['valor_rps'] = formata_valor(nota.valor.retido.inss or 0)
    nf['valor_rps'] = formata_valor(0).replace('.', '')
    nf['valor_pis'] = formata_valor(nota.valor.retido.pis or 0).replace('.', '')
    nf['valor_cofins'] = formata_valor(nota.valor.retido.cofins or 0).replace('.', '')

    #
    # Prestador
    #
    prestador = DicionarioBrasil()
    prestador['cpfcnpj'] = nota.prestador.cnpj_cpf_numero
    prestador['cidade'] = nota.prestador.municipio.codigo_siafi or None

    #
    # Tomador
    #
    tomador = DicionarioBrasil()
    #tomador['endereco_informado'] = '1'

    if nota.tomador.tipo_pessoa == 'PF':
        tomador['tipo'] = 'F'
    else:
        tomador['tipo'] = 'J'

    #tomador['identificador'] = 'numero passaporte estrangeiro'
    tomador['estado'] = nota.tomador.estado.uf
    #tomador['pais'] = nota.tomador.estado.uf
    tomador['cpfcnpj'] = nota.tomador.cnpj_cpf_numero
    #tomador['ie'] = nota.tomador.cnpj_cpf_numero
    tomador['nome_razao_social'] = nota.tomador.nome.strip()
    #tomador['sobrenome_nome_fantasia'] = nota.tomador.nome.strip()
    tomador['logradouro'] = nota.tomador.endereco.strip()[:70]
    #tomador['email'] = nota.tomador.email.strip() or None
    tomador['numero_residencia'] = nota.tomador.numero.strip()[:8]
    tomador['complemento'] = nota.tomador.complemento.strip()[:50] or None
    #tomador['ponto_referencia'] = nota.tomador.nome.strip()
    tomador['bairro'] = nota.tomador.bairro.strip()[:30] or None
    tomador['cidade'] = nota.tomador.municipio.codigo_siafi or None
    tomador['cep'] = nota.tomador.cep_numero.strip() or None

    servico = DicionarioBrasil()
    servico['tributa_municipio_prestador'] = 'S' if nota.natureza_operacao == NAT_OP_TRIBUTADA_NO_MUNICIPIO else 'N'
    #servico['tributa_municipio_prestador'] = 'N' # if nota.natureza_operacao == NAT_OP_TRIBUTADA_NO_MUNICIPIO else 'N'

    if nota.municipio_fato_gerador and nota.municipio_fato_gerador.codigo_siafi:
        servico['codigo_local_prestacao_servico'] = nota.municipio_fato_gerador.codigo_siafi
    elif nota.natureza_operacao == NAT_OP_TRIBUTADA_FORA_MUNICIPIO:
        servico['codigo_local_prestacao_servico'] = nota.tomador.municipio.codigo_siafi
    else:
        servico['codigo_local_prestacao_servico'] = nota.prestador.municipio.codigo_siafi

    #
    # Prefeitura de Concórdia exige os campos abaixo
    #
    if nota.prestador.municipio.codigo_siafi == '8083':
        servico['unidade_codigo'] = '1'
        servico['unidade_quantidade'] = '1'
        servico['unidade_valor_unitario'] = formata_valor(nota.valor.bc_iss or 0).replace('.', '')

    servico['codigo_item_lista_servico'] = nota.servico.codigo.zfill(4)
    servico['descritivo'] = nota.descricao.replace('\n', ';').strip()[:1000]
    servico['aliquota_item_lista_servico'] = formata_valor(nota.valor.al_iss or 0).replace('.', '')

    if nota.valor.retido.iss > 0:
        #
        # Para órgão público, vai 1, para particular, 2
        #
        servico['situacao_tributaria'] = '2'
    else:
        servico['situacao_tributaria'] = '0'

    servico['valor_tributavel'] = formata_valor(nota.valor.bc_iss or 0).replace('.', '')
    #servico['valor_deducao'] = None
    servico['valor_issrf'] = formata_valor(nota.valor.retido.iss or 0).replace('.', '')

    raiz = DicionarioBrasil()
    raiz['nfse'] = DicionarioBrasil()
    raiz.nfse['identificador'] = numero_lote
    #raiz.nfse['rps'] = rps
    raiz.nfse['nf'] = nf
    raiz.nfse['prestador'] = prestador
    raiz.nfse['tomador'] = tomador
    raiz.nfse['itens'] = DicionarioBrasil()
    raiz.nfse.itens['lista'] = servico

    return raiz.como_xml_em_texto


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
        print(raiz.como_xml_em_texto)

    return raiz.como_xml_em_texto
