# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .constantes import (WS_BC_DOLAR, WS_BC_EURO_VENDA, WS_BC_EURO_COMPRA,
    WS_BC_IGPM, WS_BC_INPC, WS_BC_SELIC)
from .base import (cotacao_dolar, cotacao_euro, cotacao_igpm,
    cotacao_dolar_periodo, cotacao_euro_periodo, cotacao_igpm_periodo)
