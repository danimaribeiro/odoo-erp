
if variavel.ARREDONDAMENTO_MES_PASSADO:
    result = variavel.ARREDONDAMENTO_MES_PASSADO.valor

else:
    arred = holerite.rubrica_outro_periodo(rubrica='ARREDONDAMENTO_MES', tipo='N', mes_todo=True)
    result = arred.total