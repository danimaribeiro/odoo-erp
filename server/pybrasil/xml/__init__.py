# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .abertura import tira_abertura, poe_abertura
from .escape import escape, unescape
#from .tag_caracter import TagCaracter
#from .tag_boolean import TagBoolean
#from .tag_inteiro import TagInteiro
#from .tag_decimal import TagDecimal, TagDinheiro
#from .tag_data import TagData
#from .tag_hora import TagHora
#from .tag_datahora import TagDataHora, TagDataHoraUTC
from .dicionario import xml_para_dicionario, dicionario_para_xml
