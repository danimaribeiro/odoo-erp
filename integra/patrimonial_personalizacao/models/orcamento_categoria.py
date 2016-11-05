# -*- encoding: utf-8 -*-


from osv import osv, fields

from orcamento_categoria_view_sale import CABECALHO_FORM as CABECALHO_FORM_SALE
from orcamento_categoria_view_sale import RODAPE_FORM as RODAPE_FORM_SALE
from orcamento_categoria_view_sale import CORPO_FORM as CORPO_FORM_SALE
from orcamento_categoria_view_stock import CABECALHO_FORM as CABECALHO_FORM_STOCK
from orcamento_categoria_view_stock import RODAPE_FORM as RODAPE_FORM_STOCK
from orcamento_categoria_view_stock import CORPO_FORM as CORPO_FORM_STOCK


class orcamento_categoria(osv.osv):
    _name = 'orcamento.categoria'
    _inherit = 'orcamento.categoria'

    def ajusta_parametro_views(self):
        super(orcamento_categoria, self).ajusta_parametro_views()

        self.cabecalho_form_sale = CABECALHO_FORM_SALE
        self.rodape_form_sale = RODAPE_FORM_SALE
        self.corpo_form_sale = CORPO_FORM_SALE

        self.cabecalho_form_stock = CABECALHO_FORM_STOCK
        self.rodape_form_stock = RODAPE_FORM_STOCK
        self.corpo_form_stock = CORPO_FORM_STOCK
