-- view: project_orcamento_meses_colunas

drop view project_orcamento_meses_planejamento_colunas;

create or replace view project_orcamento_meses_planejamento_colunas as 
 select o.id as orcamento_id,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes           limit 1) as mes_01,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset  1 limit 1) as mes_02,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset  2 limit 1) as mes_03,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset  3 limit 1) as mes_04,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset  4 limit 1) as mes_05,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset  5 limit 1) as mes_06,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset  6 limit 1) as mes_07,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset  7 limit 1) as mes_08,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset  8 limit 1) as mes_09,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset  9 limit 1) as mes_10,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 10 limit 1) as mes_11,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 11 limit 1) as mes_12,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 12 limit 1) as mes_13,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 13 limit 1) as mes_14,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 14 limit 1) as mes_15,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 15 limit 1) as mes_16,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 16 limit 1) as mes_17,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 17 limit 1) as mes_18,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 18 limit 1) as mes_19,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 19 limit 1) as mes_20,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 20 limit 1) as mes_21,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 21 limit 1) as mes_22,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 22 limit 1) as mes_23,
   (select pom.mes from project_orcamento_meses_planejamento pom where pom.orcamento_id = o.id order by pom.orcamento_id, pom.mes offset 23 limit 1) as mes_24
 from project_orcamento o
;
