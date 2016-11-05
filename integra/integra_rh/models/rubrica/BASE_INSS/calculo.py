
result = D(0)

if 'BASE_INSS_anterior' in locals():
    result = BASE_INSS_anterior

result += categoria.BASE + categoria.PROV + categoria.PROV_PROV

if 'DIAS_FALTA' in locals():
    result -= DIAS_FALTA

if 'HORA_FALTA' in locals():
    result -= HORA_FALTA

if 'DESC_PAGTO_INDEVIDO_INTERVALAR' in locals():
    result -= DESC_PAGTO_INDEVIDO_INTERVALAR

if holerite.tipo == 'R':
    if 'FERIAS_PROPORCIONAL' in locals():
        result -= FERIAS_PROPORCIONAL
    if 'FERIAS_PROPORCIONAL_1_3' in locals():
        result -= FERIAS_PROPORCIONAL_1_3
    if 'FERIAS_PROPORCIONAL_AP' in locals():
        result -= FERIAS_PROPORCIONAL_AP
    if 'FERIAS_PROPORCIONAL_1_3_AP' in locals():
        result -= FERIAS_PROPORCIONAL_1_3_AP
    if 'FERIAS_VENCIDA' in locals():
        result -= FERIAS_VENCIDA
    if 'FERIAS_VENCIDA_1_3' in locals():
        result -= FERIAS_VENCIDA_1_3
    if 'SAL_13' in locals():
        result -= SAL_13
    if 'SAL_13_AP' in locals():
        result -= SAL_13_AP
    if 'BASE_INSS_RESCISAO_ORIGINAL' in locals():
        result -= BASE_INSS_RESCISAO_ORIGINAL

#
# Comentado dia 12/08/2015 em função de email sobre as férias do Vanderlei Brigo
#
#if 'DSR_HORISTA' in locals() and holerite.tipo in ('F', 'D'):
#    result -= DSR_HORISTA
