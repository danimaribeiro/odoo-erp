# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from datetime import date
from pybrasil.data import parse_datetime
from pybrasil.febraban.boleto import Boleto
from pybrasil.valor.decimal import Decimal as D
from pybrasil.inscricao import limpa_formatacao

#
# No contexto deste banco, o campo
# modalidade do SICOOB é o posto do SICREDI
#

def calcula_digito_nosso_numero(self, boleto):
    calculo_digito = str(boleto.beneficiario.agencia.numero).zfill(4)
    calculo_digito += str(boleto.banco.modalidade).zfill(2)  # Posto
    calculo_digito += str(boleto.beneficiario.codigo_beneficiario.numero).zfill(5)
    calculo_digito += str(boleto.documento.data.year).zfill(4)[2:4]
    calculo_digito += str(boleto.nosso_numero).zfill(6)

    return self.modulo11(calculo_digito)


def carteira_nosso_numero(self, boleto):
    return '%s/%s-%s' % (str(boleto.documento.data.year).zfill(4)[2:4], boleto.nosso_numero, boleto.digito_nosso_numero)


def agencia_conta(self, boleto):
    return '%s.%s.%s' % (str(boleto.beneficiario.agencia.numero).zfill(4),
        str(boleto.banco.modalidade).zfill(2),  # Posto
        str(boleto.beneficiario.codigo_beneficiario.numero).zfill(5))


def fator_vencimento(self, boleto):
    fator_vencimento = boleto.data_vencimento - date(2000, 7, 3)
    return fator_vencimento.days + 1000


def campo_livre(self, boleto):
    boleto.banco.carteira = str(boleto.banco.carteira).zfill(1)
    boleto.beneficiario.agencia.numero = str(boleto.beneficiario.agencia.numero).zfill(4)
    boleto.banco.modalidade = str(boleto.banco.modalidade).zfill(2)
    boleto.beneficiario.codigo_beneficiario.numero = str(boleto.beneficiario.codigo_beneficiario.numero).zfill(5)
    boleto.beneficiario.codigo_beneficiario.digito = str(boleto.beneficiario.codigo_beneficiario.digito).zfill(1)
    boleto.nosso_numero = str(boleto.nosso_numero).zfill(6)

    campo_livre = boleto.banco.carteira
    campo_livre += '1'  #  Carteira simples
    campo_livre += str(boleto.documento.data.year).zfill(4)[2:4]
    campo_livre += boleto.nosso_numero
    campo_livre += boleto.digito_nosso_numero
    campo_livre += boleto.beneficiario.agencia.numero
    campo_livre += boleto.banco.modalidade
    campo_livre += boleto.beneficiario.codigo_beneficiario.numero.zfill(5)

    if boleto.documento.valor > 0:
        campo_livre += '1'
    else:
        campo_livre += '0'

    campo_livre += '0'  # filler

    campo_livre += self.modulo11(campo_livre, mapa_digitos={10: 0, 11: 0})

    return campo_livre


def header_remessa_400(self, remessa):
    boleto = remessa.boletos[0]
    beneficiario = boleto.beneficiario
    #
    # Header do arquivo
    #
    texto = '0'
    texto += '1'
    texto += 'REMESSA'
    texto += '01'
    texto += 'COBRANCA'.ljust(15)
    #texto += str(beneficiario.agencia.numero).zfill(4)
    #texto += str(beneficiario.agencia.digito).zfill(1)
    texto += str(beneficiario.codigo_beneficiario.numero).zfill(5)
    #texto += str(beneficiario.codigo_beneficiario.digito).zfill(1)
    #texto += str(beneficiario.conta.numero).zfill(6)
    texto += beneficiario.cnpj_cpf_numero.zfill(14)
    texto += ''.ljust(31)
    texto += '748'
    texto += 'Sicredi'.ljust(15)
    texto += remessa.data_hora.strftime(b'%Y%m%d')
    texto += ''.ljust(8)
    texto += str(remessa.sequencia).zfill(7)
    texto += ''.ljust(273)
    texto += '2.00'
    texto += str(1).zfill(6)

    return self.tira_acentos(texto)


def trailler_remessa_400(self, remessa):
    boleto = remessa.boletos[0]
    beneficiario = boleto.beneficiario
    #
    # Trailler do arquivo
    #
    texto = '9'
    texto += '1'
    texto += '748'
    texto += str(beneficiario.codigo_beneficiario.numero).zfill(5)
    texto += ''.ljust(384)
    texto += str(len(remessa.registros) + 1).zfill(6)  # Quantidade de registros

    return self.tira_acentos(texto)


def linha_remessa_400(self, remessa, boleto):
    beneficiario = boleto.beneficiario
    pagador = boleto.pagador

    texto = '1'
    texto += 'A'  # com registro
    texto += 'A'  # tipo da carteira
    texto += 'A'  # tipo da impressão
    texto += ''.ljust(12)
    texto += 'A'  # tipo da moeda
    texto += 'A'  # tipo de desconto (A - valor, B - %)
    texto += 'A'  # tipo de juros (A - valor, B - %)
    texto += ''.ljust(28)

    texto += str(boleto.documento.data.year).zfill(4)[2:4]
    texto += boleto.nosso_numero.zfill(6)
    texto += boleto.digito_nosso_numero

    texto += ''.ljust(6)
    texto += remessa.data_hora.strftime(b'%Y%m%d')

    #
    # Posição 071
    #
    texto += ' '

    texto += 'N'  # Postagem
    texto += ' '
    texto += 'B'  # Impressão pelo beneficiário

    # Tipo de impressa A '0000' se B com parcelas

    texto += '0000'  # Impressão pelo beneficiário

    #texto += str(boleto.parcela).zfill(2)
    #texto += '00' # total de parcelas do carnê


    texto += ''.ljust(4)
    texto += ''.zfill(10)  # Desconto por antecipação
    texto += str(int(boleto.valor_multa / boleto.documento.valor * 100)).zfill(4)
    texto += ''.ljust(12)
    texto += boleto.comando or '01'
    texto += str(boleto.documento.numero).ljust(10)[:10]
    texto += boleto.data_vencimento.strftime('%d%m%y')
    texto += str(int(boleto.documento.valor * 100)).zfill(13)
    texto += ''.ljust(9)

    texto += 'A'  # Duplicata mercantil
    texto += boleto.aceite  # Aceite
    texto += boleto.documento.data.strftime('%d%m%y')

    if boleto.dias_protesto:
        texto += '06'
        texto += str(boleto.dias_protesto).zfill(2)
    else:
        texto += '00'
        texto += '00'

    texto += str(int(boleto.valor_juros * 100)).zfill(13)

    if boleto.data_desconto:
        texto += boleto.data_desconto.strftime('%d%m%y')
        texto += str(int(boleto.valor_desconto * 100)).zfill(13)
    else:
        texto += ''.zfill(6)
        texto += ''.zfill(13)

    texto += ''.zfill(13)
    texto += str(int(boleto.valor_abatimento * 100)).zfill(13)

    if pagador.tipo_pessoa == 'PJ':
        texto += '2'
    else:
        texto += '1'

    texto += ' '

    texto += pagador.cnpj_cpf_numero.zfill(14)
    texto += pagador.nome[:40].ljust(40)
    texto += pagador.endereco_numero_complemento.ljust(40)[:40]
    texto += ''.zfill(5)
    texto += ''.zfill(6)  # Filler
    texto += ' '  # Filler
    texto += pagador.cep.replace('-', '').zfill(8)
    texto += str(boleto.identificacao).replace('id_', '').zfill(5)[:5]

    #
    # Sacador
    #
    texto += ''.ljust(14)
    texto += ''.ljust(41)
    texto += str(len(remessa.registros) + 1).zfill(6)  # nº do registro

    return self.tira_acentos(texto)


def header_retorno_400(self, retorno):
    header = retorno.linhas[0]

    beneficiario = retorno.beneficiario

    beneficiario.codigo_beneficiario.numero = header[26:31]
    beneficiario.cnpj_cpf = header[31:45]
    #retorno.beneficiario.nome = header[46:76]

    retorno.data_hora = parse_datetime(header[94:102], ano_primeiro=True).date()
    retorno.sequencia = int(header[110:117])


def header_retorno_240(self, retorno):
    header = retorno.linhas[0]

    beneficiario = retorno.beneficiario

    beneficiario.cnpj_cpf = header[18:32]
    beneficiario.agencia.numero = unicode(D(header[52:57]))
    beneficiario.agencia.digito = header[57]
    beneficiario.conta.numero = unicode(D(header[58:70]))
    beneficiario.conta.digito = header[70]
    beneficiario.nome = header[72:102]
    retorno.data_hora = parse_datetime(header[143:151] + ' ' + header[151:157])
    retorno.sequencia = int(header[157:163])


DESCRICAO_COMANDO_REMESSA = {
    '01': 'Registro de título',
    '02': 'Solicitação de baixa',
    '03': 'Pedido de débito em conta',
    '04': 'Concessão de abatimento',
    '05': 'Cancelamento de abatimento',
    '06': 'Alteração de vencimento',
    '07': 'Alteração do número de controle',
    '08': 'Alteração de seu número',
    '09': 'Instrução para protestar',
    '10': 'Instrução para sustar protesto',
    '11': 'Instrução para dispensar juros',
    '12': 'Alteração de sacado',
    '30': 'Recusa de alegação do sacado',
    '31': 'Alteração de outros dados',
    '34': 'Baixa - pagamento direto ao beneficiário',
}


DESCRICAO_COMANDO_RETORNO = {
    '02': 'Confirmação de entrada do título',
    '03': 'Entrada do título rejeitada',
    '05': 'Liquidação sem registro',
    '06': 'Liquidação normal',
    '09': 'Baixa de título',
    '10': 'Baixa a pedido do beneficiário',
    '11': 'Títulos em aberto',
    '14': 'Alteração de vencimento',
    '15': 'Liquidação em cartório',
    '23': 'Encaminhado a protesto',
    '27': 'Confirmação de alteração de dados',
    '28': 'Tarifas',
}


COMANDOS_RETORNO_LIQUIDACAO = {
    '05': True,
    '06': True,
    '15': True,
}


COMANDOS_RETORNO_BAIXA = [
    '09',
    '10',
]


def linha_retorno_400(self, retorno):
    beneficiario = retorno.beneficiario
    linha = retorno.linhas[1]

    #
    # Beneficiario
    #
    #beneficiario.cnpj_cpf = linha[3:17]
    #beneficiario.conta.numero = unicode(D(linha[22:30]))
    #beneficiario.conta.digito = linha[30]

    for i in range(1, len(retorno.linhas) - 1):
        linha = retorno.linhas[i]
        boleto = Boleto()
        boleto.beneficiario = retorno.beneficiario
        boleto.banco = self

        #boleto.nosso_numero = unicode(D(linha[47:56]))
        boleto.nosso_numero = unicode(D(linha[49:55]))
        #boleto.nosso_numero_digito = linha[73]
        #boleto.parcela = int(linha[74:76])
        #boleto.documento.especie = linha[83:85]
        #boleto.banco.modalidade = linha[106:108]
        boleto.comando = linha[108:110]
        #print(boleto.comando)
        boleto.data_ocorrencia = parse_datetime(linha[110:116])
        boleto.data_credito = parse_datetime(linha[328:336], ano_primeiro=True)
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


        #boleto.pagador.cnpj_cpf = linha[342:357]

        retorno.boletos.append(boleto)



#
#
#
#
###################### Folha de Pagamento Sicred #############################
#
#
#




def header_remessa_240(self, remessa):
    beneficiario = remessa.beneficiario
    banco = beneficiario.banco


    #
    # Header do arquivo
    #

    texto = '748'.ljust(3) # 01-03 Código do banco na compensação
    texto += '0000' # 4-7 Lote de serviço
    texto += '0' # 8-8 Tipo de registro
    texto += ''.ljust(9)  # 9-17 uso sicred
    texto += '2' # 18-18 ipo de inscrição da empresa
    texto += limpa_formatacao(beneficiario.cnpj_cpf).zfill(14) # 19-32 Número de inscrição da empresa
    texto += str(beneficiario.conta.convenio).ljust(20) # 33-52 Código do convênio no banco
    texto += str(beneficiario.agencia.numero).zfill(5) # 53-57Agência mantenedora da conta
    texto += str(beneficiario.agencia.digito).zfill(1)  # 58-58 Dígito verificador da agência
    texto += str(beneficiario.conta.numero).zfill(12)  # 59-70 Número da conta corrente empresa
    texto += str(beneficiario.conta.digito).zfill(1)  # 71-71 Dígito verificador da conta
    texto += ''.ljust(1)  # 72-72 Dígito verificador da Ag/conta
    texto += beneficiario.nome.ljust(30)[:30] # 73-102 Nome da empresa
    texto += 'SICREDI'.ljust(30)[:30]  # 103-132 Nome do banco
    texto += ''.ljust(10)  # 133-142 uso sicred
    texto += '1'.zfill(1)  # 143-143 Código remessa / retorno
    texto += remessa.data_hora.strftime(b'%d%m%Y') # 144-151 DATA DO ARQUIVO
    texto += remessa.data_hora.strftime(b'%H%M%S')[:6] # 152-157 HORA DO ARQUIVO
    texto += str(remessa.sequencia).zfill(6) # 158-163 Número seqüencial do arquivo
    texto += '082' # 164-166 No da versão do leiaute do arquivo
    texto += '1600'.zfill(5) # 167-171 Densidade de gravação do arquivo
    texto += ''.ljust(20) # 172-191 Para uso reservado da empresa
    texto += ''.ljust(20) # 192-211 Para uso reservado da empresa
    texto += ''.ljust(29) # 212-240 Uso exclusivo SICREDI
    texto += '\n'

    #
    # Header do lote
    #

    texto += '748'.ljust(3) # 1-3 Código do banco na compensação
    texto += '0001'.zfill(4) # 4-7 Lote de serviço
    texto += '1' # 8-8 Tipo de registro
    texto += 'C' # 9-9 Tipo da operação
    texto += '30'.zfill(2)  # 10-11 Tipo do serviço
    texto += '01'.zfill(2)  # 12-13  Forma de lançamento
    texto += '042'  # 14-16 Nº da versão do leiaute do lote
    texto += ''.ljust(1)  # 17-17 uso sicrid

    if beneficiario.tipo_pessoa == 'PJ':
        texto += '2'
    else:
        texto += '1'

    texto += limpa_formatacao(beneficiario.cnpj_cpf).zfill(14)  # 19-32 Número de inscrição da empresa
    texto += str(beneficiario.conta.convenio).ljust(20)[:20]  # 33-52 Código do convênio no banco
    texto += str(beneficiario.agencia.numero).zfill(5) # 53-57Agência mantenedora da conta
    texto += str(beneficiario.agencia.digito).zfill(1) # 58-58 Dígito verificador da agência
    texto += str(beneficiario.conta.numero).zfill(12)  # 59-70 Número da conta corrente empresa
    texto += str(beneficiario.conta.digito).zfill(1)  # 71-71 Dígito verificador da conta
    texto += ''.ljust(1)  # 72-72 Dígito verificador da Ag/conta
    texto += beneficiario.nome.ljust(30)[:30] # 73-102 Nome da empresa
    texto += ''.ljust(40)[:40]  # 103-142 mensagem
    texto += beneficiario.endereco_numero_complemento.ljust(30)[:30] # 143-172 endereco empresa
    texto += ''.ljust(5)[:5] # 173-177 numero
    texto += ''.ljust(15)[:15] # 178-192 complemento
    texto += beneficiario.cidade.ljust(20)[:20] # 193-212 empresa cidade
    texto += beneficiario.cep.replace('-', '').ljust(8)[:8] # 213-217 CEP
    texto += beneficiario.estado.ljust(2)[:2] # 221-222 sigla UF
    texto += ''.ljust(8)  # 223-230  uso sicred
    texto += ''.ljust(10)  # 231-240 ocorrencia / retorno

    return self.tira_acentos(texto.upper())


def trailler_remessa_240(self, remessa):

    #
    # Trailler do lote
    #
    texto = '748'.ljust(3) # 1-3 Código do banco na compensação
    texto += '0001'.ljust(4) # 4-7 Lote de Serviço
    texto += '5' # 8-8
    texto += ''.ljust(9) # 9-17 uso o sicred
    texto += str(remessa.beneficiario.registro + 1).zfill(6)[:6]  # 18-23 Quantidade de registros
    texto += str(int(remessa.beneficiario.valor_total * 100)).zfill(18)[:18] # 24-41 somatória dos valores
    texto += ''.zfill(18) # 42-59 somatória de quantidade de moeda
    texto += ''.zfill(6) # 60-65 numero de aviso de débito
    texto += ''.ljust(165) # 66-230 uso o sicred
    texto += ''.ljust(10) # 231-240 código de ocorencia
    texto += '\n'
    #
    # Trailler do arquivo
    #
    texto += '748'.ljust(3) # 1-3 Código do banco na compensação
    texto += '9999' # 4-7
    texto += '9' # 8-8 Tipo de registro
    texto += ''.ljust(9) # 9-17 Uso exclusivo SICREDI
    texto += '000001'.zfill(6) # 18-23 Quantidade de lotes do arquivo
    texto += str(remessa.beneficiario.registro + 3).zfill(6)[:6]  # 24-29 Quantidade de registros
    texto += ''.zfill(6) # 30-35 Qtde de contas p/ conc. (lotes)
    texto += ''.ljust(205) # 36-240 Uso exclusivo SICREDI

    return self.tira_acentos(texto.upper())


def linha_remessa_240(self, remessa, funcionario):

    #
    # Seguimento A
    #

    texto = '748'.zfill(3) # 1-3 Código do banco na compensação

    texto += '0001'.zfill(4) # 4-7 Lote de serviço

    texto += '3' # 8-8 Tipo do registro
    texto += str(funcionario.registro).zfill(5) # 9-13 Nº seqüencial do registro no lote
    texto += 'A' # 14-14 Código de segmento do reg. detalhe
    texto += ''.zfill(1) # 15-15 Tipo de movimento ** verifica com empresa
    texto += ''.zfill(2) # 16-17 Código da instrução p/ movimento ** verifica com empresa
    texto += ''.zfill(3) # 18-20 Código da câmara centralizadora
    texto += '748'.zfill(3) # 21-23 Código do banco do favorecido
    texto += str(funcionario.agencia.numero).zfill(5) # 24-28 Ag. mantenedora da conta do favorecido
    texto += ''.ljust(1) # 29-29 Ag. Dígito verificador da agência
    texto += str(funcionario.conta.numero).zfill(12)[:12] # 30-41 Número da conta corrente
    texto += str(funcionario.conta.digito).ljust(1)[:1] # 42-42 Dígito verificador da conta
    texto += ''.ljust(1) # 43-43 Dígito verificador da ag./conta
    texto += funcionario.nome.ljust(30)[:30] # 44-73 Nome do favorecido
    texto +=  'ID_' + str(funcionario.holerite_id).zfill(17)[:20] # 74-93 Nº do docum. atribuído p/ empresa
    texto += remessa.data_debito.strftime(b'%d%m%Y') # 94-101 Data do pagamento
    texto += 'BRL'.ljust(3) # 102-104 Tipo da moeda
    texto += ''.zfill(15)[:15] # 105-119 Quantidade da moeda
    texto += str(int(funcionario.valor_creditar * 100)).zfill(15)[:15] # 120-134 Valor pagamento
    texto += ''.ljust(20) # 135-154 Nosso número Nº do docum. atribuído pelo banco
    texto += '00000000' # 155-162 Data real da efetivação pagto /  arquivo de retorno
    texto += ''.zfill(15)[:15]  #163-177 Valor real da efetivação do pagto
    texto += ''.ljust(40) # 178-217 Outras informações – vide formatação em G031 para identificação de depósito judicial e pagto. salários de servidores pelo SIAPE
    texto += ''.ljust(2) # 218-219 Compl. tipo serviço
    texto += ''.ljust(5) # 220-224 Código finalidade da TED
    texto += ''.ljust(2) # 225-226 Complemento de finalidade pagto
    texto += ''.ljust(3) # 227-229 Uso exclusivo SICREDI
    texto += ''.zfill(1) # 230-230 Aviso ao favorecido
    texto += ''.ljust(10) # 231-240 Códigos das ocorrências p/ retorno
    texto += '\n'

    #
    # Seguimento B
    #

    texto += '748'.zfill(3) # 1-3 Código do banco na compensação
    texto += '0001'.zfill(4) # 4-7  Lote de serviço
    texto += '3' # 8-8 Tipo do registro
    texto += str(funcionario.registro + 1 ).zfill(5) # 9-13 Nº seqüencial do registro no lote
    texto += 'B' # 14-14 Código de segmento do reg. detalhe
    texto += ''.ljust(3) #15-17 Uso da sicred

    if funcionario.tipo_pessoa == 'PJ':
        texto += '2'
    else:
        texto += '1'

    texto += limpa_formatacao(funcionario.cnpj_cpf).zfill(14)[:14] # 19-32 Nº de inscrição do favorecido
    texto += ''.ljust(30)[:30] # 33-62 Nome da rua, av, pça, etc
    texto += ''.ljust(5)[:5] # 63-67 Numero
    texto += ''.ljust(15)[:15] #68-82 Complemento
    texto += ''.ljust(15)[:15] # 83-97 Bairro
    texto += ''.ljust(20)[:20] # 98-117 Nome da cidade
    texto += ''.ljust(8) # 118-122 CEP
    texto += ''.ljust(2) # 126-127 Sigla Estado
    #texto += remessa.data_hora.strftime(b'%d%m%Y') # 128-135 Data do vencimento (nominal)
    texto += ''.zfill(8) # 128-135 Data do vencimento (nominal)
    texto += str(int(funcionario.valor_creditar * 100)).zfill(15)[:15] # 136-150 Valor documeneto
    texto += ''.zfill(15)[:15] # 151-165 Valor do abatimento
    texto += ''.zfill(15) # 166-180 Valor do desconto
    texto += ''.zfill(15) # 181-195 Valor da mora
    texto += ''.zfill(15) # 196-210 Valor da multa
    texto += ''.ljust(15) # 211-225 Código/documento do favorecido
    texto += ''.zfill(1) # 226-226  Aviso ao favorecido
    texto += ''.zfill(6) # 227-232 Uso exclusivo para o SIAPE
    texto += ''.ljust(8) # 233-240 Uso exclusivo SICREDI

    return self.tira_acentos(texto.upper())

