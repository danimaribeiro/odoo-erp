# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from pybrasil.base import escape_xml


VARIAVEIS = {

    #'AVPF': '${ holerite.data_afastamento }',
    #'AVPI': '${ holerite.data_aviso_previo }',
    #'BASE': 'Base INSS da empresa',
    'BOPT': '${ empregado.bank_id.bic }',
    'BairroCli': '${ empresa.bairro }',
    'BairroFil': '${ empresa.bairro }',
    'CHAPEIRA': '${ contrato.name }',
    'CID-UF-FILIAL': '${ empresa.cidade } - ${ empresa.estado }',
    'CIDADE_UF_CAB': '${ empresa.cidade } - ${ empresa.estado }',
    'CIDFILIAL': '${ empresa.cidade }',
    'CID_UF_FUN': '${ empregado.cidade } - ${ empregado.estado }',
    'CNPJCAB': '${ empresa.cnpj_cpf }',
    'CNPJCli': '${ empresa.cnpj_cpf }',
    'CNPJFil': '${ empresa.cnpj_cpf }',
    'CODFUN': '${ contrato.name }',
    'CONT': '',
    'CPF': '${ empregado.cpf }',
    'CPFAUT': '${ empregado.cpf }',
    'CPFResp': '',
    'CPFRespAss': '',
    'CPFTest': '',
    'CPFTest2': '',
    'CTPS': '${ empregado.carteira_trabalho_numero }',
    'CidadeCli': '${ empresa.cidade }',
    'CidadeFil': '${ empresa.cidade }',
    'CidadeResp': '${ empresa.cidade }',
    'ComplementoCli': '${ empresa.complemento }',
    'ConselhoResp': '',
    'DOPT': '${ formata_data(contrato.data_opcao_fgts) }',
    'DTNASC': '${ formata_data(empregado.data_nascimento) }',
    'Data': '${ formata_data(contrato.date_start) }',
    'data': '${ formata_data(contrato.date_start) }',
    'DATA': '${ formata_data(contrato.date_start) }',
    'DATA_AVISO': '${ formata_data(paysplip.data_aviso_previo) }',
    'DATA_RESCISAO': '${ formata_data(contrato.date_end) if contrato.date_end else "" }',
    'DataContrato': '${ formata_data(contrato.date_start) }',
    'DataExt': '${ data_por_extenso(hoje()) }',
    'EMPRESACAB': '${ empresa.razao_social }',
    'ENDERECOCAB': '${ empresa.endereco }, ${ empresa.numero }${ " - " + empresa.complemento if empresa.complemento else "" } - ${ empresa.bairro } - ${ empresa.cidade } - ${ empresa.estado } - ${ empresa.cep }',
    #'ENDFUN': '${ empregado.endereco }, ${ empregado.numero }${ " - " + empregado.complemento if empregado.complemento else "" } - ${ empregado.bairro } - ${ empregado.cidade } - ${ empregado.estado } - ${ empregado.cep }',
    'MILIT': '${ empregado.carteira_reservista }',
    'CIDFUN': '${ empregado.cidade }',
    'ENDFUN': '${ empregado.endereco }, ${ empregado.numero }',
    'ESCALA': '12 x 36',
    'ESTCIVIL': '${ ESTADO_CIVIL[empregado.estado_civil] }',
    'EXADM': '${ formata_data(contrato.date_start) }',
    'EXTCONTRATO': "${ formata_data(contrato.final_prim_esperiencia) }",
    'EXTEXP1': "${ formata_data(contrato.final_prim_esperiencia) }",
    'EXTEXP2': "${ formata_data(contrato.final_seg_esperiencia) }",
    'EXTLIQD': '',
    'EXTPRORROGA': "${ formata_data(contrato.final_seg_esperiencia) }",
    'EnderecoCli': '${ empresa.endereco }, ${ empresa.numero }',
    'EnderecoFil': '${ empresa.endereco }, ${ empresa.numero }',
    'EstadoCli': '${ empresa.estado }',
    'EstadoResp': '${ empresa.estado }',
    'Extensovenc1': '${ formata_data(contrato.date_start) }',
    'FPG': '${ UNIDADE_SALARIO[contrato.unidade_salario] }',
    'Funcao': '${ contrato.job_id.name }',
    'FUNCAO': '${ contrato.job_id.name }',
    'CARGO': '${ contrato.job_id.name }',
    'CBO': '${ contrato.job_id.cbo_id.codigo }',
    'HOR01': '',
    'HOR02': '',
    'HORARIO': '',
    'IDD': '${ idade(empregado.data_nascimento, contrato.date_start) }',
    'INSCRINSS': '${ empregado.cpf }',
    'INSS': '',
    'INTERVALO': '',
    'IRRF': '',
    'ISS': '',
    'InfoResp': '',
    'InscricaoCli': '',
    'LIQD': '',
    'MAE': '${ empregado.nome_mae }',
    'NACION': '${ empregado.pais_nacionalidade_id.nome }',
    'NACIONALIDADE': '${ empregado.pais_nacionalidade_id.nome }',
    'NACIONALIDADEP': '${ empregado.pais_nacionalidade_id.nome }',
    'NATURAL': '${ empregado.municipio_nascimento_id.nome } - ${ empregado.municipio_nascimento_id.estado_id.uf }',
    'NOMEAUT': '${ empregado.nome }',
    'NRRECB': '',
    'NmFun': '${ empregado.nome }',
    'NomeCli': '',
    'NomeCliAss': '',
    'NomeFil': '',
    'NomeFilAss': '',
    'NomeResp': '',
    'NomeRespAss': '',
    'NomeTest': '',
    'NomeTest2': '',
    'NumeroCli': '',
    'NumeroFil': '',
    'OPT': 'SIM',
    'OUTR': '',
    'PAI': '${ empregado.nome_pai }',
    'PIS': '${ empregado.nis }',
    'POLICFED': '',
    'PessoaCli': 'J',
    'RG': '${ empregado.rg_numero }',
    'RGResp': '',
    'RGRespAss': '',
    'RespCli': '',
    'SERC': '${ empregado.carteira_trabalho_serie }',
    'SERCART': '${ empregado.carteira_trabalho_serie }',
    'SERV': '',
    'SalExtenso': '${ valor_por_extenso_unidade(contrato.wage or 0) }',
    'TERC': '',
    'TIPOSANG': '${ empregado.tipo_sanguineo }',
    'TIT': '${ empregado.numero_titulo_eleitor }',
    'TOMADOR': '${ contrato.department_id.name }',
    'DEPARTAMENTO': '${ contrato.department_id.name }',
    'UFC': '${ empregado.carteira_trabalho_estado }',
    'UFFILIAL': '${ empresa.estado }',
    'ValorContrato': '',
    'ValorContratoExt': '',
    'salario': '${ formata_valor(contrato.wage) }',
    'Salario': '${ formata_valor(contrato.wage) }',
    'venc1': '${ formata_data(contrato.final_prim_esperiencia) }',
    'venc2': '${ formata_data(contrato.final_seg_esperiencia) }',
    'PostoServico': '${ contrato.lotacao_id.razao_social if contrato.lotacao_id else "" }',
    'horario': '${ contrato.jornada_segunda_a_sexta_id.descricao if contrato.jornada_tipo == "1" and contrato.jornada_segunda_a_sexta_id else contrato.jornada_escala_id.descricao if contrato.jornada_escala_id else "" }',
    'horario_intervalo': '${ contrato.jornada_segunda_a_sexta_id.descricao_intervalo_1 if contrato.jornada_tipo == "1" and contrato.jornada_segunda_a_sexta_id else "" }',
    'horario_sabado': '${ contrato.jornada_sabado_id.descricao if contrato.jornada_tipo == "1" and contrato.jornada_sabado_id else "" }',
    'horario_sabado_intervalo': '${ contrato.jornada_sabado_id.descricao_intervalo_1 if contrato.jornada_tipo == "1" and contrato.jornada_sabado_id else "" }',
    'cor': '${ RACA_COR[empregado.raca_cor] }',
    'TIPOCC': '${ u"Conta salário" if empregado.banco_tipo_conta == "1" else u"Poupança" }',

    'FILHO_1_NOME': '${ filhos[0].nome if len(filhos) >= 1 else "" }',
    'FILHO_2_NOME': '${ filhos[1].nome if len(filhos) >= 2 else "" }',
    'FILHO_3_NOME': '${ filhos[2].nome if len(filhos) >= 3 else "" }',
    'FILHO_4_NOME': '${ filhos[3].nome if len(filhos) >= 4 else "" }',
    'FILHO_5_NOME': '${ filhos[4].nome if len(filhos) >= 5 else "" }',
    'FILHO_6_NOME': '${ filhos[5].nome if len(filhos) >= 6 else "" }',

    'FILHO_1_DATA_NASCIMENTO': '${ formata_data(filhos[0].data_nascimento) if len(filhos) >= 1 else "" }',
    'FILHO_2_DATA_NASCIMENTO': '${ formata_data(filhos[1].data_nascimento) if len(filhos) >= 2 else "" }',
    'FILHO_3_DATA_NASCIMENTO': '${ formata_data(filhos[2].data_nascimento) if len(filhos) >= 3 else "" }',
    'FILHO_4_DATA_NASCIMENTO': '${ formata_data(filhos[3].data_nascimento) if len(filhos) >= 4 else "" }',
    'FILHO_5_DATA_NASCIMENTO': '${ formata_data(filhos[4].data_nascimento) if len(filhos) >= 5 else "" }',
    'FILHO_6_DATA_NASCIMENTO': '${ formata_data(filhos[5].data_nascimento) if len(filhos) >= 6 else "" }',

    'DEPENDENTE_1_NOME': '${ empregado.dependente_ids[0].nome if len(empregado.dependente_ids) >= 1 else "" }',
    'DEPENDENTE_2_NOME': '${ empregado.dependente_ids[1].nome if len(empregado.dependente_ids) >= 2 else "" }',
    'DEPENDENTE_3_NOME': '${ empregado.dependente_ids[2].nome if len(empregado.dependente_ids) >= 3 else "" }',
    'DEPENDENTE_4_NOME': '${ empregado.dependente_ids[3].nome if len(empregado.dependente_ids) >= 4 else "" }',
    'DEPENDENTE_5_NOME': '${ empregado.dependente_ids[4].nome if len(empregado.dependente_ids) >= 5 else "" }',
    'DEPENDENTE_6_NOME': '${ empregado.dependente_ids[5].nome if len(empregado.dependente_ids) >= 6 else "" }',

    'DEPENDENTE_1_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[0].data_nascimento) if len(empregado.dependente_ids) >= 1 else "" }',
    'DEPENDENTE_2_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[1].data_nascimento) if len(empregado.dependente_ids) >= 2 else "" }',
    'DEPENDENTE_3_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[2].data_nascimento) if len(empregado.dependente_ids) >= 3 else "" }',
    'DEPENDENTE_4_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[3].data_nascimento) if len(empregado.dependente_ids) >= 4 else "" }',
    'DEPENDENTE_5_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[4].data_nascimento) if len(empregado.dependente_ids) >= 5 else "" }',
    'DEPENDENTE_6_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[5].data_nascimento) if len(empregado.dependente_ids) >= 6 else "" }',

    'BNF01': '${ filhos[0].nome if len(filhos) >= 1 else "" }',
    'BNF02': '${ filhos[1].nome if len(filhos) >= 2 else "" }',
    'BNF03': '${ filhos[2].nome if len(filhos) >= 3 else "" }',
    'BNF04': '${ filhos[3].nome if len(filhos) >= 4 else "" }',
    'BNF05': '${ filhos[4].nome if len(filhos) >= 5 else "" }',
    'BNF06': '${ filhos[5].nome if len(filhos) >= 6 else "" }',

    'DNF01': '${ formata_data(filhos[0].data_nascimento) if len(filhos) >= 1 else "" }',
    'DNF02': '${ formata_data(filhos[1].data_nascimento) if len(filhos) >= 2 else "" }',
    'DNF03': '${ formata_data(filhos[2].data_nascimento) if len(filhos) >= 3 else "" }',
    'DNF04': '${ formata_data(filhos[3].data_nascimento) if len(filhos) >= 4 else "" }',
    'DNF05': '${ formata_data(filhos[4].data_nascimento) if len(filhos) >= 5 else "" }',
    'DNF06': '${ formata_data(filhos[5].data_nascimento) if len(filhos) >= 6 else "" }',

    'FILHO_1_CARTORIO': '${ filhos[0].cartorio or "" if len(filhos) >= 1 else "" }',
    'FILHO_2_CARTORIO': '${ filhos[1].cartorio or "" if len(filhos) >= 2 else "" }',
    'FILHO_3_CARTORIO': '${ filhos[2].cartorio or "" if len(filhos) >= 3 else "" }',
    'FILHO_4_CARTORIO': '${ filhos[3].cartorio or "" if len(filhos) >= 4 else "" }',
    'FILHO_5_CARTORIO': '${ filhos[4].cartorio or "" if len(filhos) >= 5 else "" }',
    'FILHO_6_CARTORIO': '${ filhos[5].cartorio or "" if len(filhos) >= 6 else "" }',

    'FILHO_1_REG_CARTORIO': '${ filhos[0].registro_cartorio or "" if len(filhos) >= 1 else "" }',
    'FILHO_2_REG_CARTORIO': '${ filhos[1].registro_cartorio or "" if len(filhos) >= 2 else "" }',
    'FILHO_3_REG_CARTORIO': '${ filhos[2].registro_cartorio or "" if len(filhos) >= 3 else "" }',
    'FILHO_4_REG_CARTORIO': '${ filhos[3].registro_cartorio or "" if len(filhos) >= 4 else "" }',
    'FILHO_5_REG_CARTORIO': '${ filhos[4].registro_cartorio or "" if len(filhos) >= 5 else "" }',
    'FILHO_6_REG_CARTORIO': '${ filhos[5].registro_cartorio or "" if len(filhos) >= 6 else "" }',

    'FILHO_1_NUM_LIVRO': '${ filhos[0].numero_livro or "" if len(filhos) >= 1 else "" }',
    'FILHO_2_NUM_LIVRO': '${ filhos[1].numero_livro or "" if len(filhos) >= 2 else "" }',
    'FILHO_3_NUM_LIVRO': '${ filhos[2].numero_livro or "" if len(filhos) >= 3 else "" }',
    'FILHO_4_NUM_LIVRO': '${ filhos[3].numero_livro or "" if len(filhos) >= 4 else "" }',
    'FILHO_5_NUM_LIVRO': '${ filhos[4].numero_livro or "" if len(filhos) >= 5 else "" }',
    'FILHO_6_NUM_LIVRO': '${ filhos[5].numero_livro or "" if len(filhos) >= 6 else "" }',

    'FILHO_1_FOLHA': '${ filhos[0].folha or "" if len(filhos) >= 1 else "" }',
    'FILHO_2_FOLHA': '${ filhos[1].folha or "" if len(filhos) >= 2 else "" }',
    'FILHO_3_FOLHA': '${ filhos[2].folha or "" if len(filhos) >= 3 else "" }',
    'FILHO_4_FOLHA': '${ filhos[3].folha or "" if len(filhos) >= 4 else "" }',
    'FILHO_5_FOLHA': '${ filhos[4].folha or "" if len(filhos) >= 5 else "" }',
    'FILHO_6_FOLHA': '${ filhos[5].folha or "" if len(filhos) >= 6 else "" }',

    'DEP_1_NOME': '${ empregado.dependente_ids[0].nome if len(empregado.dependente_ids) >= 1 else "" }',
    'DEP_2_NOME': '${ empregado.dependente_ids[1].nome if len(empregado.dependente_ids) >= 2 else "" }',
    'DEP_3_NOME': '${ empregado.dependente_ids[2].nome if len(empregado.dependente_ids) >= 3 else "" }',
    'DEP_4_NOME': '${ empregado.dependente_ids[3].nome if len(empregado.dependente_ids) >= 4 else "" }',
    'DEP_5_NOME': '${ empregado.dependente_ids[4].nome if len(empregado.dependente_ids) >= 5 else "" }',
    'DEP_6_NOME': '${ empregado.dependente_ids[5].nome if len(empregado.dependente_ids) >= 6 else "" }',

    'DEP_1_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[0].data_nascimento) if len(empregado.dependente_ids) >= 1 else "" }',
    'DEP_2_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[1].data_nascimento) if len(empregado.dependente_ids) >= 2 else "" }',
    'DEP_3_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[2].data_nascimento) if len(empregado.dependente_ids) >= 3 else "" }',
    'DEP_4_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[3].data_nascimento) if len(empregado.dependente_ids) >= 4 else "" }',
    'DEP_5_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[4].data_nascimento) if len(empregado.dependente_ids) >= 5 else "" }',
    'DEP_6_DATA_NASCIMENTO': '${ formata_data(empregado.dependente_ids[5].data_nascimento) if len(empregado.dependente_ids) >= 6 else "" }',

    'DATA_AVISO': '${ data_aviso_previo }',
    'DATA_AVISO_PREVIO': '${ data_aviso_previo }',
    'DATA_INICIO_AVISO_PREVIO': '${ data_inicio_aviso_previo }',
    'DATA_UTIL_AVISO_PREVIO': '${ data_util_aviso_previo }',
    'DATA_AFASTAMENTO_REAL': '${ data_afastamento_real }',
    'DATA_UTIL_AFASTAMENTO_REAL': '${ data_util_afastamento_real }',
    'DATA_AFASTAMENTO_PROJETADO': '${ data_afastamento_projetado }',
    'DATA_UTIL_AFASTAMENTO_PROJETADO': '${ data_util_afastamento_projetado }',

    'DATA_FIM_PERIODO_AQUISITIVO': '${ data_fim_periodo_aquisitivo }',
    'DATA_SOLICITACAO_ABONO': '${ data_solicitacao_abono }',
    'DIAS_AVISO': '${ dias_aviso }',

    ### CAMPOS DO CONTRATO FINANCEIRO ###

    'CONTRATO_NUMERO': "${ finan_contrato_obj.numero or '' }",
    'CONTRATO_VALOR': '${ formata_valor(finan_contrato_obj.valor or 0) }',
    'CONTRATO_VALOR_EXTENSO': '${ valor_por_extenso_unidade(finan_contrato_obj.valor or 0) }',
    'CONTRATO_VALOR_MENSAL': '${ formata_valor(finan_contrato_obj.valor_mensal or 0) }',
    'CONTRATO_VALOR_MENSAL_EXTENSO': '${ valor_por_extenso_unidade(finan_contrato_obj.valor_mensal or 0) }',
    'CONTRATO_DATA_ASSINATURA': '${ formata_data(finan_contrato_obj.data_assinatura) }',
    'CONTRATO_DATA_EXTENSO': '${ data_por_extenso(finan_contrato_obj.data_assinatura) }',

    ### COMPRADOR ###

    'CLIENTE': '${ escape_xml(cliente_obj.name) }',
    'CLIENTE_QUALIFICACAO': '${ cliente_obj.qualificacao_contratual }',
    'COMPRADOR': '${ escape_xml(comprador_obj.name) }',
    'COMPRADOR_QUALIFICACAO': '${ comprador_obj.qualificacao_contratual }',
    #'C_CNPJ_CPF': '${ "CNPJ" if comprador_obj.cnpj_cpf > 11 else "CPF"  }',
    #'CNPJ_COMPRADOR': '${ comprador_obj.cnpj_cpf }',
    #'RUA_COMPRADOR': '${ vendedor_obj.endereco }',
    #'NUMERO_COMPRADOR': '${ vendedor_obj.numero }',
    #'COMP_COMPRADOR': '${ vendedor_obj.complemento }',
    #'BAIRRO_COMPRADOR': '${ vendedor_obj.bairro }',
    #'CIDADE_COMPRADOR': '${ vendedor_obj.cidade }',
    #'UF_COMPRADOR': '${ vendedor_obj.estado }',
    #'CEP_COMPRADOR': '${ vendedor_obj.cep }',

    ### VENDEDOR ###

    'VENDEDOR': '${ escape_xml(vendedor_obj.name) }',
    'VENDEDOR_QUALIFICACAO': '${ vendedor_obj.qualificacao_contratual }',
    #'V_CNPJ_CPF': '${ "CNPJ" if vendedor_obj.cnpj_cpf > 11 else "CPF"  }',
    #'CNPJ_VENDEDOR': '${ vendedor_obj.cnpj_cpf }',
    #'RUA_VENDEDOR': '${ vendedor_obj.endereco }',
    #'NUMERO_VENDEDOR': '${ vendedor_obj.numero }',
    #'COMP_VENDEDOR': '${ vendedor_obj.complemento }',
    #'BAIRRO_VENDEDOR': '${ vendedor_obj.bairro }',
    #'CIDADE_VENDEDOR': '${ vendedor_obj.cidade }',
    #'UF_VENDEDOR': '${ vendedor_obj.estado }',
    #'CEP_VENDEDOR': '${ vendedor_obj.cep }',

    ### IMOVEL ###
    'IMOVEL_DESCRICAO': '${ imovel_obj.descricao }',
    'IMOVEL_AREA': '${ formata_valor(imovel_obj.area_total) }',
    'IMOVEL_NOME': '${ imovel_obj.project_id.name }',
    'IMOVEL_CONFRONTACOES_CONTRATUAIS': '${ imovel_obj.confrontacoes_contratuais }',

    #
    # Condições de pagamento do imóvel
    #
    'CONTRATO_CONDICAO_1': "${ finan_contrato_obj.condicao_ids[0].descricao_contratual if len(finan_contrato_obj.condicao_ids) >=1 else u'' }",
    'CONTRATO_CONDICAO_2': "${ finan_contrato_obj.condicao_ids[1].descricao_contratual if len(finan_contrato_obj.condicao_ids) >=2 else u'' }",
    'CONTRATO_CONDICAO_3': "${ finan_contrato_obj.condicao_ids[2].descricao_contratual if len(finan_contrato_obj.condicao_ids) >=3 else u'' }",
    'CONTRATO_CONDICAO_4': "${ finan_contrato_obj.condicao_ids[3].descricao_contratual if len(finan_contrato_obj.condicao_ids) >=4 else u'' }",
    'CONTRATO_CONDICAO_5': "${ finan_contrato_obj.condicao_ids[4].descricao_contratual if len(finan_contrato_obj.condicao_ids) >=5 else u'' }",
    'CONTRATO_CONDICAO_6': "${ finan_contrato_obj.condicao_ids[5].descricao_contratual if len(finan_contrato_obj.condicao_ids) >=6 else u'' }",

    #'CONDICAO_PAGAMENTO_1': '<text:list xml:id="list112046175932432" text:continue-numbering="true" text:style-name="WW8Num4"><text:list-item><text:p text:style-name="P8"><text:span text:style-name="T9">R$ 4.800,00 (quatro mil e oitocentos reais)</text:span><text:span text:style-name="T12"> a serem pagos em moeda corrente nacional, sendo </text:span><text:span text:style-name="T9">R$ 4.000,00</text:span><text:span text:style-name="T12"> (quatro mil reais) no ato da assinatura do presente contrato e </text:span><text:span text:style-name="T9">R$ 800,00</text:span><text:span text:style-name="T12"> (oitocentos reais) divididos em 02 (duas) parcelas mensais, fixas e consecutivas no valor de </text:span><text:span text:style-name="T9">R$ 400,00 </text:span><text:span text:style-name="T12">(quatrocentos reais) cada uma, representadas por boleto bancários emitidos pelo </text:span><text:span text:style-name="T9">PROMITENTE VENDEDOR</text:span><text:span text:style-name="T12">, a primeira com vencimento para 15 (quinze) de janeiro de 2015 e a última com vencimento para o dia 15 (quinze) de fevereiro de 2015; </text:span></text:p></text:list-item></text:list>',
}

TEMPLATE_CAMPO = '<text:database-display text:table-name="" text:table-type="table" text:column-name="%s">«%s»</text:database-display>'
TEMPLATE_CAMPO2 = '«%s»'


def troca_campo(texto, novas_variaveis={}):
    for campo, valor in VARIAVEIS.iteritems():
        tag_campo = TEMPLATE_CAMPO % (campo, campo)

        if campo in novas_variaveis:
            texto = texto.replace(tag_campo, novas_variaveis[campo])
        else:
            texto = texto.replace(tag_campo, valor)

        tag_campo = TEMPLATE_CAMPO2 % campo

        if campo in novas_variaveis:
            texto = texto.replace(tag_campo, novas_variaveis[campo])
        else:
            texto = texto.replace(tag_campo, valor)

    return texto
