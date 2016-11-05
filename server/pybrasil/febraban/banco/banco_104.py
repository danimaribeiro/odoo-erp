# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from datetime import date
from pybrasil.data import parse_datetime
from pybrasil.febraban.boleto import Boleto
from decimal import Decimal as D


#def calcula_digito_nosso_numero(self, boleto):
    #calculo_digito = str(boleto.beneficiario.agencia.numero).zfill(4)
    #calculo_digito += str(boleto.banco.modalidade).zfill(3)
    #calculo_digito += str(boleto.beneficiario.codigo_beneficiario.numero).zfill(6)
    #calculo_digito += str(boleto.beneficiario.codigo_beneficiario.digito).zfill(1)
    #calculo_digito += str(boleto.nosso_numero).zfill(7)

    #return self.modulo11(calculo_digito, pesos=[3, 7, 9, 1])

def calcula_digito_nosso_numero(self, boleto):
    calculo_digito = str(boleto.banco.modalidade).zfill(2)
    calculo_digito += str(boleto.nosso_numero).zfill(15)

    return self.modulo11(calculo_digito)


def fator_vencimento(self, boleto):
    fator_vencimento = boleto.data_vencimento - date(2000, 7, 3)
    return fator_vencimento.days + 1000


def imprime_carteira(self, boleto):
    print('passou aqui', boleto.banco.carteira)
    if str(boleto.banco.carteira).zfill(2) == '01':
        return 'RG'
    else:
        return 'SR'


def campo_livre(self, boleto):
    boleto.beneficiario.agencia.numero = str(boleto.beneficiario.agencia.numero).zfill(4)
    boleto.beneficiario.codigo_beneficiario.numero = str(boleto.beneficiario.codigo_beneficiario.numero).zfill(6)
    boleto.beneficiario.codigo_beneficiario.digito = str(boleto.beneficiario.codigo_beneficiario.digito).zfill(1)

    nosso_numero = str(boleto.banco.modalidade).zfill(2) + str(boleto.nosso_numero).zfill(15)

    campo_livre = boleto.beneficiario.codigo_beneficiario.numero
    campo_livre += boleto.beneficiario.codigo_beneficiario.digito
    campo_livre += nosso_numero[2:5]
    campo_livre += nosso_numero[0]
    campo_livre += nosso_numero[5:8]
    campo_livre += nosso_numero[1]
    campo_livre += nosso_numero[8:]

    #campo_livre = nosso_numero
    #campo_livre += boleto.beneficiario.agencia.numero
    #campo_livre += boleto.banco.modalidade
    #campo_livre += str(boleto.beneficiario.codigo_beneficiario.numero).zfill(8)
    #campo_livre += self.modulo11(campo_livre)

    dv = self.modulo11(campo_livre)

    return campo_livre + dv


def agencia_conta(self, boleto):
    agencia = str(boleto.beneficiario.agencia.numero).zfill(4)

    #return '%s.%s.%s-%s' % (agencia, boleto.banco.modalidade, str(boleto.beneficiario.codigo_beneficiario.numero).zfill(8), str(boleto.beneficiario.codigo_beneficiario.digito).zfill(1))
    return '%s / %s-%s' % (agencia, str(boleto.beneficiario.codigo_beneficiario.numero).zfill(6), str(boleto.beneficiario.codigo_beneficiario.digito).zfill(1))


def carteira_nosso_numero(self, boleto):
    return '%s%s-%s' % (str(boleto.banco.modalidade).zfill(2), str(boleto.nosso_numero).zfill(15), boleto.digito_nosso_numero)


def header_remessa_400(self, remessa):
    boleto = remessa.boletos[0]
    beneficiario = boleto.beneficiario
    #
    # Header do arquivo
    #
    texto = '0' # 01-01 fixo
    texto += '1' # 02-02 fixo
    texto += 'REMESSA' # 03-09 Na fase de teste informar REM.TST, em produção REMESSA
    texto += '01' # 10-11 fixo
    texto += 'COBRANCA'.ljust(15) # 12-26 fixo
    texto += str(boleto.beneficiario.agencia.numero).zfill(4)[:4]
    texto += str(boleto.banco.modalidade).zfill(3)[:3]
    #
    # Campo seguinte com 9 posições, informado o dígito por tentativa e erro
    # no dia 07/04/2015
    # O manual da Caixa não informa se deveria ser informado ou não o dígito,
    # mas durante a implantação na ASP chegamos a conclusão de que esse problema
    # não permitiu o envio correto do arquivo
    #
    texto += str(beneficiario.codigo_beneficiario.numero).zfill(8)[:8] # 27-42 código da empresa na CAIXA
    texto += str(beneficiario.codigo_beneficiario.digito).zfill(1)[0]

    texto += ''.ljust(4)
    texto += beneficiario.nome.ljust(30)[:30]
    texto += '104'
    texto += 'C ECON FEDERAL'.ljust(15)
    texto += remessa.data_hora.strftime(b'%d%m%y')
    texto += ''.ljust(289)
    texto += str(remessa.sequencia).zfill(5)[:5]
    texto += str(1).zfill(6)[:6]

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

    #
    # Registro Tipo 1 – Registro Detalhe Cobrança de Títulos – Arquivo Remessa
    #
    texto = '1' # 01-01 FIXO

    if beneficiario.tipo_pessoa == 'PJ': # 02-03  01 P/ CPF e 2 /P CNPJ
        texto += '02'
    else:
        texto += '01'

    texto += str(beneficiario.cnpj_cpf_numero).zfill(14) # 04-17  cnpj

    texto += str(boleto.beneficiario.agencia.numero).zfill(4)[:4]
    texto += str(boleto.banco.modalidade).zfill(3)[:3]
    texto += str(beneficiario.codigo_beneficiario.numero).zfill(8)[:8]
    texto += str(beneficiario.codigo_beneficiario.digito).zfill(1)[0]

    texto += ''.ljust(2) # 34-35 brancos
    texto += '00' # 36-37  00 Acata Comissão por Dia (recomendável) ou 51 Acata Condições de Cadastramento na CAIXA
    texto += str(boleto.identificacao).ljust(25)[:25] # 38-62 identificação boleto da empresa
    texto += str(boleto.nosso_numero).zfill(10)[:10] # 63-72 identificação boleto na caixa (nosso numero)

    if boleto.nosso_numero == '0':
        texto += '0'
    else:
        texto += str(boleto.digito_nosso_numero).zfill(1)[0] # dígito do nosso número

    texto += ''.ljust(3) # 74-76 Campo em branco
    texto += ''.ljust(30)[:30] # 77-106 Mensagem a ser impressa no boleto
    texto += str(banco.carteira).zfill(2)[:2] # 107-108 Código da Carteira
    texto += boleto.comando or '01'  # 109-110 ocorrencia do titulo
    texto += str(boleto.documento.numero).ljust(10)[:10] # 111-120 ocorrencia do titulo
    texto += boleto.data_vencimento.strftime('%d%m%y') # 121-126 data vencimento
    texto += str(int(boleto.documento.valor * 100)).zfill(13)[:13] #  127-139 valor
    texto += '104' # 140-142 fixo

    #
    # Agência cobradora, deve ir zerada
    #
    #texto += str(beneficiario.agencia.numero).zfill(4)[:4] # 143-147 agencia e digito
    #texto += str(beneficiario.agencia.digito).zfill(1)[:1]
    texto += ''.zfill(4)[:4] # 143-147 agencia e digito
    texto += ''.zfill(1)[:1]

    texto += '01' # 148-149 tipo do titulo nota 06
    texto += boleto.aceite  # 149-150 Aceite / Não aceite
    texto += boleto.data_processamento.strftime('%d%m%y') # 151-156 data de emissao
    texto += '01'.zfill(2) # 157-158 Primeira Instrução de Cobrança
    texto += ''.zfill(2) # 159-160 Segunda Instrução de Cobrança
    texto += ''.zfill(13) # 161-173 Juros de Mora por dia/Valor

    if boleto.data_desconto: # 174-192 data descont e valor desconto
        texto += boleto.data_desconto.strftime('%d%m%y')
        texto += str(int(boleto.valor_desconto * 100)).zfill(13)
    else:
        texto += ''.zfill(6)
        texto += ''.zfill(13)
    texto += str(int(boleto.valor_iof * 100)).zfill(13) # 193-205 iof
    texto += str(int(boleto.valor_abatimento * 100)).zfill(13) # 206-218 valor abatimento

    if pagador.tipo_pessoa == 'PJ': # 219-220 identificador sacado
        texto += '02'
    else:
        texto += '01'

    texto += pagador.cnpj_cpf_numero.zfill(14)[:14] # 221-234 cnpj sacado
    texto += pagador.nome.ljust(40)[:40] # 235-274 nome sacado
    texto += pagador.endereco_numero_complemento.ljust(40)[:40] # 275-314 logradouro
    texto += pagador.bairro.ljust(12)[:12] # 315-326 bairro sacado
    texto += pagador.cep.replace('-', '').zfill(8)[:8] # 327-334 CEP
    texto += pagador.cidade.ljust(15)[:15] # 335-349 cidade
    texto += pagador.estado[:2] # 350-351 uf
    texto += boleto.data_vencimento.strftime('%d%m%y') # 352-357 Definição da data para pagamento de multa
    texto += ''.zfill(10) #358-367 Valor nominal da multa
    texto += ''.ljust(22)[:22] # 368-389 Nome do Sacador/Avalista
    texto += ''.zfill(2) # 390-391 Terceira Instrução de Cobrança
    texto += str(boleto.dias_protesto).zfill(2) # 392-393 dias de protesto
    texto += '1' # 394-394
    texto += str(len(remessa.registros) + 1).zfill(6) #395-400 nº do registro

    return self.tira_acentos(texto.upper())


def Mensagem_remessa_400(self, remessa, boleto):
    beneficiario = boleto.beneficiario
    pagador = boleto.pagador
    #
    # Registro Tipo 2 – Registro Detalhe Cobrança de Títulos – Arquivo Remessa (Mensagens)
    #
    texto = '2'
    if beneficiario.tipo_pessoa == 'PJ':
        texto += '02'
    else:
        texto += '01'
    texto += str(beneficiario.cnpj_cpf_numero).zfill(14)
    texto += str(beneficiario.agencia.numero).zfill(4)
    texto += str(beneficiario.agencia.digito).zfill(1)
    texto += str(beneficiario.codigo_beneficiario.numero).zfill(6)
    texto += str(beneficiario.codigo_beneficiario.digito).zfill(1)
    texto += ''.ljust(4)
    texto += ''.ljust(25)
    texto += str(boleto.nosso_numero).zfill(15)
    texto += str(boleto.digito_nosso_numero).zfill(2)
    texto += ''.ljust(33)
    texto += ''.ljust(2) #Código da Carteira
    texto += ''.ljust(2) #Identificação Tipo Ocorrência do arquivo remessa
    texto += ''.ljust(29)
    texto += '104'
    texto += ''.ljust(30) #Mensagem a ser impressa 1 a ser impressa
    texto += ''.ljust(30) #Mensagem a ser impressa 2 a ser impressa
    texto += ''.ljust(30) #Mensagem a ser impressa 3 a ser impressa
    texto += ''.ljust(30) #Mensagem a ser impressa 4 a ser impressa
    texto += ''.ljust(30) #Mensagem a ser impressa 5 a ser impressa
    texto += ''.ljust(30) #Mensagem a ser impressa 6 a ser impressa
    texto += ''.ljust(12)
    texto += str(len(remessa.registros) + 1).zfill(6)

    return texto


def header_retorno_400(self, retorno):
    header = retorno.linhas[0]
    
    retorno.banco.codigo = header[76:79]

    beneficiario = retorno.beneficiario

    beneficiario.agencia.numero = header[26:30]
    beneficiario.codigo_beneficiario.numero = unicode(D(header[30:36])).zfill(6)
    beneficiario.nome = header[46:76]

    retorno.data_hora = parse_datetime(header[94:100]).date()
    retorno.sequencia = int(header[389:394])


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

        boleto.identificacao = linha[31:56]
        boleto.banco.modalidade = linha[56:58]
        boleto.nosso_numero = unicode(D(linha[58:73]))
        #boleto.nosso_numero_digito = linha[73]
        #boleto.parcela = int(linha[74:76])
        #boleto.documento.especie = linha[83:85]
        boleto.comando = linha[108:110]
        boleto.data_ocorrencia = parse_datetime(linha[110:116])
        boleto.data_credito = parse_datetime(linha[293:299])
     
        
        boleto.valor_despesa_cobranca = D(linha[175:188]) / D('100')
        
        boleto.valor_desconto = D(linha[240:253]) / D('100')
        boleto.documento.valor = D(linha[253:266]) / D('100')
        boleto.valor_juros = D(linha[266:279]) / D('100')
        boleto.valor_multa = D(linha[279:292]) / D('100')
     
        boleto.valor_recebido = boleto.documento.valor - boleto.valor_desconto + boleto.valor_juros + boleto.valor_multa

        retorno.boletos.append(boleto)


DESCRICAO_COMANDO_REMESSA = {
    '01': 'Registro de título',
    '02': 'Solicitação de baixa',
    '03': 'Concessão de abatimento',
    '04': 'Cancelamento de abatimento',
    '05': 'Alteração de vencimento',
    '06': 'Alteração do uso da empresa',
    '07': 'Alteração do prazo de protesto',
    '08': 'Alteração do prazo de devolução',
    '09': 'Alteração de outros dados',
    '10': 'Alteração de outros dados',
    '11': 'Alteração de outros dados',
    '12': 'Alteração de outros dados',
}


DESCRICAO_COMANDO_RETORNO = {
    '01': 'Confirmação de entrada do título',
    '02': 'Confirmação de baixa do título',
    '03': 'Abatimento concedido',
    '04': 'Abatimento cancelado',
    '05': 'Vencimento alterado',
    '06': 'Uso da empresa alterado',
    '07': 'Prazo de protesto alterado',
    '08': 'Prazo de devolução alterado',
    '09': 'Alteração confirmada',
    '10': 'Alteração confirmada',
    '11': 'Alteração confirmada',
    '12': 'Alteração confirmada',
    
    '20': 'Em ser',
    '21': 'Liquidação normal',
    '22': 'Liquidação em cartório',
    '23': 'Baixa por devolução',
    '25': 'Baixa por protesto',
    '26': 'Encaminhado a protesto',
    '27': 'Sustação de protesto',
    '28': 'Estorno de protesto',
    '29': 'Estorno de sustação de protesto',
    
    '30': 'Alteração de título',
    '31': 'Tarifa sobre título vencido',
    '32': 'Outras tarifas de alteração',
    '33': 'Estorno de baixa/liquidação',
    '34': 'Tarifas diversas',
    '99': 'Rejeição do título',
}


COMANDOS_RETORNO_LIQUIDACAO = {
    '21': True,
    '22': True,
}


COMANDOS_RETORNO_BAIXA = [
    '23',
    '25',
]
