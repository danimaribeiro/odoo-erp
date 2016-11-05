-- Function: custo_medio()
DROP FUNCTION custo_medio();

CREATE OR REPLACE FUNCTION custo_medio()
  RETURNS TABLE(move_id integer, location_id integer, product_id integer, data date, entrada_saida character varying, entrada numeric, saida numeric, vr_unitario numeric, vr_unitario_custo numeric, vr_total numeric, quantidade numeric) AS
$BODY$
from copy import copy
from decimal import Decimal as D

res = []
linha_modelo = {
  'move_id': 0,
  'location_id': 0,
  'product_id': 0,
  'data': None,
  'entrada_saida': u'',
  'entrada': D(0),
  'saida': D(0),
  'vr_unitario': D(0),
  'quantidade': D(0),
  'vr_unitario_custo': D(0),
  'vr_total': D(0),
}


for dados_location in plpy.cursor('select c.id from stock_location as c;'):
    location_id = dados_location['id']
    produto_id_anterior = 0
    quantidade_estoque = D(0)
    vr_unitario = D(0)

    for dados_move in plpy.cursor("""
        select
            c.id,
            cast(c.date as date) as date,
            case
                when c.location_id = %d then 'S'
                else 'E'
            end as entrada_saida,
            c.location_id,
            c.location_dest_id,
            cast(c.product_qty as varchar) as quantidade,
            cast(case
                when sil.vr_unitario is null and sdi.vr_unitario_custo is null then 0
                when sil.vr_unitario is not null then sil.vr_unitario
                when sdi.vr_unitario_custo is not null then sdi.vr_unitario_custo
            end as varchar) as vr_unitario_custo,
            c.product_id,
            cf.codigo as cfop

        from
            stock_move as c
            left join sped_documentoitem as sdi on sdi.id = c.sped_documentoitem_id
            left join sped_cfop cf on cf.id = sdi.cfop_id
            left join sped_documento d on d.id = sdi.documento_id and d.entrada_saida = '0'
            left join stock_inventory_line as sil on sil.id = c.stock_inventory_line_id

        where
            c.location_id = %d or c.location_dest_id = %d

        order by
            c.product_id, 2, 3, c.id;""" % (location_id, location_id, location_id)):
        stock_move_id = dados_move['id']
        date_move = dados_move['date']
        quantidade_move = D(dados_move['quantidade'])
        vr_unitario_custo = D(dados_move['vr_unitario_custo'])
        product_id = dados_move['product_id']
        location_destino_id = dados_move['location_dest_id']
        cfop = dados_move['cfop']

        if product_id != produto_id_anterior:
            produto_id_anterior = product_id
            vr_total = D(0)
            vr_unitario = D(0)
            quantidade_estoque = D(0)

        entrada = D(0)
        saida = D(0)
        #
        # Entrada
        #
        if location_id == location_destino_id:
            entrada_saida = u'E'
            entrada = quantidade_move
            quantidade_estoque += entrada
            #
            # O valor do custo só é ajustado quando houver entrada
            # com valor de custo
            #
            if vr_unitario_custo != 0 and (cfop is None or cfop not in ['1949', '2949', '1916', '2916', '1910', '2910', '1913', '2913', '1202', '2202', '1411', '2411']):
                custo_atual = vr_total
                custo_atual += entrada * vr_unitario_custo

                if quantidade_estoque > 0:
                    vr_unitario =  custo_atual / quantidade_estoque

            vr_total = vr_unitario * quantidade_estoque

        #
        # Saída
        #
        else:
            entrada_saida = u'S'
            saida = quantidade_move
            quantidade_estoque -= quantidade_move
            vr_total = vr_unitario * quantidade_estoque
            vr_unitario_custo = vr_unitario

        linha = copy(linha_modelo)
        linha['move_id'] = stock_move_id
        linha['location_id'] = location_id
        linha['product_id'] = product_id
        linha['data'] = date_move
        linha['entrada_saida'] = entrada_saida
        linha['entrada'] = D(str(entrada)).quantize(D('0.0001'))
        linha['saida'] = D(str(saida)).quantize(D('0.0001'))
        linha['vr_unitario'] = D(str(vr_unitario_custo)).quantize(D('0.000001'))
        linha['vr_unitario_custo'] = D(str(vr_unitario)).quantize(D('0.000001'))
        linha['vr_total'] = D(str(vr_total)).quantize(D('0.01'))
        linha['quantidade'] = D(str(quantidade_estoque)).quantize(D('0.0001'))
        res.append(linha)

return res
$BODY$
  LANGUAGE plpythonu VOLATILE
  COST 100
  ROWS 1000;

