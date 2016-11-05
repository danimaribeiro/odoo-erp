-- view: project_orcamento_meses

-- drop view project_orcamento_meses_planejamento;

create or replace view project_orcamento_meses_planejamento as 
select distinct meses.orcamento_id, meses.mes from (
 select po.id as orcamento_id,
    to_char(oip.data_inicial_execucao, 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
     
 union all
 select po.id as orcamento_id,
    to_char(oip.data_final_execucao, 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '1 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '1 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')


 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '2 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '2 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '3 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '3 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')


 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '4 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '4 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '5 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '5 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '6 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '6 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '7 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '7 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '8 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '8 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '9 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '9 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '10 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '10 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '11 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '11 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '12 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '12 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '13 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '13 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '14 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '14 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '15 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '15 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '16 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '16 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '17 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '17 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '18 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '18 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '19 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '19 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '20 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '20 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '21 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '21 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '22 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '22 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '23 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '23 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')

 union all
 select po.id as orcamento_id,
    to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '24 month', 'YYYY-MM') as mes
   from project_orcamento po
     join project_orcamento_etapa poe on poe.orcamento_id = po.id
     join project_orcamento_item poi on poi.etapa_id = poe.id and poi.orcamento_id = po.id
     join project_orcamento_item_planejamento oip on oip.item_id = poi.id
   where
     to_char(cast(to_char(oip.data_inicial_execucao, 'YYYY-MM-01') as date) + interval '24 month', 'YYYY-MM') < to_char(oip.data_final_execucao, 'YYYY-MM')
 
) as meses

where
   meses.orcamento_id is not null
   and meses.mes is not null
   
order by
  meses.orcamento_id,
  meses.mes
;