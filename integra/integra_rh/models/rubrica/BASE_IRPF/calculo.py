#
# Parâmetros de cálculo
#
# Lembre de usar sempre o "ponto" como separador de casas decimais
#
if holerite.data_pagamento_irpf:
    ano = int(holerite.data_pagamento_irpf[:4])
    mes = holerite.data_pagamento_irpf[5:7]

else:
    ano = int(holerite.data_inicial[:4])
    mes = holerite.data_inicial[5:7]

if ano not in TABELA_IR:
    ano = max(TABELA_IR.keys())

#
# Localiza o mês na tabela do ano
#
for mes_tabela in TABELA_IR[ano]:
    if mes_tabela <= mes:
        faixas_de_contribuicao = TABELA_IR[ano][mes_tabela]
        deducao_por_dependente = D(TABELA_IR_DEPENDENTE[ano][mes_tabela] or 0)
        break

#
# Cálculo propriamente dito; não altere daqui pra baixo
# a não ser que saiba muuuuito bem o que está fazendo
#
deducao_dependentes = 0
if 'DEDUCAO_DEPENDENTES' in locals():
    deducao_dependentes = DEDUCAO_DEPENDENTES

if variavel.BASE_IRPF:
    base_de_calculo = variavel.BASE_IRPF.valor

#elif holerite.tipo == 'R':
#    base_de_calculo = BASE_INSS - INSS

#    if 'INSS_anterior' in locals():
#        base_de_calculo += BASE_INSS_anterior
#        base_de_calculo -= INSS_anterior

#    base_de_calculo -= deducao_dependentes

#elif 'INSS_anterior' in locals():
#    base_de_calculo = BASE_INSS_anterior - INSS_anterior
#    base_de_calculo -= deducao_dependentes

else:
    base_de_calculo = BASE_INSS - INSS
    base_de_calculo -= deducao_dependentes

    #if 'BASE_INSS_13' in locals():
    #    base_de_calculo += BASE_INSS_13 - INSS_13

    if 'BASE_INSS_anterior' in locals():
        base_de_calculo -= BASE_INSS_anterior

    if 'PENSAO_ALIMENTICIA' in locals():
        base_de_calculo -= PENSAO_ALIMENTICIA

    if holerite.tipo == 'R' and holerite.struct_id.codigo_afastamento and holerite.struct_id.codigo_afastamento != 'N2':
        base_anterior = holerite.rubrica_outro_periodo(rubrica='BASE_IRPF', mes_todo=True)
        if base_anterior:
            base_de_calculo += base_anterior.total

        dependente_anterior = holerite.rubrica_outro_periodo(rubrica='DEDUCAO_DEPENDENTES', mes_todo=True)
        if dependente_anterior:
            base_de_calculo += dependente_anterior.total

        #base_de_calculo -= IRPF_FERIAS

result = 0
if base_de_calculo > 0:
    result = base_de_calculo
