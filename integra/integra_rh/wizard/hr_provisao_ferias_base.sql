
DROP VIEW hr_provisao_ferias;
DROP VIEW hr_provisao_ferias_base;

CREATE OR REPLACE VIEW hr_provisao_ferias_base AS 
SELECT 
    h.id AS provisao_id,
    h.contract_id,
    h.data_inicio_periodo_aquisitivo,
    to_char(h.date_to, 'yyyy-mm') AS competencia,
    ( 
        SELECT 
            hg.id
        FROM 
            hr_payslip hg
        WHERE 
            hg.contract_id = h.contract_id 
            AND COALESCE(hg.simulacao, false) = false 
            AND hg.tipo = 'F' 
            AND hg.state = 'done' 
            AND hg.data_inicio_periodo_aquisitivo = h.data_inicio_periodo_aquisitivo 
            AND to_char(hg.date_from, 'yyyy-mm') = to_char(h.date_from + interval '1 mon', 'yyyy-mm')
    ) AS aviso_id,
    ( 
        SELECT 
            hg.id
        FROM 
            hr_payslip hg
        WHERE 
            hg.contract_id = h.contract_id 
            AND COALESCE(hg.simulacao, false) = false 
            AND hg.tipo = 'R' 
            AND hg.state = 'done'
            AND to_char(hg.data_afastamento, 'yyyy-mm') = to_char(h.date_to + interval '1 mon', 'yyyy-mm')
    ) AS rescisao_id,
    ( 
        SELECT 
            hs.id
        FROM 
            hr_payslip hg
            join hr_payslip_line hgl on hgl.slip_id = hg.id
            join hr_payslip hs on hs.id = hgl.simulacao_id
        WHERE 
            hg.contract_id = h.contract_id 
            AND COALESCE(hg.simulacao, false) = false 
            AND hg.tipo = 'R' 
            AND hg.state = 'done'
            AND to_char(hg.data_afastamento, 'yyyy-mm') = to_char(h.date_to + interval '1 mon', 'yyyy-mm')
            AND hs.tipo = 'F'
            AND hs.data_inicio_periodo_aquisitivo = h.data_inicio_periodo_aquisitivo
    ) AS memoria_rescisao_id,
    (
        SELECT 
            hg.id
        FROM 
            hr_payslip hg
            JOIN hr_payslip fg ON fg.id = hg.holerite_anterior_id
        WHERE 
            hg.contract_id = h.contract_id 
            AND COALESCE(hg.simulacao, false) = false 
            AND hg.tipo = 'N' 
            AND hg.state = 'done' 
            AND to_char(hg.date_to, 'yyyy-mm') = to_char(h.date_to + interval '1 mon', 'yyyy-mm')
            AND fg.data_inicio_periodo_aquisitivo = h.data_inicio_periodo_aquisitivo
    ) AS folha_id
FROM 
    hr_payslip h
WHERE 
    h.provisao = true 
    AND h.tipo = 'F';
