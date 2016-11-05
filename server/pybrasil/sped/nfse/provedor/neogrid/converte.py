# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from StringIO import StringIO
#from ....base import gera_assinatura, tira_abertura
from ...nfse import *
#from .servico_enviar_g2ka_envio_v01 import *
#from .servico_enviar_g2ka_envio_v01 import parseString as parse_g2ka
#from .servico_consultar_g2ka_envio_v01 import parseString as parse_lote_nfse
#from decimal import Decimal as D
from ....participante import REGIME_TRIBUTARIO_SIMPLES
from .....base import DicionarioBrasil, dicionario_para_xml, xml_para_dicionario, UnicodeBrasil, tira_acentos
from ....base import Signature, gera_assinatura


def gera_rps(lista_notas, numero_lote, certificado=None):
    prestador = lista_notas[0].prestador
    nota = lista_notas[0]

    print('entrou aqui')

    g2ka = DicionarioBrasil()
    g2ka['__xmlns:g'] = 'http://www.g2ka.com.br'
    g2ka['__versao'] = '1'

    g2ka['Identificador'] = nota.prestador.municipio.codigo_ibge
    g2ka['RPS'] = DicionarioBrasil()

    g2ka.RPS['A'] = DicionarioBrasil()
    g2ka.RPS.A['Versao'] = '1'
    g2ka.RPS.A['Id'] = numero_lote

    g2ka.RPS['B'] = DicionarioBrasil()
    g2ka.RPS.B['Numero'] = str(nota.rps.numero)
    g2ka.RPS.B['Serie'] = 'RPS'
    g2ka.RPS.B['Tipo'] = '1'

    g2ka.RPS['C'] = DicionarioBrasil()
    g2ka.RPS.C['DataEmissao'] = nota.rps.data_hora_emissao.isoformat()
    g2ka.RPS.C['Competencia'] = nota.rps.data_hora_emissao.isoformat()

    g2ka.RPS['D'] = DicionarioBrasil()
    g2ka.RPS.D['NaturezaOperacao'] = nota.natureza_operacao

    g2ka.RPS['E'] = DicionarioBrasil()
    g2ka.RPS.E['RegimeEspecialTributacao'] = '1'

    g2ka.RPS['F'] = DicionarioBrasil()
    g2ka.RPS.F['OptanteSimplesNacional'] = '1' if nota.prestador.regime_tributario == REGIME_TRIBUTARIO_SIMPLES else '2'

    g2ka.RPS['G'] = DicionarioBrasil()
    g2ka.RPS.G['IncentivadorCultural'] = '2'
    g2ka.RPS.G['IncentivoFiscal'] = '2'

    g2ka.RPS['H'] = DicionarioBrasil()
    g2ka.RPS.H['Status'] = '2' if nota.cancelada else '1'
    g2ka.RPS.H['MotivoCancelamento'] = None

    #if nota.nfse_substituida.numero != 0:
        #g2ka.RPS['I'] = DicionarioBrasil()
        #g2ka.RPS.A['RPSSubst'] = DicionarioBrasil()
        #rps.RPSSubst['nRPSSubst'] = nota.nfse_substituida.numero
        #rps.RPSSubst['nSerieSubst'] = 'RPS'
        #rps.RPSSubst['tpRPSSubst'] = '1'

    #
    # Serviço
    #
    g2ka.RPS['J'] = DicionarioBrasil()
    g2ka.RPS.J['ItemListaServico'] = nota.servico.codigo.zfill(4)
    g2ka.RPS.J['CodigoCnae'] = None
    g2ka.RPS.J['CodigoTributacaoMunicipio'] = None
    g2ka.RPS.J['Descricao'] = nota.descricao.replace('\n', ';').strip()
    g2ka.RPS.J['CodigoMunicipio'] = nota.prestador.municipio.codigo_ibge
    g2ka.RPS.J['ExigibilidadeISS'] = '1'

    #
    # Valores
    #
    g2ka.RPS['K'] = DicionarioBrasil()
    g2ka.RPS.K['ValorServicos'] = nota.valor.servico
    g2ka.RPS.K['ValorDeducoes'] = nota.valor.deducao or '0.00'
    g2ka.RPS.K['ValorPis'] = nota.valor.retido.pis or '0.00'
    g2ka.RPS.K['ValorCofins'] = nota.valor.retido.cofins or '0.00'
    g2ka.RPS.K['ValorInss'] = nota.valor.retido.inss or '0.00'
    g2ka.RPS.K['ValorIr'] = nota.valor.retido.ir or '0.00'
    g2ka.RPS.K['ValorCsll'] = nota.valor.retido.csll or '0.00'

    if nota.prestador.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
        g2ka.RPS.K['IssRetido'] = '2'
        g2ka.RPS.K['ValorIss'] = '0.00'
        g2ka.RPS.K['ValorIssRetido'] = '0.00'
        g2ka.RPS.K['OutrasRetencoes'] = nota.valor.retido.outras or '0.00'
        g2ka.RPS.K['BaseCalculo'] = '0.00'
        g2ka.RPS.K['Aliquota'] = '0.00'

    else:
        g2ka.RPS.K['IssRetido'] = '2'
        g2ka.RPS.K['ValorIss'] = nota.valor.vr_iss or '0.00'
        g2ka.RPS.K['ValorIssRetido'] = nota.valor.retido.iss or '0.00'
        g2ka.RPS.K['OutrasRetencoes'] = nota.valor.retido.outras or '0.00'
        g2ka.RPS.K['BaseCalculo'] = nota.valor.bc_iss or '0.00'
        g2ka.RPS.K['Aliquota'] = nota.valor.al_iss or '0.00'

    g2ka.RPS.K['ValorLiquidoNfse'] = nota.valor.liquido or '0.00'
    g2ka.RPS.K['DescontoIncondicionado'] = nota.valor.desconto_incondicionado or '0.00'
    g2ka.RPS.K['DescontoCondicionado'] = nota.valor.desconto_condicionado or '0.00'


    #
    # Prestador
    #
    g2ka.RPS['L'] = DicionarioBrasil()
    g2ka.RPS.L['Cnpj'] = nota.prestador.cnpj_cpf_numero
    g2ka.RPS.L['InscricaoMunicipal'] = nota.prestador.im or '0'
    #rps.prestador['rSocialPrest'] = nota.prestador.nome.strip()
    #rps.prestador['nFantasiaPrest'] = nota.prestador.nome.strip()
    #rps.prestador['endPrest'] = nota.prestador.endereco.strip()
    #rps.prestador['nPrest'] = nota.prestador.numero.strip()
    #rps.prestador['cPrest'] = nota.prestador.complemento.strip()
    #rps.prestador['bPrest'] = nota.prestador.bairro.strip()
    #rps.prestador['cMunPrest'] = nota.prestador.municipio.codigo_ibge
    #rps.prestador['ufPrest'] = nota.prestador.municipio.estado
    #rps.prestador['cepPrest'] = nota.prestador.cep

    #
    # Tomador
    #
    g2ka.RPS['M'] = DicionarioBrasil()

    if nota.tomador.tipo_pessoa in ('PF', 'PJ'):
        if nota.tomador.tipo_pessoa == 'PF':
            g2ka.RPS.M['Cpf'] = nota.tomador.cnpj_cpf_numero
        else:
            g2ka.RPS.M['Cnpj'] = nota.tomador.cnpj_cpf_numero

    g2ka.RPS.M['RazaoSocial'] = nota.tomador.nome.strip()


    g2ka.RPS['N'] = DicionarioBrasil()
    g2ka.RPS.N['LogradouroTomador'] = nota.tomador.endereco.strip()
    g2ka.RPS.N['Numero'] = nota.tomador.numero.strip()
    g2ka.RPS.N['Complemento'] = nota.tomador.complemento.strip() or None
    g2ka.RPS.N['Bairro'] = nota.tomador.bairro.strip()
    g2ka.RPS.N['CodigoMunicipio'] = nota.tomador.municipio.codigo_ibge
    g2ka.RPS.N['Uf'] = nota.tomador.estado.uf
    g2ka.RPS.N['CepTomador'] = nota.tomador.cep_numero.strip()

    ##
    ## Serviço
    ##
    #if nota.municipio_fato_gerador and nota.municipio_fato_gerador.codigo_ibge:
        #rps.servico['cMunServ'] = nota.municipio_fato_gerador.codigo_ibge

    #elif nota.natureza_operacao == NAT_OP_TRIBUTADA_FORA_MUNICIPIO:
        #rps.servico['cMunServ'] = nota.tomador.municipio.codigo_ibge

    #else:
        #rps.servico['cMunServ'] = nota.prestador.municipio.codigo_ibge


    #if nota.prestador.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
        #rps.servico['alISS'] = '0.00'
    #else:
        #rps.servico['alISS'] =

    #rps.servico['cExISS'] = '1'

    #g2ka.RPS.A['descricao'] = DicionarioBrasil()

    rps_raiz = DicionarioBrasil()
    rps_raiz['G2KA'] = g2ka

    res = rps_raiz.como_xml_em_texto

    nome_arq = '/home/prottege/neogrid/OUT/NFSeProd/NFSe_' + str(nota.rps.numero) + '.xml'

    open(nome_arq, 'w').write(res.encode('utf-8'))
    #open('/home/prottege/neogrid/neogrid.xml', 'w').write(res.encode('utf-8'))

    return res
