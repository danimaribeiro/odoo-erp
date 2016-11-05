# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from . import (base, data, febraban, ibge, inscricao, ncm, sped, telefone, valor, xml)
import locale
import os

#
# Define o locale personalizado
#
CURDIR = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(CURDIR, 'locale_brasil')

os.environ['LOCPATH'] = LOCALE_DIR
os.environ['NLSPATH'] = LOCALE_DIR

#locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8'.encode('utf-8'))
locale.setlocale(locale.LC_COLLATE, 'pt_BR.UTF-8'.encode('utf-8'))

os.environ['LANG'] = 'pt_BR.UTF-8'
os.environ['LC_ALL'] = 'pt_BR.UTF-8'
os.environ['LANGUAGE'] = 'pt_BR:en_US'
