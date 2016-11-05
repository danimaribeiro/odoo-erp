# -*- coding: utf-8 -*-


SQL_FINAN_ESTRUTURA_DEMONSTRATIVO = """
SELECT 
ed.id as estrutura_id,
ed.codigo_completo,
ed.nome,
case
   when ed.resumida or ed.sintetica then null
   else p.conta_id
end as conta_id,
ed.resumida,
sum(coalesce(p.vr_debito,0)) as vr_debito,
sum(coalesce(p.vr_credito,0)) as vr_credito

FROM finan_estrutura_demonstrativo_arvore a
join finan_estrutura_demonstrativo_partida p on p.conta_demonstrativo_id = a.conta_id
join finan_estrutura_demonstrativo ed on ed.id = a.conta_pai_id

where 
ed.tipo_demonstrativo = '{tipo_demonstrativo}'
and p.data between '{data_inicial}' and '{data_final}'
and p.company_id = {company_id}
{centrocusto_id}

group by
ed.id, 
ed.codigo_completo,
ed.nome,
4,
ed.resumida

ORDER BY 
ed.codigo_completo"""

