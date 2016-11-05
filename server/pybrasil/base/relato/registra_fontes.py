# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

import os

DIRNAME = os.path.dirname(__file__)


#
# Fontes DejaVu Sans
#
FONTE_DEJAVU_SANS = 'DejaVu Sans'
FONTE_DEJAVU_SANS_NEGRITO = FONTE_DEJAVU_SANS + ' Bold'
FONTE_DEJAVU_SANS_ITALICO = FONTE_DEJAVU_SANS + ' Italic'
FONTE_DEJAVU_SANS_NEGRITO_ITALICO = FONTE_DEJAVU_SANS + ' Bold Italic'
LISTA_FONTES_DEJAVU_SANS = (
    (FONTE_DEJAVU_SANS, DIRNAME + '/fonts/DejaVuSans.ttf', False, False),
    (FONTE_DEJAVU_SANS_NEGRITO, DIRNAME + '/fonts/DejaVuSans-Bold.ttf', True, False),
    (FONTE_DEJAVU_SANS_ITALICO, DIRNAME + '/fonts/DejaVuSans-Oblique.ttf', False, True),
    (FONTE_DEJAVU_SANS_NEGRITO_ITALICO, DIRNAME + '/fonts/DejaVuSans-BoldOblique.ttf', True, True),
)

#
# Fontes DejaVu Sans Mono
#
FONTE_DEJAVU_SANS_MONO = 'DejaVu Sans Mono'
FONTE_DEJAVU_SANS_MONO_NEGRITO = FONTE_DEJAVU_SANS_MONO + ' Bold'
FONTE_DEJAVU_SANS_MONO_ITALICO = FONTE_DEJAVU_SANS_MONO + ' Italic'
FONTE_DEJAVU_SANS_MONO_NEGRITO_ITALICO = FONTE_DEJAVU_SANS_MONO + ' Bold Italic'
LISTA_FONTES_DEJAVU_SANS_MONO = [
    (FONTE_DEJAVU_SANS_MONO, DIRNAME + '/fonts/DejaVuSansMono.ttf', False, False),
    (FONTE_DEJAVU_SANS_MONO_NEGRITO, DIRNAME + '/fonts/DejaVuSansMono-Bold.ttf', True, False),
    (FONTE_DEJAVU_SANS_MONO_ITALICO, DIRNAME + '/fonts/DejaVuSansMono-Oblique.ttf', False, True),
    (FONTE_DEJAVU_SANS_MONO_NEGRITO_ITALICO, DIRNAME + '/fonts/DejaVuSansMono-BoldOblique.ttf', True, True),
]
