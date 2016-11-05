--drop extension if exists plpythonu;
--create extension plpython;


drop function if exists valor_por_extenso(valor double precision);

create function valor_por_extenso(valor double precision)
   returns varchar
as $$
from pybrasil.valor import valor_por_extenso_unidade

return valor_por_extenso_unidade(valor)
$$ language plpythonu;


drop function if exists valor_por_extenso(valor numeric);

create function valor_por_extenso(valor numeric)
   returns varchar
as $$
from pybrasil.valor import valor_por_extenso_unidade

return valor_por_extenso_unidade(valor)
$$ language plpythonu;


drop function if exists valor_por_extenso(valor varchar);

create function valor_por_extenso(valor varchar)
   returns varchar
as $$
from pybrasil.valor import valor_por_extenso_unidade
from decimal import Decimal as D

return valor_por_extenso_unidade(D(valor.replace(',', '.')))
$$ language plpythonu;


drop function if exists formata_valor(valor numeric);

create function formata_valor(valor numeric)
   returns varchar
as $$
from pybrasil.valor import formata_valor

return formata_valor(valor)
$$ language plpythonu;


drop function if exists formata_valor(valor varchar);

create function formata_valor(valor varchar)
   returns varchar
as $$
from pybrasil.valor import formata_valor
from decimal import Decimal as D

return formata_valor(D(valor.replace(',', '.')))
$$ language plpythonu;


/*
   Função data_por_extenso
*/

drop function if exists data_por_extenso(data date);

create function data_por_extenso(data date)
   returns varchar
as $$
from pybrasil.data import data_por_extenso
from dateutil.parser import parse as parse_datetime

return data_por_extenso(parse_datetime(data))
$$ language plpythonu;

drop function if exists data_por_extenso(data timestamp with time zone);

create function data_por_extenso(data timestamp with time zone)
   returns varchar
as $$
from pybrasil.data import data_por_extenso
from dateutil.parser import parse as parse_datetime

return data_por_extenso(parse_datetime(data))
$$ language plpythonu;


/*
  Função data_cabecalho
*/

drop function if exists data_cabecalho(data_texto date);

create function data_cabecalho(data_texto date)
   returns varchar
as $$
from pybrasil.data import dia_da_semana_por_extenso, data_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = dia_da_semana_por_extenso(data)
texto += ', '
texto += data_por_extenso(data)

return texto
$$ language plpythonu;

drop function if exists data_cabecalho(data_texto timestamp with time zone);

create function data_cabecalho(data_texto timestamp with time zone)
   returns varchar
as $$
from pybrasil.data import dia_da_semana_por_extenso, data_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = dia_da_semana_por_extenso(data)
texto += ', '
texto += data_por_extenso(data)

return texto
$$ language plpythonu;

drop function if exists mes_extenso(data_texto date);

create function mes_extenso(data_texto date)
   returns varchar
as $$
from pybrasil.data import mes_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = mes_extenso(data)
texto += '/'
texto += str(data.year).zfill(4)

return texto
$$ language plpythonu;


drop function if exists mes_extenso(data_texto timestamp with time zone);

create function mes_extenso(data_texto timestamp with time zone)
   returns varchar
as $$
from pybrasil.data import mes_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = mes_extenso(data)
texto += '/'
texto += str(data.year).zfill(4)

return texto
$$ language plpythonu;


drop function if exists dia_semana_extenso(data_texto date);

create function dia_semana_extenso(data_texto date)
   returns varchar
as $$
from pybrasil.data import dia_da_semana_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = dia_da_semana_por_extenso(data)

return texto
$$ language plpythonu;


drop function if exists dia_semana_extenso(data_texto timestamp with time zone);

create function dia_semana_extenso(data_texto timestamp with time zone)
   returns varchar
as $$
from pybrasil.data import dia_da_semana_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = dia_da_semana_por_extenso(data)

return texto
$$ language plpythonu;


drop function if exists formata_fone(fone varchar);

create function formata_fone(fone varchar)
   returns varchar
as $$
from pybrasil.telefone import formata_fone

return formata_fone(fone)
$$ language plpythonu;
