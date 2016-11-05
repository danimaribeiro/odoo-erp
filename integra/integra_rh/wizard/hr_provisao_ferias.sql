-- View: hr_provisao_ferias

DROP VIEW hr_provisao_ferias;

CREATE OR REPLACE VIEW hr_provisao_ferias AS 

SELECT 
    pf.provisao_id,
    pf.contract_id,
    pf.data_inicio_periodo_aquisitivo,
    pf.competencia,
    pf.aviso_id,
    pf.rescisao_id,
    pf.folha_id,
    ( 
        SELECT 
            pfa.provisao_id
        FROM 
            hr_provisao_ferias_base pfa
        WHERE 
            pfa.contract_id = pf.contract_id 
            AND pfa.data_inicio_periodo_aquisitivo = pf.data_inicio_periodo_aquisitivo 
            AND pfa.competencia = to_char(cast((pf.competencia || '-01') as date) - interval '1 mon', 'yyyy-mm')
    ) AS provisao_anterior_id
FROM 
    hr_provisao_ferias_base pf
    
UNION ALL

SELECT 
    COALESCE(pf.memoria_rescisao_id, pf.aviso_id) AS provisao_id,
    pf.contract_id,
    pf.data_inicio_periodo_aquisitivo,
    to_char(cast((pf.competencia || '-01') as date) + interval '1 mon', 'yyyy-mm') AS competencia,
    pf.aviso_id,
    pf.rescisao_id,
    pf.folha_id,
    pf.provisao_id AS provisao_anterior_id
    
FROM 
    hr_provisao_ferias_base pf

WHERE 
    (
        pf.aviso_id IS NOT NULL 
        OR pf.rescisao_id IS NOT NULL 
        OR pf.folha_id IS NOT NULL
    ) AND NOT (EXISTS ( 
            SELECT 
                pfa.contract_id
            FROM 
                hr_provisao_ferias_base pfa
            WHERE 
                pfa.competencia = to_char(cast(pf.competencia || '-01' as date) + interval '1 mon', 'yyyy-mm') 
                AND pfa.contract_id = pf.contract_id 
                AND pfa.data_inicio_periodo_aquisitivo = pf.data_inicio_periodo_aquisitivo
        )
    )
