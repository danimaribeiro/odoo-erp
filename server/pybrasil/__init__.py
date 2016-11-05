# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from . import (base, data, febraban, ibge, inscricao, ncm, sped, telefone, valor, xml)
import locale
import os
import getpass


#
# Define o locale personalizado
#
CURDIR = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(CURDIR, 'locale_brasil')
USUARIO = getpass.getuser()

#os.environ['LOCPATH'] = LOCALE_DIR
#os.environ['NLSPATH'] = LOCALE_DIR

#
# O LC_ALL e LC_NUMERIC afetam o comportamento
# do Postgres quando convertendo de e para formatos
# numéricos, devido a troca do separador decimal
#
if USUARIO != 'postgres':
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8'.encode('utf-8'))
    locale.setlocale(locale.LC_NUMERIC, 'pt_BR.UTF-8'.encode('utf-8'))

#locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8'.encode('utf-8'))
#locale.setlocale(locale.LC_NUMERIC, 'pt_BR.UTF-8'.encode('utf-8'))
locale.setlocale(locale.LC_COLLATE, 'pt_BR.UTF-8'.encode('utf-8'))
locale.setlocale(locale.LC_MESSAGES, 'pt_BR.UTF-8'.encode('utf-8'))
locale.setlocale(locale.LC_MONETARY, 'pt_BR.UTF-8'.encode('utf-8'))
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8'.encode('utf-8'))
locale.setlocale(locale.LC_CTYPE, 'pt_BR.UTF-8'.encode('utf-8'))

os.environ['LANG'] = 'pt_BR.UTF-8'
os.environ['LC_ALL'] = 'pt_BR.UTF-8'
os.environ['LANGUAGE'] = 'pt_BR:en_US'
