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
from .....base import DicionarioBrasil, xml_para_dicionario, UnicodeBrasil, tira_acentos
from sped.constante_tributaria import *
from .retorno_joinville import  RETORNO_JLLE, RPS
from .....inscricao import formata_cnpj

def gera_rps(lista_notas, numero_lote, certificado=None):
    prestador = lista_notas[0].prestador

    lote = DicionarioBrasil()
    envialote = lote
    envialote['__xmlns'] = 'http://www.nfem.joinville.sc.gov.br'
    envialote['__xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
    #envialote['__xsi:schemaLocation'] = 'http://www.nfem.joinville.sc.gov.br rps_1.0.xsd'
    lote['versao'] = '1.0'
    lote['numero'] =  str(numero_lote)
    lote['tipo'] = '1'

    Prestador = DicionarioBrasil()
    Prestador['documento'] = prestador.cnpj_cpf_numero
    Prestador['razao_social'] = prestador.nome[:60] or ''
    lote['prestador'] = Prestador
    lote['rps'] = []

    for nota in lista_notas:
        rps = DicionarioBrasil()
        rps['numero'] = str(nota.rps.numero)
        rps['serie'] = nota.rps.serie
        rps['data'] = nota.rps.data_emissao_iso
        if nota.cancelada:
            rps['operacao'] = 'C'
        else:
            rps['operacao'] = 'I'

        rps['tipo'] = '1'

        Tomador = DicionarioBrasil()
        if nota.tomador.tipo_pessoa == 'PJ':
            Tomador['documento'] = nota.tomador.cnpj_cpf_numero
        else:
            Tomador['documento'] = nota.tomador.cnpj_cpf_numero
        Tomador['nome'] = nota.tomador.nome.strip()[:60]

        if nota.natureza_operacao == NAT_OP_TRIBUTADA_NO_MUNICIPIO:
            Tomador['inscricao_municipal'] = nota.tomador.im_numero or None

        Tomador['email'] = nota.tomador.email.strip()[:75] or None
        Tomador['situacao_especial'] = '0'
        Tomador['cep'] = nota.tomador.cep_numero.strip() or ''
        Tomador['endereco'] = nota.tomador.endereco.strip()[:150]
        Tomador['numero'] = nota.tomador.numero.strip()[:10]

        if nota.tomador.complemento:
            Tomador['complemento'] = nota.tomador.complemento.strip()[:100]

        Tomador['bairro'] = nota.tomador.bairro.strip()[:50]
        if not nota.natureza_operacao == NAT_OP_TRIBUTADA_NO_MUNICIPIO:
            Tomador['cidade'] = nota.tomador.municipio.nome
            Tomador['estado'] = nota.tomador.estado.uf
        rps['tomador'] = Tomador

        rps['descricao_servicos'] = nota.descricao.replace('\n', ';').strip()[:8000]
        rps['destino_servico'] = '0'
        rps['valor_total'] = nota.valor.servico or 0
        rps['valor_deducao'] = nota.valor.deducao or 0
        codigo = nota.servico.codigo_formatado

        if codigo.startswith('0'):
            codigo = codigo[1:]

        rps['servico'] = codigo

        if nota.natureza_operacao == NAT_OP_TRIBUTADA_FORA_MUNICIPIO:
            rps['local_servico'] = nota.tomador.municipio.nome[:50]

        rps['aliquota_iss'] = nota.valor.al_iss or 0
        rps['valor_iss'] = nota.valor.vr_iss or 0
        rps['iss_retido'] = '1' if nota.valor.retido.iss != 0 else '0'
        rps['valor_irrf'] = nota.valor.retido.ir or 0
        rps['valor_inss'] = nota.valor.retido.inss or 0
        rps['valor_pis'] = nota.valor.retido.pis or 0
        rps['valor_cofins'] = nota.valor.retido.cofins or 0
        rps['valor_csll'] = nota.valor.retido.csll or 0
        lote.rps.append(rps)


    raiz = DicionarioBrasil()
    raiz['lote'] = lote
    xml = tira_acentos(raiz.como_xml_em_texto)
    nfse = '<?xml version="1.0" encoding="utf-8"?>' + xml

    return nfse

def le_envio_lote_rps(xml):
    lote_rps = xml_para_dicionario(xml)
    print(lote_rps.como_xml_em_texto)

    notas = []
    numero = 0
    if '<rps>' not in xml:
        return notas

    if not isinstance(lote_rps.lote.rps, (list, tuple)):
        rps = lote_rps.lote.rps
        nota = RETORNO_JLLE()
        nota.numero_lote = lote_rps.lote.numero or 0
        nota.tipo = lote_rps.lote.tipo or 0
        nota.data_envio = lote_rps.lote.data_envio
        nota.data_processamento = lote_rps.lote.data_processamento
        nota.status = lote_rps.lote.status or 1
        nota.descricao_status = lote_rps.lote.status or ''
        nota.observacao = lote_rps.lote.observacao or ''

        if '<prestador>' in xml:
            nota.documento = formata_cnpj(lote_rps.lote.prestador.documento) or 0
            nota.razao_social = lote_rps.lote.prestador.razao_social or ''

        item = RPS()
        if numero != rps.numero:
            nota.rps.append(item)
            item.numero = rps.numero or 0
            numero = rps.numero or 0
            item.serie = rps.serie or ''
            item.nfem_numero = rps.nfem_numero or 0
            item.nfem_codigo_verificacao =  rps.nfem_codigo_verificacao or ''

        notas.append(nota)
    else:
        for rps in lote_rps.lote.rps:
            nota = RETORNO_JLLE()
            nota.numero_lote = lote_rps.lote.numero or 0
            nota.tipo = lote_rps.lote.tipo or 0
            nota.data_envio = lote_rps.lote.data_envio
            nota.data_processamento = lote_rps.lote.data_processamento
            nota.status = lote_rps.lote.status or 1
            nota.descricao_status = lote_rps.lote.status or ''
            nota.observacao = lote_rps.lote.observacao or ''

            if '<prestador>' in xml:
                nota.documento = formata_cnpj(lote_rps.lote.prestador.documento) or 0
                nota.razao_social = lote_rps.lote.prestador.razao_social or ''

            item = RPS()
            if numero != rps.numero:
                nota.rps.append(item)
                item.numero = rps.numero or 0
                numero = rps.numero or 0
                item.serie = rps.serie or ''
                item.nfem_numero = rps.nfem_numero or 0
                item.nfem_codigo_verificacao =  rps.nfem_codigo_verificacao or ''

            notas.append(nota)

    return notas
