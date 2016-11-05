# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from datetime import date
from pybrasil.data import parse_datetime
from pybrasil.febraban.boleto import Boleto
from decimal import Decimal as D
from string import ljust


def calcula_digito_nosso_numero(self, boleto):
    calculo_digito = str(boleto.beneficiario.agencia.numero).zfill(4)
    calculo_digito += str(boleto.beneficiario.codigo_beneficiario.numero).zfill(9)
    calculo_digito += str(boleto.beneficiario.codigo_beneficiario.digito).zfill(1)
    calculo_digito += str(boleto.nosso_numero).zfill(7)

    return self.modulo11(calculo_digito, pesos=[3, 7, 9, 1])


def carteira_nosso_numero(self, boleto):
    #return '%s%s' % (str(boleto.beneficiario.codigo_beneficiario.numero).zfill(7), str(boleto.nosso_numero).zfill(10))

    if len(boleto.beneficiario.conta.convenio) == 4:
        return '%s%s-%s' % (str(boleto.beneficiario.conta.convenio).zfill(4)[:4], str(boleto.nosso_numero).zfill(7), boleto.digito_nosso_numero)

    elif len(boleto.beneficiario.conta.convenio) == 6:
        return '%s%s-%s' % (str(boleto.beneficiario.conta.convenio).zfill(6)[:6], str(boleto.nosso_numero).zfill(5), boleto.digito_nosso_numero)

    elif len(boleto.beneficiario.conta.convenio) == 7:
        return '%s%s' % (str(boleto.beneficiario.conta.convenio).zfill(7)[:7], str(boleto.nosso_numero).zfill(10))


def agencia_conta(self, boleto):
    return '%s-%s/%s-%s' % (str(boleto.beneficiario.agencia.numero).zfill(4),
        str(boleto.beneficiario.agencia.digito).zfill(1),
        boleto.beneficiario.conta.numero.zfill(5)[:5],
        boleto.beneficiario.conta.digito.zfill(1)[:1])


def fator_vencimento(self, boleto):
    fator_vencimento = boleto.data_vencimento - date(2000, 7, 3)
    return fator_vencimento.days + 1000


def campo_livre(self, boleto):
    campo_livre = ''.zfill(6)
    #campo_livre += boleto.beneficiario.codigo_beneficiario.numero.zfill(7)[:7]

    if len(boleto.beneficiario.conta.convenio) == 4:
        campo_livre += str(boleto.beneficiario.conta.convenio).zfill(6)[:6]
        campo_livre += str(boleto.nosso_numero).zfill(5)[:5]
        campo_livre += str(boleto.beneficiario.agencia.numero).zfill(4)[:4]
        campo_livre += str(boleto.beneficiario.conta.numero).zfill(8)[:8]
        campo_livre += str(boleto.banco.carteira).zfill(2)[:2]

    elif len(boleto.beneficiario.conta.convenio) == 6:
        campo_livre += str(boleto.beneficiario.conta.convenio).zfill(6)[:6]
        campo_livre += str(boleto.nosso_numero).zfill(5)[:5]
        campo_livre += str(boleto.beneficiario.agencia.numero).zfill(4)[:4]
        campo_livre += str(boleto.beneficiario.conta.numero).zfill(8)[:8]
        campo_livre += str(boleto.banco.carteira).zfill(2)[:2]

    elif len(boleto.beneficiario.conta.convenio) == 7:
        campo_livre += str(boleto.beneficiario.conta.convenio).zfill(7)[:7]
        campo_livre += str(boleto.nosso_numero).zfill(10)[:10]
        campo_livre += str(boleto.banco.carteira).zfill(2)[:2]

    return campo_livre


#
#
########################## Banco do Brasil ########################
#
#

def header_remessa_400(self, remessa):
    boleto = remessa.boletos[0]
    beneficiario = boleto.beneficiario
    #
    # Header do arquivo
    #
    texto = '0' # 01-01 identificação do registro header
    texto += '1' # 02-02 tipo de operação
    texto += 'REMESSA'.ljust(7) # 03-09 Na fase de teste informar TESTE, em produção REMESSA
    texto += '01'# 10-11 tipo de serviço
    texto += 'COBRANCA'.ljust(8) # 12-19 identificador por ex. da operação
    texto += ''.ljust(7) # 20-26 brancos
    texto += str(beneficiario.agencia.numero).zfill(4)[:4] # 27-30 prefixo da agencia
    texto += str(beneficiario.agencia.digito).zfill(1) # 31-31 digito prefixo da agencia
    texto += beneficiario.conta.numero.zfill(8)[:8] # 32-39 numero conta corrente do convenio
    texto += beneficiario.conta.digito.zfill(1)[:1] # 40-40 digito conta corrente do convenio
    texto += '000000' # 41-46 complemento do registro
    texto += beneficiario.nome.ljust(30)[:30] # 47-76 Nome do cedente
    texto += '001BANCODOBRASIL'.ljust(18)[:18] # 77-94
    texto += remessa.data_hora.strftime(b'%d%m%y') # 95-100 data da gravação
    texto += str(remessa.sequencia).zfill(7)[:7] # 101-107 sequencia da remesa
    texto += ''.ljust(22) # 108-129 # brancos
    texto += str(beneficiario.codigo_beneficiario.numero).zfill(07) # 130-136 numero do convenio lider
    texto += ''.ljust(258) # 137-394 # brancos
    texto += str(1).zfill(6)[:6] # sequencial

    return self.tira_acentos(texto.upper())


def trailler_remessa_400(self, remessa):
    #
    # Trailler do arquivo
    #
    texto = '9'
    texto += ''.ljust(393)
    texto += str(len(remessa.registros) + 1).zfill(6)

    return self.tira_acentos(texto.upper())


def linha_remessa_400(self, remessa, boleto):
    beneficiario = boleto.beneficiario
    pagador = boleto.pagador
    banco = boleto.banco

    texto = '7' # 01-01 identidicação do titulo


    if beneficiario.tipo_pessoa == 'PJ':
        texto += '02'
    else:
        texto += '01'

    texto += str(beneficiario.cnpj_cpf_numero).zfill(14)[:14] # 04-17 numero do cnpj ou cpf
    texto += str(beneficiario.agencia.numero).zfill(4)[:4] # 18-21 prefixo da agencia
    texto += str(beneficiario.agencia.digito).zfill(1)[:1] # 22-22 digito do prefixo da agencia
    texto += str(beneficiario.conta.numero).zfill(8)[:8] # 23-30 beneficiario conta corrente
    texto += str(beneficiario.conta.digito).zfill(1)[:1] # 31-31 digito da conta corrente
    texto += str(beneficiario.codigo_beneficiario.numero).zfill(7)[:7] # 32-38 numero do convenio de cobrança cedente
    texto += ''.ljust(25) # 39-63 codigo de controle da empresa

    codigo = str(beneficiario.codigo_beneficiario.numero).zfill(7)[:7]
    numero = str(boleto.nosso_numero).zfill(10)[:10]

    texto += '' + codigo + numero # 64-80 nosso numero
    texto += ''.zfill(2) # 81-82 numero da prestação
    texto += ''.zfill(2) # 83-84 grupo valor
    texto += ''.ljust(3) # 85-87 complemento valor
    texto += ''.ljust(1) # 88-88 indicação mensagem sacadista
    texto += ''.ljust(3) # 89-91 prefixo dos titulos
    texto += str(banco.modalidade).zfill(3)[:3] # 92-94 variação da carteira
    texto += ''.zfill(1) # 95-95 conta caução
    texto += ''.zfill(6) # 96-101 numero bordero
    texto += ''.ljust(5) # 102-106 tipo de cobrança
    texto += str(banco.carteira).zfill(2)[:2] # 107-108 carteira de cobrança
    texto += '01' # 109-110 comando
    texto += ''.ljust(10) # 111-120 seu numero atribuido pelo cedente
    texto += boleto.data_vencimento.strftime('%d%m%y') # 121-126 data do vencimento
    texto += str(int(boleto.documento.valor * 100)).zfill(13) # 127-139 valor do titulo
    texto += '001' # 140-142 numero do banco
    texto += ''.zfill(4) # 143-146 prefixo da agencia cobradora
    texto += ''.ljust(1) # 147-147 digito do prefixo
    texto += '01' # 148-149 especie do titulo
    texto += 'N' # 150-150 aceite do titulo
    texto += boleto.data_processamento.strftime('%d%m%y') # 151-156 data emissao

    if boleto.dias_protesto:
        if int(boleto.dias_protesto) >= 6:
            texto += '06' # 157-158 instrucao codificada banco
    else:
        texto += ''.zfill(2) # 157-158 instrucao codificada

    texto += ''.zfill(2) # 159-160 instrucao codificada


    texto += ''.zfill(13) # 161-173 Juros de Mora por dia/Valor

    # 174-192 data limite para conscessao
    if boleto.data_desconto:
        texto += boleto.data_desconto.strftime('%d%m%y')
        texto += str(int(boleto.valor_desconto * 100)).zfill(13)[:13]
    else:
        texto += ''.zfill(6)
        texto += ''.zfill(13)
    texto += str(int(boleto.valor_iof * 100)).zfill(13)[:13] # 193-205 iof
    texto += str(int(boleto.valor_abatimento * 100)).zfill(13)[:13] # 206-218 valor abatimento

    if pagador.tipo_pessoa == 'PJ':
        texto += '02'
    else:
        texto += '01'
    texto += pagador.cnpj_cpf_numero.zfill(14)[:14] # 211-234 numero de inscr. pagador
    texto += pagador.nome.ljust(37)[:37] # 235 -271 nome do sacado
    texto += ''.ljust(3) # 272-274 complemento
    texto += pagador.endereco_numero_complemento.ljust(40)[:40] # 275-314 endereço
    texto += pagador.bairro.ljust(12)[:12] # 315 326 bairro
    texto += pagador.cep.replace('-', '').zfill(8)[:8] # 327-334 CEP
    texto += pagador.cidade.ljust(15)[:15] # 335-349 cidade
    texto += pagador.estado[:2] # 350-351 estado
    texto += ''.ljust(40) # 352-391 observação

    if boleto.dias_protesto:
        if int(boleto.dias_protesto) >= 6:
            texto += str(boleto.dias_protesto).zfill(2) # 392-393 dias de protesto
    else:
        texto += ''.ljust(2) # 392-393 dias de protesto

    texto += ''.ljust(1) # 394-394 estado
    texto += str(len(remessa.registros) + 1).zfill(6)[:6] # 395-40 branco

    return self.tira_acentos(texto.upper())


############## RETORNO 400 ####################

def header_retorno_400(self, retorno):
    header = retorno.linhas[0]

    beneficiario = retorno.beneficiario

    beneficiario.agencia.numero = header[27:30]
    beneficiario.agencia.digito = header[30]
    beneficiario.codigo_beneficiario.numero = unicode(D(header[31:36])).zfill(6)
    beneficiario.codigo_beneficiario.digito = header[36]
    beneficiario.nome = header[47:76]

    retorno.data_hora = parse_datetime(header[95:100]).date()
    retorno.sequencia = int(header[395:400])



def linha_retorno_400(self, retorno):
    beneficiario = retorno.beneficiario
    linha = retorno.linhas[1]

    #
    # Beneficiario
    #
    beneficiario.cnpj_cpf = linha[3:17]
    beneficiario.conta.numero = unicode(D(linha[22:30]))
    beneficiario.conta.digito = linha[30]

    for i in range(1, len(retorno.linhas) - 1):
        linha = retorno.linhas[i]
        boleto = Boleto()
        boleto.beneficiario = retorno.beneficiario
        boleto.banco = self

        boleto.nosso_numero = unicode(D(linha[62:73]))
        #boleto.nosso_numero_digito = linha[73]
        boleto.parcela = int(linha[74:76])
        boleto.documento.especie = linha[83:85]
        boleto.banco.modalidade = linha[106:108]
        boleto.comando = linha[108:110]
        print(boleto.comando)
        boleto.data_ocorrencia = parse_datetime(linha[110:116])
        boleto.data_credito = parse_datetime(linha[175:181])
        boleto.valor_despesa_cobranca = D(linha[181:188]) / D('100')
        boleto.valor_multa = D(linha[188:201]) / D('100')
        boleto.valor_desconto = D(linha[240:253]) / D('100')
        boleto.valor_recebido = D(linha[253:266]) / D('100')
        boleto.valor_juros = D(linha[266:279]) / D('100')
        boleto.valor_outros_creditos = D(linha[279:292]) / D('100')
        boleto.documento.valor = boleto.valor_recebido
        boleto.documento.valor -= boleto.valor_juros
        boleto.documento.valor -= boleto.valor_multa
        boleto.documento.valor -= boleto.valor_outros_creditos
        boleto.documento.valor += boleto.valor_desconto
        #boleto.documento.valor += boleto.valor_despesa_cobranca


        boleto.pagador.cnpj_cpf = linha[342:357]

        retorno.boletos.append(boleto)
