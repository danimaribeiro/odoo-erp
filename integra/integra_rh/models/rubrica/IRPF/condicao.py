#
# A condição para o cálculo do IR é que o valor seja > R$ 10,00
#

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

base_de_calculo = D(BASE_IRPF)
result = 0

for inicio_faixa in faixas_de_contribuicao:
    if base_de_calculo >= inicio_faixa:
        aliquota, parcela_deduzir = faixas_de_contribuicao[inicio_faixa]
        result = base_de_calculo * (D(aliquota) / D(100))
        result -= D(parcela_deduzir)
        forca_porcentagem = D(aliquota)
        forca_valor = D(base_de_calculo)
        break

if variavel.IRPF:
    result = variavel.IRPF.valor

if holerite.tipo == 'R' and holerite.struct_id.codigo_afastamento and holerite.struct_id.codigo_afastamento != 'N2':
    ir_anterior = holerite.rubrica_outro_periodo(rubrica='IRPF', mes_todo=True)
    if ir_anterior:
        result -= ir_anterior.total

#
# Base legal para não retenção abaixo de R$ 10,00
# http://www.econeteditora.com.br//boletim_imposto_renda/ir-06/irrf_dispensa-retencao.asp?1=1
#
if result <= 10:
    result = False
