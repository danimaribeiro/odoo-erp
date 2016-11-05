# -*- coding: utf-8 -*-
#

import os
import reportlab.rl_config
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from tools.config import config


DIRNAME = os.path.dirname(__file__)


def registra_fontes():
    reportlab.rl_config.warnOnMissingFontGlyphs = 0

    #
    # Define a codificação padrão de todos os relatórios para utf-8
    #
    reportlab.rl_config.defaultEncoding = 'utf-8'

    #
    # Adiciona o caminho das fontes nas configurações do reportlab
    #
    reportlab.rl_config.TTFSearchPath.append(os.path.join(DIRNAME, 'fontes'))

    #
    # Fontes DejaVu Sans
    #
    pdfmetrics.registerFont(TTFont('DejaVu Sans', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Bold', 'DejaVuSans-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Oblique', 'DejaVuSans-Oblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Italic', 'DejaVuSans-Oblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Bold Oblique', 'DejaVuSans-BoldOblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Bold Italic', 'DejaVuSans-BoldOblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans ExtraLight', 'DejaVuSans-ExtraLight.ttf'))
    addMapping('DejaVu Sans', 0, 0, 'DejaVu Sans')
    addMapping('DejaVu Sans', 1, 0, 'DejaVu Sans Bold')
    addMapping('DejaVu Sans', 0, 1, 'DejaVu Sans Italic')
    addMapping('DejaVu Sans', 1, 1, 'DejaVu Sans Bold Italic')

    #
    # Define a fonte padrão como sendo a DejaVu Sans
    #
    reportlab.rl_config.canvas_basefontname = 'DejaVu Sans'

    #
    # Fontes DejaVu Sans Mono
    #
    pdfmetrics.registerFont(TTFont('DejaVu Sans Mono', 'DejaVuSansMono.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Mono Bold', 'DejaVuSansMono-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Mono Oblique', 'DejaVuSansMono-Oblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Mono Italic', 'DejaVuSansMono-Oblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Mono Bold Oblique', 'DejaVuSansMono-BoldOblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Mono Bold Italic', 'DejaVuSansMono-BoldOblique.ttf'))
    addMapping('DejaVu Sans Mono', 0, 0, 'DejaVu Sans Mono')
    addMapping('DejaVu Sans Mono', 1, 0, 'DejaVu Sans Mono Bold')
    addMapping('DejaVu Sans Mono', 0, 1, 'DejaVu Sans Mono Italic')
    addMapping('DejaVu Sans Mono', 1, 1, 'DejaVu Sans Mono Bold Italic')

    #
    # Fontes DejaVu Sans Condensed
    #
    pdfmetrics.registerFont(TTFont('DejaVu Sans Condensed', 'DejaVuSansCondensed.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Condensed Bold', 'DejaVuSansCondensed-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Condensed Oblique', 'DejaVuSansCondensed-Oblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Condensed Italic', 'DejaVuSansCondensed-Oblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Condensed Bold Oblique', 'DejaVuSansCondensed-BoldOblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Sans Condensed Bold Italic', 'DejaVuSansCondensed-BoldOblique.ttf'))
    addMapping('DejaVu Sans Condensed', 0, 0, 'DejaVu Sans Condensed')
    addMapping('DejaVu Sans Condensed', 1, 0, 'DejaVu Sans Condensed Bold')
    addMapping('DejaVu Sans Condensed', 0, 1, 'DejaVu Sans Condensed Italic')
    addMapping('DejaVu Sans Condensed', 1, 1, 'DejaVu Sans Condensed Bold Italic')

    #
    # Fontes DejaVu Serif
    #
    pdfmetrics.registerFont(TTFont('DejaVu Serif', 'DejaVuSerif.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Serif Bold', 'DejaVuSerif-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Serif Italic', 'DejaVuSerif-Italic.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Serif Bold Italic', 'DejaVuSerif-BoldItalic.ttf'))
    addMapping('DejaVu Serif', 0, 0, 'DejaVu Serif')
    addMapping('DejaVu Serif', 1, 0, 'DejaVu Serif Bold')
    addMapping('DejaVu Serif', 0, 1, 'DejaVu Serif Italic')
    addMapping('DejaVu Serif', 1, 1, 'DejaVu Serif Bold Italic')

    #
    # Fontes DejaVu Serif Condensed
    #
    pdfmetrics.registerFont(TTFont('DejaVu Serif Condensed', 'DejaVuSerifCondensed.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Serif Condensed Bold', 'DejaVuSerifCondensed-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Serif Condensed Italic', 'DejaVuSerifCondensed-Italic.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu Serif Condensed Bold Italic', 'DejaVuSerifCondensed-BoldItalic.ttf'))
    addMapping('DejaVu Serif Condensed', 0, 0, 'DejaVu Serif Condensed')
    addMapping('DejaVu Serif Condensed', 1, 0, 'DejaVu Serif Condensed Bold')
    addMapping('DejaVu Serif Condensed', 0, 1, 'DejaVu Serif Condensed Italic')
    addMapping('DejaVu Serif Condensed', 1, 1, 'DejaVu Serif Condensed Bold Italic')

    #
    # Fontes Gentium Book Basic
    #
    pdfmetrics.registerFont(TTFont('Gentium Book Basic', 'genbkbasr.ttf'))
    pdfmetrics.registerFont(TTFont('Gentium Book Basic Bold', 'genbkbasb.ttf'))
    pdfmetrics.registerFont(TTFont('Gentium Book Basic Italic', 'genbkbasi.ttf'))
    pdfmetrics.registerFont(TTFont('Gentium Book Basic Bold Italic', 'genbkbasbi.ttf'))
    addMapping('Gentium Book Basic', 0, 0, 'Gentium Book Basic')
    addMapping('Gentium Book Basic', 1, 0, 'Gentium Book Basic Bold')
    addMapping('Gentium Book Basic', 0, 1, 'Gentium Book Basic Italic')
    addMapping('Gentium Book Basic', 1, 1, 'Gentium Book Basic Bold Italic')

    #
    # Fontes Linux Libertine
    #
    pdfmetrics.registerFont(TTFont('Libertine', 'LinLibertine_Rah.ttf'))
    pdfmetrics.registerFont(TTFont('Libertine Bold', 'LinLibertine_RBah.ttf'))
    pdfmetrics.registerFont(TTFont('Libertine Italic', 'LinLibertine_RIah.ttf'))
    pdfmetrics.registerFont(TTFont('Libertine Bold Italic', 'LinLibertine_RBIah.ttf'))
    #pdfmetrics.registerFont(TTFont('Libertine Demi Bold', 'LinLibertine_RZah.ttf'))
    #pdfmetrics.registerFont(TTFont('Libertine Demi Bold Italic', 'LinLibertine_RZIah.ttf'))
    #pdfmetrics.registerFont(TTFont('Libertine Initials', 'LinLibertine_I.ttf'))
    #pdfmetrics.registerFont(TTFont('Libertine Mono', 'LinLibertine_Mah.ttf'))
    #pdfmetrics.registerFont(TTFont('Libertine Display', 'LinLibertine_DRah.ttf'))
    addMapping('Libertine', 0, 0, 'Libertine')
    addMapping('Libertine', 1, 0, 'Libertine Bold')
    addMapping('Libertine', 0, 1, 'Libertine Italic')
    addMapping('Libertine', 1, 1, 'Libertine Bold Italic')

    #pdfmetrics.registerFont(TTFont('Libertine Smallcaps', 'LinLibertineC_Re.ttf'))
    #addMapping('Libertine Smallcaps', 0, 0, 'Libertine Smallcaps')

    pdfmetrics.registerFont(TTFont('Biolinum', 'LinBiolinum_Rah.ttf'))
    pdfmetrics.registerFont(TTFont('Biolinum Bold', 'LinBiolinum_RBah.ttf'))
    pdfmetrics.registerFont(TTFont('Biolinum Italic', 'LinBiolinum_RIah.ttf'))
    addMapping('Biolinum', 0, 0, 'Biolinum')
    addMapping('Biolinum', 1, 0, 'Biolinum Bold')
    addMapping('Biolinum', 0, 1, 'Biolinum Italic')


    #
    # Adiciona agora o mapeamento das fontes Type1 para as fontes TTF
    #

    #
    # Helvetica para DejaVu Sans
    #
    addMapping('Helvetica', 0, 0, 'DejaVu Sans')
    addMapping('Helvetica', 1, 0, 'DejaVu Sans Bold')
    addMapping('Helvetica', 0, 1, 'DejaVu Sans Italic')
    addMapping('Helvetica', 1, 1, 'DejaVu Sans Bold Italic')

    #
    # Time e Times-Roman para Libertine
    #
    addMapping('Times', 0, 0, 'Libertine')
    addMapping('Times', 1, 0, 'Libertine Bold')
    addMapping('Times', 0, 1, 'Libertine Italic')
    addMapping('Times', 1, 1, 'Libertine Bold Italic')
    addMapping('Times-Roman', 0, 0, 'Libertine')
    addMapping('Times-Roman', 1, 0, 'Libertine Bold')
    addMapping('Times-Roman', 0, 1, 'Libertine Italic')
    addMapping('Times-Roman', 1, 1, 'Libertine Bold Italic')

    #
    # Courrier para DejaVu Sans Mono
    #
    addMapping('Courier', 0, 0, 'DejaVu Sans Mono')
    addMapping('Courier', 1, 0, 'DejaVu Sans Mono Bold')
    addMapping('Courier', 0, 1, 'DejaVu Sans Mono Italic')
    addMapping('Courier', 1, 1, 'DejaVu Sans Mono Bold Italic')
