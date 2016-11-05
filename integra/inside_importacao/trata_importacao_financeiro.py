# -*- coding: utf-8 -*-


from pybrasil.inscricao import *

arqs = [
    #'prottege_pagar.csv',
    'prottege_receber.csv',
]

#print('delete from importa_finan;')

cnpjs = []


for nome_arq in arqs:
    arq = open(nome_arq, 'r')
    #print(nome_arq)
    i = 1
    for linha in arq.readlines():
        linha = linha.replace('\r\n', '')
        linha = linha.replace('\n', '')
        linha = linha.replace('\xef\xbb\xbf', '')
        linha = linha.decode('utf-8')

        if linha[-1] == ';':
            linha = linha[:-1]

        if not linha:
            continue

        campos = linha.split(';')
        #print(i, linha, campos)
        i += 1
        cnpj_empresa, tipo, cnpj_partner, nome_partner, documento_id, data_documento, numero_documento, valor_documento, data_vencimento, conta_antiga, carteira_id, nosso_numero, juros, multa, desconto, saldo = campos

        if float(saldo.replace(',', '.')) == 0:
            continue

        try:
            if (not carteira_id) or carteira_id == 'null':
                carteira_id = ''
        except:
            carteira_id = ''

        #if tipo != 'R':
            #continue

        #elif carteira_id == '1':
            #carteira_id = '3'

        #if carteira_id != '1':
            #continue

        if valida_cnpj(cnpj_partner):
            cnpj_partner = formata_cnpj(cnpj_partner)
        elif valida_cpf(cnpj_partner):
            cnpj_partner = formata_cpf(cnpj_partner)

        if valida_cnpj(cnpj_empresa):
            cnpj_empresa = formata_cnpj(cnpj_empresa)

        if cnpj_partner not in cnpjs:
            cnpjs.append(cnpj_partner)

        texto = u"insert into importa_finan (create_date, create_uid, cnpj_empresa, tipo, cnpj_partner, nome_partner, documento_antigo, data_documento, numero_documento, valor_documento, data_vencimento, conta_antiga, carteira_antiga, nosso_numero, valor_juros, valor_multa, valor_desconto, valor_saldo, partner_id, company_id) values ('2014-08-31', 1, '{cnpj_empresa}', '{tipo}', '{cnpj_partner}', '{nome_partner}','{documento_antigo}', '{data_documento}', '{numero_documento}', {valor_documento}, '{data_vencimento}', '{conta_antiga}', '{carteira_antiga}', '{nosso_numero}', {juros}, {multa}, {desconto}, {saldo}, (select id from res_partner where cnpj_cpf = '{cnpj_partner}' limit 1), (select id from res_company where cnpj_cpf = '{cnpj_empresa}' limit 1));"
        #texto = "update importa_finan set carteira_id = 11 where cnpj_empresa = '{cnpj_empresa}' and cnpj_partner = '{cnpj_partner}' and tipo = '{tipo}' and data_documento = '{data_documento}' and numero_documento = '{numero_documento}' and carteira_id = 3;"

        dados = {
            'cnpj_empresa': cnpj_empresa,
            'tipo': tipo,
            'nome_partner': nome_partner.strip().replace("'", ' ')[:60],
            'cnpj_partner': cnpj_partner,
            'documento_antigo': documento_id,
            'data_documento': data_documento,
            'numero_documento': numero_documento,
            'valor_documento': valor_documento.replace(',', '.'),
            'data_vencimento': data_vencimento,
            'conta_antiga': conta_antiga,
            'carteira_antiga': carteira_id,
            'nosso_numero': nosso_numero.strip(),
            'juros': juros.replace(',', '.'),
            'multa': multa.replace(',', '.'),
            'desconto': desconto.replace(',', '.'),
            'saldo': saldo.replace(',', '.'),
        }

        print(texto.format(**dados).encode('utf-8'))

    arq.close()

#for cnpj in cnpjs:
    #print("update importa_finan if set partner_id = (select p.id from res_partner p where p.cnpj_cpf = '{cnpj_partner}' order by p.id limit 1) where if.cnpj_partner = '{cnpj_partner}';".format(cnpj_partner=cnpj))


#print('update importa_finan if set company_id = (select c.company_id from finan_contrato c join res_company cc on cc.id = c.company_id join res_partner p on p.id = cc.partner_id where c.partner_id = if.partner_id  and p.cnpj_cpf = if.cnpj_empresa  order by c.company_id limit 1);')
#print('update importa_finan if set company_id = (select cc.id from res_company cc join res_partner p on p.id = cc.partner_id where p.cnpj_cpf = if.cnpj_empresa order by p.name limit 1);')
