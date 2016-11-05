update product_product p
set tipo = coalesce((select distinct sp.tipo from sped_produto sp where sp.product_id = p.id and sp.tipo <> '' limit 1), '')
where p.tipo is null;

update product_product p
set ncm_id = coalesce((select distinct sp.ncm_id from sped_produto sp where sp.product_id = p.id and sp.ncm_id is not null limit 1), null)
where p.ncm_id is null;

update product_product p
set familiatributaria_id = coalesce((select distinct sp.familiatributaria_id from sped_produto sp where sp.product_id = 1 and sp.familiatributaria_id is not null limit 1), null)
where p.familiatributaria_id is null;

update product_product p
set al_ipi_id = coalesce((select distinct sp.al_ipi_id from sped_produto sp where sp.product_id = 1 and sp.al_ipi_id is not null limit 1), null)
where p.al_ipi_id is null;

update product_product p
set al_pis_cofins_id = coalesce((select distinct sp.al_pis_cofins_id from sped_produto sp where sp.product_id = 1 and sp.al_pis_cofins_id is not null limit 1), null)
where p.al_pis_cofins_id is null;
