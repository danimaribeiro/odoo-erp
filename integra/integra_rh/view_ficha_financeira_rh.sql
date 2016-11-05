-- View: hr_payslip_line_competencia

-- DROP VIEW hr_payslip_line_competencia;

CREATE OR REPLACE VIEW hr_payslip_line_competencia AS
 SELECT
        CASE
            WHEN hl.code::text = ANY (ARRAY['INSS'::character varying::text, 'INSS_anterior'::character varying::text, 'IRPF'::character varying::text]) THEN (((hl.name::text || ' ('::text) || formata_valor(hl.rate)::text) || '%)'::text)::character varying
            ELSE hl.name
        END AS rubrica,
        CASE
            WHEN h.tipo::text = 'N'::text THEN to_char(h.date_from::timestamp with time zone, 'yyyy-mm'::text)
            WHEN h.tipo::text = 'R'::text THEN to_char(h.data_afastamento::timestamp with time zone, 'yyyy-mm'::text)
            WHEN h.tipo::text = 'D'::text THEN to_char(h.date_from::timestamp with time zone, 'yyyy-13'::text)
            WHEN h.tipo::text = 'F'::text THEN to_char(h.date_from - '2 days'::interval, 'yyyy-mm'::text)
            ELSE NULL::text
        END AS competencia,
    hl.quantity AS quantidade,
    hl.total AS valor,
    hl.salary_rule_id AS code,
    sr.sinal,
    h.contract_id,
    h.employee_id,
    h.id AS payslip_id
   FROM hr_payslip_line hl
     JOIN hr_salary_rule sr ON hl.salary_rule_id = sr.id
     JOIN hr_payslip h ON h.id = hl.slip_id
  WHERE ((sr.sinal::text = ANY (ARRAY['+'::character varying::text, '-'::character varying::text])) OR sr.code::text ~~ 'BASE%'::text) AND hl.total > 0::numeric AND hl.holerite_anterior_line_id IS NULL AND (h.simulacao IS NULL OR h.simulacao = false)
  ORDER BY
        CASE
            WHEN h.tipo::text = 'N'::text THEN to_char(h.date_from::timestamp with time zone, 'yyyy-mm'::text)
            WHEN h.tipo::text = 'R'::text THEN to_char(h.data_afastamento::timestamp with time zone, 'yyyy-mm'::text)
            WHEN h.tipo::text = 'D'::text THEN to_char(h.date_from::timestamp with time zone, 'yyyy-13'::text)
            WHEN h.tipo::text = 'F'::text THEN to_char(h.date_from - '2 days'::interval, 'yyyy-mm'::text)
            ELSE NULL::text
        END, sr.sinal DESC,
        CASE
            WHEN hl.code::text = ANY (ARRAY['INSS'::character varying::text, 'INSS_anterior'::character varying::text, 'IRPF'::character varying::text]) THEN (((hl.name::text || ' ('::text) || formata_valor(hl.rate)::text) || '%)'::text)::character varying
            ELSE hl.name
        END;

