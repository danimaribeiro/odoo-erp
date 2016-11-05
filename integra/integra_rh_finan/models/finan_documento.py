# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import orm, fields


POSTERGACAO_EXATA = 'EXATA'
POSTERGACAO_POSTERGA = 'POSTERGA'
POSTERGACAO_ANTECIPA = 'ANTECIPA'

TIPO_POSTERGACAO = (
    (POSTERGACAO_EXATA, 'Data Exata'),
    (POSTERGACAO_POSTERGA, 'Postergar'),
    (POSTERGACAO_ANTECIPA, 'Antecipar'),
)


class finan_documento(orm.Model):
    _description = u'Tipos de Documento'
    _name = 'finan.documento'
    _inherit = 'finan.documento'

    def _cria_id_folha(self, cr, uid, rubrica):
        folha_ids = self.search(cr, uid, [('nome', 'in', [rubrica.upper(), rubrica.lower()])])

        if folha_ids:
            return folha_ids[0]

        dados = {
            'nome': rubrica.upper(),
            'postergacao': 'POSTERGA',
        }
        folha_id = self.create(cr, uid, dados)
        return folha_id

    def id_folha(self, cr, uid):
        return self._cria_id_folha(cr, uid, 'PAGAMENTO FOLHA')

    def id_ferias(self, cr, uid):
        return self._cria_id_folha(cr, uid, 'PAGAMENTO FÉRIAS')

    def id_rescisao(self, cr, uid):
        return self._cria_id_folha(cr, uid, 'PAGAMENTO RESCISÃO')

    def id_decimo(self, cr, uid):
        return self._cria_id_folha(cr, uid, 'PAGAMENTO 13º')

    def id_prolabore(self, cr, uid):
        return self._cria_id_folha(cr, uid, 'PAGAMENTO PRO-LABORE')

    def id_inss(self, cr, uid):
        return self._cria_id_folha(cr, uid, 'PAGAMENTO INSS')

    def id_fgts(self, cr, uid):
        return self._cria_id_folha(cr, uid, 'PAGAMENTO FGTS')

    def id_irpf(self, cr, uid):
        return self._cria_id_folha(cr, uid, 'PAGAMENTO IRPF')


finan_documento()
