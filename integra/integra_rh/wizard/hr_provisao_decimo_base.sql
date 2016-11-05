
-- View: hr_provisao_decimo_base

-- DROP VIEW hr_provisao_decimo_base;

CREATE OR REPLACE VIEW hr_provisao_decimo_base AS 
 SELECT h.id AS provisao_id,
    h.contract_id,
    h.data_inicio_periodo_aquisitivo,
    h.data_fim_periodo_aquisitivo,
    to_char(h.date_to::timestamp with time zone, 'yyyy-mm'::text) AS competencia,
    ( SELECT hg.id
           FROM hr_payslip hg
          WHERE hg.contract_id = h.contract_id AND COALESCE(hg.simulacao, false) = false AND COALESCE(hg.complementar, false) = false AND hg.tipo::text = 'D'::text AND hg.state::text = 'done'::text AND hg.data_inicio_periodo_aquisitivo = h.data_inicio_periodo_aquisitivo AND to_char(hg.date_from::timestamp with time zone, 'yyyy-mm'::text) = to_char(h.date_from, 'yyyy-mm'::text)) AS decimo_id,
    ( SELECT hg.id
           FROM hr_payslip hg
          WHERE hg.contract_id = h.contract_id AND COALESCE(hg.simulacao, false) = false AND hg.tipo::text = 'R'::text AND hg.state::text = 'done'::text AND to_char(hg.data_afastamento::timestamp with time zone, 'yyyy-mm'::text) = to_char(h.date_to, 'yyyy-mm'::text)) AS rescisao_id
    
   FROM hr_payslip h
  WHERE h.provisao = true AND h.tipo::text = 'D'::text;
