-- View: project_orcamento_meses

-- DROP VIEW project_orcamento_meses;

CREATE OR REPLACE VIEW project_orcamento_meses_desembolso AS 
 SELECT DISTINCT po.id AS orcamento_id,
    to_char(ipp.data_vencimento::timestamp with time zone, 'YYYY-MM'::text) AS mes
   FROM project_orcamento po
     JOIN project_orcamento_etapa poe ON poe.orcamento_id = po.id
     JOIN project_orcamento_item poi ON poi.etapa_id = poe.id AND poi.orcamento_id = po.id
     JOIN project_orcamento_item_planejamento oip ON oip.item_id = poi.id
     JOIN project_orcamento_item_planejamento_parcela ipp ON ipp.planejamento_id = oip.id
  ORDER BY to_char(ipp.data_vencimento::timestamp with time zone, 'YYYY-MM'::text);

