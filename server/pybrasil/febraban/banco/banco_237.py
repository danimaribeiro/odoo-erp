# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from decimal import Decimal as D
from pybrasil.data import parse_datetime
from pybrasil.febraban.boleto import Boleto
from pybrasil.inscricao import limpa_formatacao

def limpa_nome(texto):
    probibidos = u'.,-_;:?!=+*/&#$%{}[]()<>|@"\´`~^¨' + u"'"

    for c in probibidos:
        texto = texto.replace(c, ' ')

    while '  ' in texto:
        texto = texto.replace('  ', ' ')

    return texto


def calcula_digito_nosso_numero(self, boleto):
    boleto.banco.carteira = str(boleto.banco.carteira).zfill(2)
    boleto.nosso_numero = str(boleto.nosso_numero).zfill(11)
    return self.modulo11(boleto.banco.carteira + boleto.nosso_numero, pesos=range(2, 8), mapa_digitos={10: 'P', 11: 0})


def campo_livre(self, boleto):
    boleto.nosso_numero = str(boleto.nosso_numero).zfill(11)

    campo_livre = str(boleto.beneficiario.agencia.numero).zfill(4)
    campo_livre += str(boleto.banco.carteira).zfill(2)
    campo_livre += str(boleto.nosso_numero).zfill(11)
    campo_livre += str(boleto.beneficiario.conta.numero).zfill(7)
    campo_livre += '0'
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
    texto += str(beneficiario.codigo_beneficiario.numero).zfill(20)
    texto += beneficiario.nome.ljust(30)[:30]
    texto += '237'
    texto += 'BRADESCO'.ljust(15)
    texto += remessa.data_hora.strftime(b'%d%m%y')
    texto += ''.ljust(8)
    texto += 'MX'
    texto += str(remessa.sequencia).zfill(7)
    texto += ''.ljust(277)
    texto += str(1).zfill(6)

    return self.tira_acentos(texto.upper())


def trailler_remessa_400(self, remessa):
    #
    # Trailler do arquivo
    #
    texto = '9'
    texto += ''.ljust(393)
    texto += str(len(remessa.registros) + 1).zfill(6)  # Quantidade de registros

    return self.tira_acentos(texto.upper())


def linha_remessa_400(self, remessa, boleto):
    beneficiario = boleto.beneficiario
    banco = boleto.banco
    pagador = boleto.pagador

    #
    # 1º segmento
    #
    texto = '1'
    texto += '00000'
    texto += '0'
    texto += '00000'
    texto += '0000000'
    texto += '0'
    #
    # posições 21 a 37
    #
    texto += '0'
    texto += str(banco.carteira).zfill(3)
    texto += beneficiario.agencia.numero.zfill(5)
    texto += beneficiario.conta.numero.zfill(7)
    texto += beneficiario.conta.digito.zfill(1)

    texto += str(boleto.identificacao).ljust(25)
    texto += '000'  # Preencher com 237 somente se for débito automático

    if boleto.valor_multa > 0:
        texto += '2'
        percentual_multa = D(str(boleto.valor_multa)) / D(str(boleto.documento.valor)) * D('100')
        texto += str(int(percentual_multa * 100)).zfill(4)
    else:
        texto += '0'
        texto += '0000'

    texto += str(boleto.nosso_numero).zfill(11)
    texto += str(boleto.digito_nosso_numero).zfill(1)

    texto += ''.zfill(10)
    texto += '2'  # Beneficiário emite, banco registra
    texto += 'N'
    texto += ''.ljust(10)
    texto += ' '
    texto += '0'
    texto += '  '
    texto += boleto.comando or '01'  # Registro do boleto no banco
    texto += str(boleto.documento.numero).ljust(10)[:10]
    texto += boleto.data_vencimento.strftime('%d%m%y')
    texto += str(int(boleto.documento.valor * 100)).zfill(13)
    texto += '0'.zfill(3)
    texto += '0'.zfill(5)
    texto += '99'  # Tipo do documento - 99 outros
    texto += 'N'
    texto += boleto.data_processamento.strftime('%d%m%y')

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

    texto += str(int(boleto.valor_iof * 100)).zfill(13)
    texto += str(int(boleto.valor_abatimento * 100)).zfill(13)

    if pagador.tipo_pessoa == 'PJ':
        texto += '02'
    else:
        texto += '01'

    texto += pagador.cnpj_cpf_numero.zfill(14)
    texto += pagador.nome[:40].ljust(40)
    texto += pagador.endereco_numero_complemento.ljust(40)[:40]
    texto += ''.ljust(12)
    texto += pagador.cep.replace('-', '').zfill(8)
    texto += ''.ljust(60)  # Sacador/avalista - não existe mais
    texto += str(len(remessa.registros) + 1).zfill(6)  # nº do registro

    return self.tira_acentos(texto.upper())


def header_retorno_400(self, retorno):
    header = retorno.linhas[0]

    beneficiario = retorno.beneficiario

    #beneficiario.agencia.numero = header[26:30]
    #beneficiario.agencia.digito = header[30]
    beneficiario.codigo_beneficiario.numero = unicode(D(header[26:46]))
    #beneficiario.codigo_beneficiario.digito = header[39]
    beneficiario.nome = header[46:76]

    retorno.data_hora = parse_datetime(header[94:100]).date()
    retorno.sequencia = int(header[108:113])


def header_retorno_240(self, retorno):
    header = retorno.linhas[0]

    beneficiario = retorno.beneficiario

    beneficiario.cnpj_cpf = header[18:32]
    beneficiario.agencia.numero = header[52:57]
    beneficiario.agencia.digito = header[57]
    beneficiario.conta.numero = header[58:70]
    beneficiario.conta.digito = header[70]
    beneficiario.nome = header[72:102]
    retorno.data_hora = parse_datetime(header[143:151])
    retorno.sequencia = int(header[157:163])
    
def fp_header_retorno_240(self, retorno):
    header = retorno.linhas[0]

    beneficiario = retorno.beneficiario

    beneficiario.cnpj_cpf = header[18:32]
    beneficiario.agencia.numero = header[52:57]
    beneficiario.agencia.digito = header[57]
    beneficiario.conta.numero = header[58:70]
    beneficiario.conta.digito = header[70]
    beneficiario.nome = header[72:102]
    retorno.data_hora = parse_datetime(header[143:151])
    retorno.sequencia = int(header[157:163])
    
    
def fp_linha_retorno_240(self, retorno):
    beneficiario = retorno.beneficiario
    linha = retorno.linhas[1]

    #
    # Beneficiario
    #    
    beneficiario.codigo_beneficiario.numero = linha[64:71]
    beneficiario.conta.digito = linha[71]
    retorno.codigo_ocorrencia =  linha[230:240]

    for i in range(2, len(retorno.linhas) - 1):
        linha = retorno.linhas[i]
                
        if linha[13] == 'A':                    
            boleto = Boleto()           
            boleto.pagador.nome = linha[43:73] 
            boleto.identificacao = linha[73:93].replace('id ','ID_')            
            boleto.nosso_numero = linha[134:155]
            boleto.data_credito = parse_datetime(linha[154:162])
            boleto.valor_recebido = D(linha[163:177]) / D('100') 
            boleto.comando = linha[230:240]           
            retorno.boletos.append(boleto)
            
        elif linha[13] == 'B':
            boleto.pagador.cnpj_cpf = linha[21:32] 
            continue        
            

DESCRICAO_COMANDO_REMESSA = {
    '01': 'Registro de título',
    '02': 'Solicitação de baixa',
    '03': 'Pedido protesto falimentar',
    '04': 'Concessão de abatimento',
    '05': 'Cancelamento de abatimento',
    '06': 'Alteração de vencimento',
    '07': 'Alteração do número de controle',
    '08': 'Alteração de seu número',
    '09': 'Instrução para protestar',
    '18': 'Sustar protesto e baixar título',
    '19': 'Sustar protesto e manter título',
    '22': 'Transferência de cessão de crédito',
    '23': 'Transferência entre carteiras',
    '24': 'Devolução de transf. entre carteiras',
    '31': 'Alteração de outros dados',
    '68': 'Acerto do dados do rateio de crédito',
    '69': 'Cancelamento dos dados do rateio',
}


DESCRICAO_COMANDO_RETORNO = {
    '02': 'Confirmação de entrada do título',
    '03': 'Rejeição de entrada do título',
    '06': 'Liquidação normal',
    '09': 'Baixa de título',
    '10': 'Baixa a pedido do beneficiário',
    '11': 'Títulos em aberto',
    '12': 'Abatimento concedido',
    '13': 'Abatimento cancelado',
    '14': 'Alteração de vencimento',
    '15': 'Liquidação em cartório',
    '16': 'Liquidação com cheque',
    '17': 'Liquidação após baixa ou sem registro',
    '18': 'Acerto de depositária',
    '19': 'Instrução de protesto',
    '20': 'Sustação de protesto',
    '21': 'Acerto do controle do participante',
    '22': 'Pagamento cancelado',
    '23': 'Encaminhado a protesto',
    '24': 'Rejeitado - CEP irregular',
    '25': 'Instrução de protesto falimentar',
    '27': 'Baixa rejeitada',
    '28': 'Débito de tarifas',
    '29': 'Ocorrência do pagador',
    '30': 'Alteração de outros dados rejeitados',
    '32': 'Instrução rejeitada',
    '33': 'Confirmação pedido de alteração de outros dados',
    '34': 'Retirado do cartório e manutenção carteira',
    '35': 'Desagendamento do débito automático',
    '40': 'Estorno de pagamento',
    '55': 'Sustação judicial',
    '68': 'Acerto do dados do rateio de crédito',
    '69': 'Cancelamento dos dados do rateio',
}


COMANDOS_RETORNO_LIQUIDACAO = {
    '06': True,
    '15': True,
    #'16': False,
    '17': True,
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
    beneficiario.cnpj_cpf = linha[3:17]
    self.carteira = linha[23]
    beneficiario.agencia.numero = linha[25:29]
    beneficiario.conta.numero = linha[29:36]
    beneficiario.conta.digito = linha[36]

    for i in range(1, len(retorno.linhas) - 1):
        linha = retorno.linhas[i]
        boleto = Boleto()
        boleto.beneficiario = retorno.beneficiario
        boleto.banco = self

        boleto.identificacao = linha[37:62]
        boleto.nosso_numero = unicode(D(linha[70:81]))
        #boleto.nosso_numero_digito = linha[82]
        boleto.banco.carteira = linha[107]
        boleto.comando = linha[108:110]
        boleto.data_ocorrencia = parse_datetime(linha[110:116]).date()
        boleto.documento.numero = linha[116:126]
        if linha[146:152].strip() != '000000':
            boleto.data_vencimento = parse_datetime(linha[146:152]).date()
        boleto.documento.valor = D(linha[152:165]) / D('100')
        boleto.valor_despesa_cobranca = D(linha[175:188]) / D('100')
        #boleto.valor_outras_despesas = D(linha[188:201]) / D('100')
        boleto.valor_multa = D(linha[188:201]) / D('100')
        boleto.valor_iof = D(linha[214:227]) / D('100')
        boleto.valor_abatimento = D(linha[227:240]) / D('100')
        boleto.valor_desconto = D(linha[240:253]) / D('100')
        boleto.valor_recebido = D(linha[253:266]) / D('100')
        boleto.valor_juros = D(linha[266:279]) / D('100')
        boleto.valor_outros_creditos = D(linha[279:292]) / D('100')

        if len(linha[295:301].strip()) > 0 and linha[295:301] != '000000':
            boleto.data_credito = parse_datetime(linha[295:301]).date()

        boleto.pagador.cnpj_cpf = linha[342:357]

        retorno.boletos.append(boleto)


def header_remessa_200(self, remessa):
    beneficiario = remessa.beneficiario
    #
    # Header do arquivo
    #
    texto = '0'
    texto += '1'
    texto += 'REMESSA'
    texto += '03'
    texto += 'CREDITO C/C'.ljust(15)
    texto += str(beneficiario.agencia.numero).zfill(5)
    texto += '00705'  # código razão - 07.05 indica que é uma conta corrente de uma empresa
    texto += str(beneficiario.conta.numero).zfill(7)
    texto += str(beneficiario.conta.digito).zfill(1)
    texto += ' '
    texto += ' '
    texto += ''.ljust(5)  # código da empresa no banco
    texto += beneficiario.nome.ljust(25)[:25]
    texto += '237'
    texto += 'BRADESCO'.ljust(15)
    texto += remessa.data_hora.strftime(b'%d%m%Y')
    texto += '01600'
    texto += 'BPI'
    texto += remessa.data_debito.strftime(b'%d%m%Y')
    texto += ' '
    texto += 'N'
    texto += ''.ljust(74)
    texto += str(1).zfill(6)

    return self.tira_acentos(texto.upper())


def trailler_remessa_200(self, remessa):
    #
    # Trailler do arquivo
    #
    texto = '9'
    texto += str(int(remessa.valor_total * 100)).zfill(13)
    texto += ''.ljust(180)
    texto += str(len(remessa.registros) + 1).zfill(6)  # Quantidade de registros

    return self.tira_acentos(texto.upper())


def linha_remessa_200(self, remessa, funcionario):
    texto = '1'
    texto += ''.ljust(61)
    texto += str(funcionario.agencia.numero).zfill(5)
    texto += '07050'  # código razão - 07.05 indica que é uma conta corrente de uma empresa
    texto += str(funcionario.conta.numero).zfill(7)
    texto += str(funcionario.conta.digito).zfill(1)
    texto += ''.ljust(2)
    texto += funcionario.nome.ljust(38)[:38]
    texto += str(funcionario.matricula).zfill(6)
    texto += str(int(funcionario.valor_creditar * 100)).zfill(13)
    texto += '298'
    texto += ''.ljust(8)
    texto += ''.ljust(44)
    texto += str(len(remessa.registros) + 1).zfill(6)  # nº do registro

    return self.tira_acentos(texto.upper())


#
# Emissão de Comprovante Salarial – Layout 250 Posições
#


def header_remessa_250(self, remessa):
    beneficiario = remessa.beneficiario
    #
    # Header do arquivo
    #
    texto = '0'  # tipo registro
    texto += 'REMESSA HPAG EMPRESA' # descricao
    texto += str(beneficiario.conta.convenio).zfill(9)[:9]
    texto += str(remessa.sequencia).zfill(9)
    texto += limpa_formatacao(beneficiario.cnpj_cpf).zfill(15)[:15]
    texto += remessa.data_hora.strftime(b'%d%m%Y')
    texto += 'I'
    texto += '00777'
    texto += ''.ljust(155)
    texto += ' '
    texto += ''.ljust(9)
    texto += ''.ljust(12)
    texto += str(1).zfill(5)

    return self.tira_acentos(texto.upper())


def linha_remessa_250(self, remessa, holerite):

    texto = '1'
    texto += 'I'
    if holerite.tipo_comprovante == 'N':
        texto += '001' # PAGAMENTO MENSAL
    if holerite.tipo_comprovante == 'F':
        texto += '004' # PAGAMENTO DE FERIAS
    if holerite.tipo_comprovante == 'R':
        texto += '001' # PAGAMENTO MENSAL
    if holerite.tipo_comprovante == 'D':
        texto += '005' # 13 SALARIO
    if holerite.tipo_comprovante == 'A':
        texto += '001' # Aviso prévio
    if holerite.tipo_comprovante == 'M':
        texto += '009' # Licença maternidade

    texto += limpa_formatacao(holerite.mes_referencia)
    texto += holerite.data_liberacao.strftime(b'%d%m%Y')
    texto += '0237'
    texto += str(holerite.funcionario.agencia.numero).zfill(5)
    texto += str(holerite.funcionario.conta.numero).zfill(13)
    texto += str(holerite.funcionario.conta.digito).zfill(2)
    texto += limpa_formatacao(holerite.funcionario.cnpj_cpf_numero).zfill(11)[:11]
    texto += limpa_formatacao(holerite.funcionario.nis).ljust(14)[:14]
    texto += limpa_formatacao(holerite.funcionario.rg).ljust(13)[:13]
    print('carteira trabalho')
    print(holerite.funcionario.carteira_trabalho)
    texto += limpa_formatacao(holerite.funcionario.carteira_trabalho).ljust(9)[:9]
    texto += limpa_nome(holerite.funcionario.nome).ljust(30)[:30]
    texto += limpa_nome(holerite.funcionario.matricula).ljust(12)[:12]
    texto += limpa_nome(holerite.funcionario.funcao).ljust(40)[:40]
    texto += holerite.funcionario.data_admissao.strftime(b'%d%m%Y')
    texto += ''.ljust(53)
    texto += ''.ljust(12)
    reg = 1
    texto += str(len(remessa.registros) + reg).zfill(5)  # nº do registro
    reg += 1
    texto += '\n'

    for holerite_detalhe in holerite.holerite_detalhe:
        texto += '2'

        if holerite_detalhe.codigo_lancamento:
            texto += str(holerite_detalhe.codigo_lancamento).zfill(4)[:4]
        else:
            texto += ''.zfill(4)

        if holerite_detalhe.codigo_lancamento:
            texto += limpa_nome(holerite_detalhe.descricao_lancamento).ljust(20)[:20]
        else:
            texto += ''.zfill(20)

        texto += str(int(holerite_detalhe.valor_lancamento * 100)).zfill(12)
        texto += str(holerite_detalhe.identificador_lancamento).zfill(1)[:1]
        texto += ''.ljust(198)
        texto += ''.ljust(9)
        texto += str(len(remessa.registros) + reg).zfill(5)  # nº do registro
        reg += 1
        texto += '\n'

    texto += '4'

    if holerite.holerite_informacao.data_pagamemto:
        texto += holerite.holerite_informacao.data_pagamemto.strftime(b'%d%m%Y')
    else:
        texto += ''.zfill(8)

    texto += str(int(holerite.holerite_informacao.qtd_dep_irrf)).zfill(2)[:2]
    texto += str(int(holerite.holerite_informacao.qtd_dep_salario_familia)).zfill(2)[:2]
    texto += str(int(holerite.holerite_informacao.qtd_horas_trabalhadas)).zfill(2)[:2]
    texto += str(int(holerite.holerite_informacao.vr_salario_base * 100)).zfill(12)[:12]
    texto += str(int(holerite.holerite_informacao.qtd_falta_ferias or 0)).zfill(2)[:2]
    texto += 'S'

    if holerite.holerite_informacao.data_inicio_periodo_aquisitivo:
        texto += holerite.holerite_informacao.data_inicio_periodo_aquisitivo.strftime(b'%d%m%Y')
    else:
        texto += ''.zfill(8)

    if holerite.holerite_informacao.data_fim_periodo_aquisitivo:
        texto += holerite.holerite_informacao.data_fim_periodo_aquisitivo.strftime(b'%d%m%Y')
    else:
        texto += ''.zfill(8)

    if holerite.holerite_informacao.data_inicio_periodo_gozo:
        texto += holerite.holerite_informacao.data_inicio_periodo_gozo.strftime(b'%d%m%Y')
    else:
        texto += ''.zfill(8)

    if holerite.holerite_informacao.data_fim_periodo_gozo:
        texto += holerite.holerite_informacao.data_fim_periodo_gozo.strftime(b'%d%m%Y')
    else:
        texto += ''.zfill(8)

    texto += str(int(holerite.holerite_informacao.vr_base_inss * 100)).zfill(12)[:12]
    texto += str(int(holerite.holerite_informacao.vr_base_inss_13 * 100)).zfill(12)[:12]
    texto += str(int(holerite.holerite_informacao.vr_base_irrf_salario * 100)).zfill(12)[:12]
    texto += str(int(holerite.holerite_informacao.vr_base_irrf_13 * 100)).zfill(12)[:12]
    texto += str(int(holerite.holerite_informacao.vr_base_irrf_ferias * 100)).zfill(12)[:12]
    texto += str(int(holerite.holerite_informacao.vr_base_irrf_ppr * 100)).zfill(12)[:12]
    texto += str(int(holerite.holerite_informacao.vr_base_fgts * 100)).zfill(12)[:12]
    texto += str(int(holerite.holerite_informacao.vr_fgts * 100)).zfill(12)[:12]
    texto += ''.ljust(78)
    texto += ''.ljust(9)
    texto += str(len(remessa.registros) + reg).zfill(5)  # nº do registro
    reg += 1
    texto += '\n'

    texto += '5'
    texto += str(len(holerite.holerite_detalhe) + 1).zfill(5)[:5]
    texto += ''.ljust(239)
    texto += str(len(remessa.registros) + reg).zfill(5)  # nº do registro

    return self.tira_acentos(texto.upper())


def trailler_remessa_250(self, remessa):
    #
    # Trailler do arquivo
    #
    texto = '9'
    texto += str(len(remessa.registros) + 1).zfill(5)  # Quantidade de registros
    texto += ''.ljust(239)
    texto += str(len(remessa.registros) + 1).zfill(5)  # nº do registro

    return self.tira_acentos(texto.upper())



def header_remessa_500(self, remessa):
    beneficiario = remessa.beneficiario
    #
    # Header do arquivo
    #
    texto = '0'  # tipo registro
    texto += str(beneficiario.conta.convenio).zfill(8)[:8]
    texto += '1'  # CNPJ
    texto += limpa_formatacao(beneficiario.cnpj_cpf).zfill(15)[:15]
    texto += beneficiario.nome.ljust(40)[:40]
    texto += '20'
    texto += '1'
    texto += str(remessa.sequencia).zfill(5)
    texto += '00000'
    texto += remessa.data_hora.strftime(b'%Y%m%d')
    texto += remessa.data_hora.strftime(b'%H%M%S')
    texto += ''.ljust(5)
    texto += ''.ljust(3)
    texto += ''.ljust(5)
    texto += ''.ljust(1)
    texto += ''.ljust(74)
    texto += ''.ljust(80)
    texto += ''.ljust(217)
    texto += str(remessa.sequencia).zfill(9)
    texto += ''.ljust(8)
    texto += str(1).zfill(6)

    return self.tira_acentos(texto.upper())


def trailler_remessa_500(self, remessa):
    beneficiario = remessa.beneficiario
    #
    # Header do arquivo
    #
    texto = '9'  # tipo registro
    texto += str(len(remessa.registros) + 1).zfill(6)  # nº do registro
    texto += str(int(remessa.valor_total * 100)).zfill(17)[:17]
    texto += ''.ljust(470)
    texto += str(len(remessa.registros) + 1).zfill(6)  # nº do registro

    return self.tira_acentos(texto.upper())



#
#
#
#
###################### Folha de Pagamento BRADESCO 240 FEBRABAN #############################
#
#
#


def header_remessa_240(self, remessa):
    beneficiario = remessa.beneficiario
    banco = beneficiario.banco

    #
    # Header do arquivo
    #

    texto = '237'.ljust(3) # 01-03 Código do banco na compensação
    texto += '0000' # 4-7 Lote de serviço
    texto += '0' # 8-8 Tipo de registro
    texto += ''.ljust(9)  # 9-17 uso bradesco
    texto += '2' # 18-18 ipo de inscrição da empresa
    texto += limpa_formatacao(beneficiario.cnpj_cpf).zfill(14) # 19-32 Número de inscrição da empresa
    texto += str(beneficiario.conta.convenio).ljust(20) # 33-52 Código do convênio no banco
    texto += str(beneficiario.agencia.numero).zfill(5) # 53-57Agência mantenedora da conta
    texto += str(beneficiario.agencia.digito).zfill(1)  # 58-58 Dígito verificador da agência
    texto += str(beneficiario.conta.numero).zfill(12)  # 59-70 Número da conta corrente empresa
    texto += str(beneficiario.conta.digito).zfill(1)  # 71-71 Dígito verificador da conta
    texto += ''.ljust(1)  # 72-72 Dígito verificador da Ag/conta
    texto += beneficiario.nome.ljust(30)[:30] # 73-102 Nome da empresa
    texto += 'Bradesco'.ljust(30)[:30]  # 103-132 Nome do banco
    texto += ''.ljust(10)  # 133-142 uso bradesco
    texto += '1'.zfill(1)  # 143-143 Código remessa / retorno
    texto += remessa.data_hora.strftime(b'%d%m%Y') # 144-151 DATA DO ARQUIVO
    texto += remessa.data_hora.strftime(b'%H%M%S')[:6] # 152-157 HORA DO ARQUIVO
    texto += str(remessa.sequencia).zfill(6) # 158-163 Número seqüencial do arquivo
    texto += '080' # 164-166 No da versão do leiaute do arquivo
    texto += '1600'.zfill(5) # 167-171 Densidade de gravação do arquivo
    texto += ''.ljust(20) # 172-191 Para uso reservado da empresa
    texto += ''.ljust(20) # 192-211 Para uso reservado da empresa
    texto += ''.ljust(29) # 212-240 Uso exclusivo bradesco
    texto += '\n'

    #
    # Header do lote
    #

    texto += '237'.ljust(3) # 1-3 Código do banco na compensação
    texto += '0001'.zfill(4) # 4-7 Lote de serviço
    texto += '1' # 8-8 Tipo de registro
    texto += 'C' # 9-9 Tipo da operação
    texto += '30'.zfill(2)  # 10-11 Tipo do serviço
    texto += '01'.zfill(2)  # 12-13  Forma de lançamento
    texto += '040'  # 14-16 Nº da versão do leiaute do lote
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
    texto += ''.ljust(8)  # 223-230  uso Bradesco
    texto += ''.ljust(10)  # 231-240 ocorrencia / retorno

    return self.tira_acentos(texto.upper())


def trailler_remessa_240(self, remessa):

    #
    # Trailler do lote
    #
    texto = '237'.ljust(3) # 1-3 Código do banco na compensação
    texto += '0001'.ljust(4) # 4-7 Lote de Serviço
    texto += '5' # 8-8
    texto += ''.ljust(9) # 9-17 uso o bradesco
    texto += str(remessa.beneficiario.registro + 1).zfill(6)[:6]  # 18-23 Quantidade de registros
    texto += str(int(remessa.beneficiario.valor_total * 100)).zfill(18)[:18] # 24-41 somatória dos valores
    texto += ''.zfill(18) # 42-59 somatória de quantidade de moeda
    texto += ''.zfill(6) # 60-65 numero de aviso de débito
    texto += ''.ljust(165) # 66-230 uso o bradesco
    texto += ''.ljust(10) # 231-240 código de ocorencia
    texto += '\n'
    #
    # Trailler do arquivo
    #
    texto += '237'.ljust(3) # 1-3 Código do banco na compensação
    texto += '9999' # 4-7
    texto += '9' # 8-8 Tipo de registro
    texto += ''.ljust(9) # 9-17 Uso exclusivo bradesco
    texto += '000001'.zfill(6) # 18-23 Quantidade de lotes do arquivo
    texto += str(remessa.beneficiario.registro + 3).zfill(6)[:6]  # 24-29 Quantidade de registros
    texto += ''.zfill(6) # 30-35 Qtde de contas p/ conc. (lotes)
    texto += ''.ljust(205) # 36-240 Uso exclusivo SICREDI

    return self.tira_acentos(texto.upper())


def linha_remessa_240(self, remessa, funcionario):

    #
    # Seguimento A
    #

    texto = '237'.zfill(3) # 1-3 Código do banco na compensação

    texto += '0001'.zfill(4) # 4-7 Lote de serviço

    texto += '3' # 8-8 Tipo do registro
    texto += str(funcionario.registro).zfill(5) # 9-13 Nº seqüencial do registro no lote
    texto += 'A' # 14-14 Código de segmento do reg. detalhe
    texto += '0'.zfill(1) # 15-15 Tipo de movimento ** verifica com empresa
    texto += '00'.zfill(2) # 16-17 Código da instrução p/ movimento ** verifica com empresa
    texto += ''.zfill(3) # 18-20 Código da câmara centralizadora
    texto += '237'.zfill(3) # 21-23 Código do banco do favorecido
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
    texto += ''.ljust(3) # 227-229 Uso exclusivo bradesco
    texto += '6'.zfill(1) # 230-230 Aviso ao favorecido
    texto += ''.ljust(10) # 231-240 Códigos das ocorrências p/ retorno
    texto += '\n'

    #
    # Seguimento B
    #

    texto += '237'.zfill(3) # 1-3 Código do banco na compensação
    texto += '0001'.zfill(4) # 4-7  Lote de serviço
    texto += '3' # 8-8 Tipo do registro
    texto += str(funcionario.registro + 1 ).zfill(5) # 9-13 Nº seqüencial do registro no lote
    texto += 'B' # 14-14 Código de segmento do reg. detalhe
    texto += ''.ljust(3) #15-17 Uso da bradesco

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
    texto += remessa.data_hora.strftime(b'%d%m%Y') # 128-135 Data do vencimento (nominal)     
    texto += str(int(funcionario.valor_creditar * 100)).zfill(15)[:15] # 136-150 Valor documeneto
    texto += ''.zfill(15) # 151-165 Valor do abatimento
    texto += ''.zfill(15) # 166-180 Valor do desconto
    texto += ''.zfill(15) # 181-195 Valor da mora
    texto += ''.zfill(15) # 196-210 Valor da multa    
    texto += ''.ljust(15) # 211-225 Código/documento do favorecido    
    texto += ''.ljust(15) # 211-225 Código/documento do favorecido        

    return self.tira_acentos(texto.upper())


CODIGO_RETORNO_FP = {
    '00': u'Crédito ou Débito Efetivado - Este código indica que o pagamento foi confirmado',
    '01': u'Insuficiência de Fundos - Débito Não Efetuado',
    '02': u'Crédito ou Débito Cancelado pelo Pagador/Credor',
    '03': u'Débito Autorizado pela Agência - Efetuado',
    'AA': u'Controle Inválido',
    'AB': u'Tipo de Operação Inválido',
    'AC': u'Tipo de Serviço Inválido',
    'AD': u'Forma de Lançamento Inválida',
    'AE': u'Tipo/Número de Inscrição Inválido',
    'AF': u'Código de Convênio Inválido',
    'AG': u'Agência/Conta Corrente/DV Inválido',
    'AH': u'Nº Seqüencial do Registro no Lote Inválido',
    'AI': u'Código de Segmento de Detalhe Inválido',
    'AJ': u'Tipo de Movimento Inválido',
    'AK': u'Código da Câmara de Compensação do Banco Favorecido/Depositário Inválido',
    'AL': u'Código do Banco Favorecido ou Depositário Inválido',
    'AM': u'Agência Mantenedora da Conta Corrente do Favorecido Inválida',
    'AN': u'Conta Corrente/DV do Favorecido Inválido',
    'AO': u'Nome do Favorecido Não Informado',
    'AP': u'Data Lançamento Inválido',
    'AQ': u'Tipo/Quantidade da Moeda Inválido',
    'AR': u'Valor do Lançamento Inválido',
    'AS': u'Aviso ao Favorecido - Identificação Inválida',
    'AT': u'Tipo/Número de Inscrição do Favorecido Inválido',
    'AU': u'Logradouro do Favorecido Não Informado',
    'AV': u'Nº do Local do Favorecido Não Informado',
    'AW': u'Cidade do Favorecido Não Informada',
    'AX': u'CEP/Complemento do Favorecido Inválido',
    'AY': u'Sigla do Estado do Favorecido Inválida',
    'AZ': u'Código/Nome do Banco Depositário Inválido',
    'BA': u'Código/Nome da Agência Depositária Não Informado',
    'BB': u'Seu Número Inválido',
    'BC': u'Nosso Número Inválido',
    'BD': u'Inclusão Efetuada com Sucesso',
    'BE': u'Alteração Efetuada com Sucesso',
    'BF': u'Exclusão Efetuada com Sucesso',
    'BG': u'Agência/Conta Impedida Legalmente',
    'BH': u'Empresa não pagou salário',
    'BI': u'Falecimento do mutuário',
    'BJ': u'Empresa não enviou remessa do mutuário',
    'BK': u'Empresa não enviou remessa no vencimento',
    'BL': u'Valor da parcela inválida',
    'BM': u'Identificação do contrato inválida',
    'BN': u'Operação de Consignação Incluída com Sucesso',
    'BO': u'Operação de Consignação Alterada com Sucesso',
    'BP': u'Operação de Consignação Excluída com Sucesso',
    'BQ': u'Operação de Consignação Liquidada com Sucesso',
    'CA': u'Código de Barras - Código do Banco Inválido',
    'CB': u'Código de Barras - Código da Moeda Inválido',
    'CC': u'Código de Barras - Dígito Verificador Geral Inválido',
    'CD': u'Código de Barras - Valor do Título Inválido',
    'CE': u'Código de Barras - Campo Livre Inválido',
    'CF': u'Valor do Documento Inválido',
    'CG': u'Valor do Abatimento Inválido',
    'CH': u'Valor do Desconto Inválido',
    'CI': u'Valor de Mora Inválido',
    'CJ': u'Valor da Multa Inválido',
    'CK': u'Valor do IR Inválido',
    'CL': u'Valor do ISS Inválido',
    'CM': u'Valor do IOF Inválido',
    'CN': u'Valor de Outras Deduções Inválido',
    'CO': u'Valor de Outros Acréscimos Inválido',
    'CP': u'Valor do INSS Inválido',
    'HA': u'Lote Não Aceito',
    'HB': u'Inscrição da Empresa Inválida para o Contrato',
    'HC': u'Convênio com a Empresa Inexistente/Inválido para o Contrato',
    'HD': u'Agência/Conta Corrente da Empresa Inexistente/Inválido para o Contrato',
    'HE': u'Tipo de Serviço Inválido para o Contrato',
    'HF': u'Conta Corrente da Empresa com Saldo Insuficiente',
    'HG': u'Lote de Serviço Fora de Seqüência',
    'HH': u'Lote de Serviço Inválido',
    'HI': u'Arquivo não aceito',
    'HJ': u'Tipo de Registro Inválido',
    'HK': u'Código Remessa / Retorno Inválido',
    'HL': u'Versão de layout inválida',
    'HM': u'Mutuário não identificado',
    'HN': u'Tipo do beneficio não permite empréstimo',
    'HO': u'Beneficio cessado/suspenso',
    'HP': u'Beneficio possui representante legal',
    'HQ': u'Beneficio é do tipo PA (Pensão alimentícia)',
    'HR': u'Quantidade de contratos permitida excedida',
    'HS': u'Beneficio não pertence ao Banco informado',
    'HT': u'Início do desconto informado já ultrapassado',
    'HU': u'Número da parcela inválida',
    'HV': u'Quantidade de parcela inválida',
    'HW': u'Margem consignável excedida para o mutuário dentro do prazo do contrato',
    'HX': u'Empréstimo já cadastrado',
    'HY': u'Empréstimo inexistente',
    'HZ': u'Empréstimo já encerrado',
    'H1': u'Arquivo sem trailer',
    'H2': u'Mutuário sem crédito na competência',
    'H3': u'Não descontado – outros motivos',
    'H4': u'Retorno de Crédito não pago',
    'H5': u'Cancelamento de empréstimo retroativo',
    'H6': u'Outros Motivos de Glosa',
    'H7': u'Margem consignável excedida para o mutuário acima do prazo do contrato',
    'H8': u'Mutuário desligado do empregador',
    'H9': u'Mutuário afastado por licença',
    'TA': u'Lote Não Aceito - Totais do Lote com Diferença',
    'YA': u'Título Não Encontrado',
    'YB': u'Identificador Registro Opcional Inválido',
    'YC': u'Código Padrão Inválido',
    'YD': u'Código de Ocorrência Inválido',
    'YE': u'Complemento de Ocorrência Inválido',
    'YF': u'Alegação já Informada',
    '  ': u'',
}

