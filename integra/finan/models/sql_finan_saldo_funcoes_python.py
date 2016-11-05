# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


FUNCAO_DATA_CABECALHO = """

CREATE OR REPLACE FUNCTION data_cabecalho(data_texto date)
    RETURNS character varying AS

$BODY$

from pybrasil.data import dia_da_semana_por_extenso, data_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = dia_da_semana_por_extenso(data)
texto += ', '
texto += data_por_extenso(data)

return texto

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION data_cabecalho(data_texto timestamp with time zone)
    RETURNS character varying AS

$BODY$

from pybrasil.data import dia_da_semana_por_extenso, data_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = dia_da_semana_por_extenso(data)
texto += ', '
texto += data_por_extenso(data)

return texto

$BODY$
    LANGUAGE plpythonu;

"""

FUNCAO_DATA_POR_EXTENSO = """

CREATE OR REPLACE FUNCTION data_por_extenso(data date)
    RETURNS character varying AS

$BODY$

from pybrasil.data import data_por_extenso
from dateutil.parser import parse as parse_datetime

return data_por_extenso(parse_datetime(data))

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION data_por_extenso(data timestamp with time zone)
    RETURNS character varying AS

$BODY$

from pybrasil.data import data_por_extenso
from dateutil.parser import parse as parse_datetime

return data_por_extenso(parse_datetime(data))

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_DATA_POR_EXTENSO_LEGALES = """

CREATE OR REPLACE FUNCTION data_por_extenso_legales(data date)
    RETURNS character varying AS

$BODY$

from pybrasil.data import data_por_extenso
from dateutil.parser import parse as parse_datetime

return data_por_extenso(parse_datetime(data), numeros_por_extenso=True, legales=True)

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION data_por_extenso_legales(data timestamp with time zone)
    RETURNS character varying AS

$BODY$

from pybrasil.data import data_por_extenso
from dateutil.parser import parse as parse_datetime

return data_por_extenso(parse_datetime(data), numeros_por_extenso=True, legales=True)

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_DIA_SEMANA_EXTENSO = """

CREATE OR REPLACE FUNCTION dia_semana_extenso(data_texto date)
    RETURNS character varying AS

$BODY$

from pybrasil.data import dia_da_semana_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = dia_da_semana_por_extenso(data)

return texto

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION dia_semana_extenso(data_texto timestamp with time zone)
    RETURNS character varying AS

$BODY$

from pybrasil.data import dia_da_semana_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = dia_da_semana_por_extenso(data)

return texto

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_DATA_UTIL_PAGAMENTO = """

CREATE OR REPLACE FUNCTION dia_util_pagamento(
    data_texto date,
    estado character varying,
    cidade character varying,
    antecipa boolean DEFAULT false)
    RETURNS date AS

$BODY$
from pybrasil.data import dia_util_pagamento
from dateutil.parser import parse as parse_datetime

return dia_util_pagamento(data_texto, estado, cidade, antecipa)

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION dia_util_pagamento(
    data_texto character varying,
    estado_texto character varying,
    cidade_texto character varying,
    antecipa boolean)
    RETURNS date AS

$BODY$
from pybrasil.data import parse_datetime, dia_util_pagamento

data = parse_datetime(data_texto)
estado = estado_texto.upper()
cidade = cidade_texto.upper().decode('utf-8')

vencimento = dia_util_pagamento(data, estado, (estado, cidade), antecipa)

return vencimento

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_FORMATA_FERIADOS_NO_PERIODO = """

CREATE OR REPLACE FUNCTION feriados_no_periodo(
    data_inicial character varying,
    data_final character varying,
    estado character varying,
    cidade character varying)
    RETURNS SETOF character varying AS

$BODY$

from pybrasil.feriado.funcoes import feriados_no_periodo

feriados = feriados_no_periodo(data_inicial, data_final, estado, cidade.decode('utf-8'))

res = []
for data in feriados:
    if feriados[data]:
        for fer in feriados[data]:
            res.append(unicode(fer))

return res

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_FORMATA_CNPJ = """

CREATE OR REPLACE FUNCTION formata_cnpj(cnpj character varying)
    RETURNS character varying AS

$BODY$

from pybrasil.inscricao import formata_cnpj

return formata_cnpj(cnpj)

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_FORMATA_CPF = """

CREATE OR REPLACE FUNCTION formata_cpf(cpf character varying)
    RETURNS character varying AS

$BODY$

from pybrasil.inscricao import formata_cpf

return formata_cpf(cpf)

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_FORMATA_FONE = """

CREATE OR REPLACE FUNCTION formata_fone(fone character varying)
    RETURNS character varying AS

$BODY$

from pybrasil.telefone import formata_fone

return formata_fone(fone)

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_FORMATA_VALOR = """

CREATE OR REPLACE FUNCTION formata_valor(valor character varying)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import formata_valor
from decimal import Decimal as D

return formata_valor(D(valor))

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION formata_valor(valor numeric)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import formata_valor

return formata_valor(valor)

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_MES_EXTENSO = """

CREATE OR REPLACE FUNCTION mes_extenso(data_texto date)
    RETURNS character varying AS

$BODY$

from pybrasil.data import mes_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = mes_por_extenso(data)
texto += '/'
texto += str(data.year).zfill(4)

return texto

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION mes_extenso(data_texto timestamp with time zone)
    RETURNS character varying AS

$BODY$

from pybrasil.data import mes_por_extenso
from dateutil.parser import parse as parse_datetime

data = parse_datetime(data_texto)
texto = mes_por_extenso(data)
texto += '/'
texto += str(data.year).zfill(4)

return texto

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_PRIMEIRA_MAIUSCULA = """

CREATE OR REPLACE FUNCTION primeira_maiuscula(texto character varying)
    RETURNS character varying AS

$BODY$

from pybrasil.base import primeira_maiuscula
return primeira_maiuscula(texto.decode('utf-8'))

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_VALOR_POR_EXTENSO = """

CREATE OR REPLACE FUNCTION valor_por_extenso(valor character varying)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import valor_por_extenso_unidade
from decimal import Decimal as D

return valor_por_extenso_unidade(D(valor))

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION valor_por_extenso(valor double precision)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import valor_por_extenso_unidade

return valor_por_extenso_unidade(valor)

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION valor_por_extenso(valor numeric)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import valor_por_extenso_unidade

return valor_por_extenso_unidade(valor)

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_VALOR_POR_EXTENSO_DOLAR = """

CREATE OR REPLACE FUNCTION valor_por_extenso_euro(valor character varying)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import valor_por_extenso_unidade
from decimal import Decimal as D

return valor_por_extenso_unidade(D(valor), unidade=('euro', 'euros'))

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION valor_por_extenso_euro(valor double precision)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import valor_por_extenso_unidade

return valor_por_extenso_unidade(valor, unidade=('euro', 'euros'))

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION valor_por_extenso_euro(valor numeric)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import valor_por_extenso_unidade

return valor_por_extenso_unidade(valor, unidade=('euro', 'euros'))

$BODY$
    LANGUAGE plpythonu;

"""


FUNCAO_VALOR_POR_EXTENSO_EURO = """

CREATE OR REPLACE FUNCTION valor_por_extenso_dolar(valor character varying)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import valor_por_extenso_unidade
from decimal import Decimal as D

return valor_por_extenso_unidade(D(valor), unidade=(u'dólar', u'dólares'))

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION valor_por_extenso_dolar(valor double precision)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import valor_por_extenso_unidade

return valor_por_extenso_unidade(valor, unidade=(u'dólar', u'dólares'))

$BODY$
    LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION valor_por_extenso_dolar(valor numeric)
    RETURNS character varying AS

$BODY$

from pybrasil.valor import valor_por_extenso_unidade

return valor_por_extenso_unidade(valor, unidade=(u'dólar', u'dólares'))

$BODY$
    LANGUAGE plpythonu;

"""


