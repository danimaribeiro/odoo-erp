drop view if exists stock_separacao;

create view stock_separacao as

select
ls.id as id,
ls.id as picking_id,
sm.location_dest_id as location_id,
sm.product_id,
sm.product_qty

from
  stock_picking ls
  join stock_move sm on sm.picking_id = ls.id

where
  ls.type = 'out'

union

select
  lr.id as id,
  lr.picking_id,
  sm.location_id,
  sm.product_id,
  sm.product_qty * -1 as product_qty

from
  stock_picking lr
  join stock_move sm on sm.picking_id = lr.id

where lr.picking_id is not null and lr.type = 'internal';


drop view if exists stock_saldo_separacao;

create view stock_saldo_separacao as

select
ls.id as id,
ls.picking_id,
ls.location_id,
ls.product_id,
sum(ls.product_qty) as product_qty

from
  stock_separacao ls

group by
ls.id,
ls.picking_id,
ls.location_id,
ls.product_id;