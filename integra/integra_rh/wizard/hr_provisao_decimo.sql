-- view: hr_provisao_decimo

-- drop view hr_provisao_decimo;

create or replace view hr_provisao_decimo as 

select pd.provisao_id,
    pd.contract_id,
    pd.data_inicio_periodo_aquisitivo,
    pd.data_fim_periodo_aquisitivo,
    pd.competencia,
    pd.decimo_id,
    pd.rescisao_id,
    (select 
        pda.provisao_id
     from 
        hr_provisao_decimo_base pda
     where 
        pda.contract_id = pd.contract_id 
        and pda.data_inicio_periodo_aquisitivo = pd.data_inicio_periodo_aquisitivo 
        and pda.competencia = to_char(((pd.competencia || '-01')::date) - '1 mon'::interval, 'yyyy-mm')
    ) as provisao_anterior_id
    
from 
    hr_provisao_decimo_base pd
    
    
UNION ALL

select coalesce(pd.rescisao_id, pd.decimo_id) as provisao_id,
    pd.contract_id,
    pd.data_inicio_periodo_aquisitivo,
    pd.data_fim_periodo_aquisitivo,
    pd.competencia,
    pd.decimo_id,
    pd.rescisao_id,
    (select 
        pda.provisao_id
     from 
        hr_provisao_decimo_base pda
     where 
        pda.contract_id = pd.contract_id 
        and pda.data_inicio_periodo_aquisitivo = pd.data_inicio_periodo_aquisitivo 
        and pda.competencia = to_char(((pd.competencia || '-01')::date) - '1 mon'::interval, 'yyyy-mm')
    ) as provisao_anterior_id
    
from 
    hr_provisao_decimo_base pd
where
    (pd.decimo_id IS NOT NULL OR pd.rescisao_id IS NOT NULL) 
    AND NOT (EXISTS ( SELECT pda.contract_id
           FROM hr_provisao_decimo_base pda
          WHERE pda.competencia = to_char(((pd.competencia || '-01'::text)::date) + '1 mon'::interval, 'yyyy-mm'::text) AND pda.contract_id = pd.contract_id AND pda.data_inicio_periodo_aquisitivo = pd.data_inicio_periodo_aquisitivo))
