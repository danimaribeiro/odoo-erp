# -*- coding: utf-8 -*-


from pybrasil.inscricao import *

arqs = [
    'pagamentos.txt',
]

#print('delete from importa_finan;')

cnpjs = []

parciais = {
    '1303180103': 26,
    '1303100003': 58,
    '1303309301': 128,
    '1303329103': 172,
    '1303296101': 190,
    '1200369002': 305,
    '1303247201': 371,
    '1303112002': 541,
    '1303329101': 628,
    '1303122401': 756,
    '1303309302': 801,
    '1303282201': 848,
    '1303296102': 882,
    '1302858901': 914,
    '1303138403': 1021,
    '1303246301': 1107,
    '1302723803': 1134,
    '1303180102': 1166,
    '1303112003': 1258,
    '1303283201': 1341,
    '1303235601': 1342,
    '1303329102': 1352,
    '1303297101': 1381,
    '1303297601': 1382,
    '0100546002': 1405,
    '1303181003': 1433,
    '1303307001': 1526,
    '1303308801': 1533,
    '1303309303': 1537,
    '1303312401': 1541,
    '1303296103': 1619,
    '1302199801': 1663,
    '1303112001': 1752,
    '1303327101': 1816,
    '2100123501': 1884,
    '2100120702': 1891,
    '2100123001': 1893,
    '2100139401': 1895,
    '2452': 3694,
}

for nome_arq in arqs:
    arq = open(nome_arq, 'r')
    #print(nome_arq)
    i = 1
    for linha in arq.readlines():
        linha = linha.replace(';\n', '')
        linha = linha.replace(';\r\n', '')
        if linha[-1] == ';':
            linha = linha[:-1]
        if not linha:
            continue
        campos = linha.split(';')
        #print(i, linha, campos)
        i += 1
        cnpj_empresa, tipo, cnpj_partner, documento_id, data_documento, numero_documento, banco_id, data_quitacao, valor_documento, juros, multa, desconto, valor, data_conciliacao = campos

        if numero_documento not in parciais:
            continue

        lancamento_id = parciais[numero_documento]

        try:
            if (not banco_id) or int(banco_id) <= 0:
                banco_id = 'null'
        except:
            banco_id = 'null'

        if valida_cnpj(cnpj_partner):
            cnpj_partner = formata_cnpj(cnpj_partner)
        elif valida_cpf(cnpj_partner):
            cnpj_partner = formata_cpf(cnpj_partner)

        if valida_cnpj(cnpj_empresa):
            cnpj_empresa = formata_cnpj(cnpj_empresa)

        if cnpj_partner not in cnpjs:
            cnpjs.append(cnpj_partner)

        texto = "insert into importa_finan (create_date, create_uid, cnpj_empresa, tipo, cnpj_partner, documento_id, data_documento, numero_documento, valor_documento, data_vencimento, conta_antiga, carteira_id, nosso_numero, valor_juros, valor_multa, valor_desconto, valor_saldo, partner_id, company_id) values ('2014-08-31', 1, '{cnpj_empresa}', '{tipo}', '{cnpj_partner}', {documento_id}, '{data_documento}', '{numero_documento}', {valor_documento}, '{data_vencimento}', {conta_antiga}, {carteira_id}, '{nosso_numero}', {juros}, {multa}, {desconto}, {saldo}, (select id from res_partner where cnpj_cpf = '{cnpj_partner}' limit 1), (select id from res_company where cnpj_cpf = '{cnpj_empresa}' limit 1));"
        #texto = "update importa_finan set carteira_id = 11 where cnpj_empresa = '{cnpj_empresa}' and cnpj_partner = '{cnpj_partner}' and tipo = '{tipo}' and data_documento = '{data_documento}' and numero_documento = '{numero_documento}' and carteira_id = 3;"

        dados = {
            'cnpj_empresa': cnpj_empresa,
            'tipo': tipo,
            'cnpj_partner': cnpj_partner,
            'documento_id': documento_id,
            'data_documento': data_documento,
            'numero_documento': numero_documento,
            'valor_documento': valor_documento,
            'data_vencimento': data_vencimento,
            'conta_antiga': conta_antiga,
            'carteira_id': carteira_id,
            'nosso_numero': nosso_numero,
            'juros': juros,
            'multa': multa,
            'desconto': desconto,
            'saldo': saldo,
        }

        print(texto.format(**dados).encode('utf-8'))

    arq.close()

#for cnpj in cnpjs:
    #print("update importa_finan if set partner_id = (select p.id from res_partner p where p.cnpj_cpf = '{cnpj_partner}' order by p.id limit 1) where if.cnpj_partner = '{cnpj_partner}';".format(cnpj_partner=cnpj))


#print('update importa_finan if set company_id = (select c.company_id from finan_contrato c join res_company cc on cc.id = c.company_id join res_partner p on p.id = cc.partner_id where c.partner_id = if.partner_id  and p.cnpj_cpf = if.cnpj_empresa  order by c.company_id limit 1);')
#print('update importa_finan if set company_id = (select cc.id from res_company cc join res_partner p on p.id = cc.partner_id where p.cnpj_cpf = if.cnpj_empresa order by p.name limit 1);')
