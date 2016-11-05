# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from decimal import Decimal as D
from sped.constante_tributaria import *
from sped.models.fields import *

#
# Alíquotas padrão para o crédito do ICMS para emissores do SIMPLES Nacional
#
class AliquotaICMSSN(orm.Model):
    _description = u'Alíquota de crédito do ICMS SIMPLES'
    _name = 'sped.aliquotaicmssn'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''

        for registro in self.browse(cursor, user_id, ids):
            if registro.al_icms == -1:
                txt = u'Não tributado'
            else:
                txt = u'%.2f%%' % registro.al_icms
                txt = txt.replace(u'.', u',')

                if registro.rd_icms != 0:
                    txt += u', com redução de %.2f%%' % registro.rd_icms

                if len(registro.observacao):
                    txt += ' - ' + registro.observacao

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('al_icms', '>=', texto),
            ]
        return procura

    _columns = {
        'al_icms': CampoPorcentagem(u'Alíquota do crédito de ICMS', required=True,
            help=u'Alíquotas definidas na <a href="http://www.receita.fazenda.gov.br/Legislacao/LeisComplementares/2006/leicp123ConsolidadaCGSN.htm" target="_blank">Lei Complementar nº 123, de 14 de dezembro de 2006</a>.'),
        'rd_icms': CampoPorcentagem(u'Percentual estadual de redução da alíquota de ICMS',
            help=u'Caso haja legislação estadual que prescreva redução do percentual de partilha do ICMS para empresas do SIMPLES Nacional, informe aqui o valor percentual dessa redução. Exemplo: no Paraná, há o <a href="http://www.sefanet.pr.gov.br/SEFADocumento/Arquivos/2200904248.pdf">Decreto Estadual nº 4.248/2009</a>.'),
        'observacao': fields.char(u'Observação', size=60),
        'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', fnct_search=_procura_descricao),
        }

    _defaults = {
        'al_icms': 0.00,
        'rd_icms': 0.00,
        }

    _rec_name = 'descricao'
    _order = 'al_icms'

    _sql_constraints = [
        ('al_icms_rd_icms_unique', 'unique (al_icms, rd_icms)',
        u'A alíquota de crédito do ICMS SIMPLES não pode se repetir!'),
        ]

AliquotaICMSSN()


class AliquotaICMSProprio(orm.Model):
    _description = u'Alíquota do ICMS próprio'
    _name = 'sped.aliquotaicmsproprio'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''

        for registro in self.browse(cursor, user_id, ids):
            if registro.al_icms == -1:
                txt = u'Não tributado'
            else:
                txt = u'%.2f%%' % registro.al_icms

                if registro.md_icms != MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO:
                    if registro.md_icms == MODALIDADE_BASE_ICMS_PROPRIO_MARGEM_VALOR_AGREGADO:
                        txt += u'; por MVA de %.4f%%' % registro.pr_icms
                    elif registro.md_icms == MODALIDADE_BASE_ICMS_PROPRIO_PAUTA:
                        txt += u'; por pauta de R$ %.4f' % registro.pr_icms
                    elif registro.md_icms == MODALIDADE_BASE_ICMS_PROPRIO_PRECO_TABELADO_MAXIMO:
                        txt += u'; por preço máximo de R$ %.4f' % registro.pr_icms

                if registro.rd_icms != 0:
                    txt += u'; com redução de %.2f%%' % registro.rd_icms

                txt = txt.replace(u'.', u',').replace(u';', u',')

                if registro.importado:
                    txt += u' (padrão para importados)'

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('al_icms', '>=', texto),
            ]
        return procura

    _columns = {
        'al_icms': CampoPorcentagem(u'Alíquota', required=True,
            help=u'Alíquota aplicável às operações em que houver incidência de ICMS próprio da operação.'),
        'md_icms': fields.selection(MODALIDADE_BASE_ICMS_PROPRIO, u'Modalidade da base de cálculo', required=True,
            help=u'Como será definida a base de cálculo do ICMS próprio da operação.'),
        'pr_icms': CampoQuantidade(u'Parâmetro da base de cálculo', required=True,
            help=u'A margem de valor agregado, ou o valor da pauta/preço tabelado máximo, de acordo com o definido na modalidade da base de cálculo.'),
        'rd_icms': CampoPorcentagem(u'Percentual de redução da alíquota de ICMS',
            help=u'A incidência ou não de redução na base de cálculo é definida também pela situação tributária na operação fiscal.'),
        'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', fnct_search=_procura_descricao),
        'importado': fields.boolean(u'Padrão para produtos importados'),
        }

    _defaults = {
        'al_icms': 0.00,
        'md_icms': MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO,
        'pr_icms': 0.00,
        'rd_icms': 0.00,
        'importado': False,
        }

    _rec_name = 'descricao'
    _order = 'al_icms'

    _sql_constraints = [
        ('al_icms_md_icms_pr_icms_rd_icms_unique', 'unique (al_icms, md_icms, pr_icms, rd_icms)',
        u'A alíquota do ICMS não pode se repetir!'),
        ]

    def create(self, cr, uid, dados, context={}):

        if 'importado' in dados and dados['importado']:
            cr.execute('update sped_aliquotaicmsproprio set importado = False;')

        res = super(AliquotaICMSProprio, self).create(cr, uid, dados, context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        if 'importado' in dados and dados['importado']:
            cr.execute('update sped_aliquotaicmsproprio set importado = False;')

        res = super(AliquotaICMSProprio, self).write(cr, uid, ids, dados, context)

        return res


AliquotaICMSProprio()


class AliquotaICMSST(orm.Model):
    _description = u'Alíquota do ICMS recolhido por substituição tributária'
    _name = 'sped.aliquotaicmsst'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''

        for registro in self.browse(cursor, user_id, ids):
            if registro.al_icms == -1:
                txt = u'Não tributado'
            else:
                txt = u'%.2f%%' % registro.al_icms

                if registro.md_icms == MODALIDADE_BASE_ICMS_ST_PRECO_TABELADO_MAXIMO:
                    txt += u'; POR PREÇO MÁXIMO DE R$ %.4f' % registro.pr_icms
                elif registro.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_NEGATIVA:
                    txt += u'; POR LISTA NEGATIVA DE R$ %.4f' % registro.pr_icms
                elif registro.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_POSITIVA:
                    txt += u'; POR LISTA POSITIVA DE R$ %.4f' % registro.pr_icms
                elif registro.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_NEUTRA:
                    txt += u'; POR LISTA NEUTRA DE R$ %.4f' % registro.pr_icms
                elif registro.md_icms == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
                    txt += u'; POR MVA DE %.4f%%' % registro.pr_icms
                elif registro.md_icms == MODALIDADE_BASE_ICMS_ST_PAUTA:
                    txt += u'; POR PAUTA DE R$ %.4f' % registro.pr_icms

                if registro.rd_icms != 0:
                    txt += u'; com redução de %.2f%%' % registro.rd_icms

                txt = txt.replace(u'.', u',').replace(u';', u',')

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('al_icms', '>=', texto),
            ]
        return procura

    _columns = {
        'al_icms': CampoPorcentagem(u'Alíquota', required=True,
            help=u'Alíquota aplicável às operações em que houver incidência de ICMS retido por substituição tributária.'),
        'md_icms': fields.selection(MODALIDADE_BASE_ICMS_ST, u'Modalidade da base de cálculo', required=True,
            help=u'Como será definida a base de cálculo do ICMS retido por substituição tributária.'),
        'pr_icms': CampoQuantidade(u'Parâmetro da base de cálculo', required=True,
            help=u'A margem de valor agregado, ou o valor da pauta/preço tabelado máximo/lista, de acordo com o definido na modalidade da base de cálculo.'),
        'rd_icms': CampoPorcentagem(u'Percentual de redução da alíquota de ICMS',
            help=u'A incidência ou não de redução na base de cálculo é definida também pela situação tributária na operação fiscal.'),
        'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', fnct_search=_procura_descricao),
        }

    _defaults = {
        'al_icms': 0.00,
        'md_icms': MODALIDADE_BASE_ICMS_ST_PAUTA,
        'pr_icms': 0.00,
        'rd_icms': 0.00,
        }

    _rec_name = 'descricao'
    _order = 'al_icms'

    _sql_constraints = [
        ('al_icms_md_icms_pr_icms_rd_icms_unique', 'unique (al_icms, md_icms, pr_icms, rd_icms)',
        u'A alíquota do ICMS ST não pode se repetir!'),
        ]

AliquotaICMSST()


class AliquotaIPI(orm.Model):
    _description = u'Alíquota do IPI'
    _name = 'sped.aliquotaipi'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''

        for registro in self.browse(cursor, user_id, ids):
            if registro.al_ipi == -1:
                txt = u'Não tributado'
            else:
                if registro.md_ipi == MODALIDADE_BASE_IPI_ALIQUOTA:
                    txt = u'%.2f%%' % registro.al_ipi
                elif registro.md_ipi == MODALIDADE_BASE_IPI_QUANTIDADE:
                    txt = u'POR QUANTIDADE, A R$ %.4f%%' % registro.al_ipi

                txt = txt.replace(u'.', u',').replace(u';', u',')

                txt += u' - CST ENTRADA: %s, CST SAÍDA: %s' % (registro.cst_ipi_entrada, registro.cst_ipi_saida)

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('al_ipi', '>=', texto),
            ]
        return procura

    _columns = {
        'al_ipi': CampoQuantidade(u'Alíquota', required=True,
            help=u'Alíquota aplicável às operações em que houver incidência de IPI.'),
        'md_ipi': fields.selection(MODALIDADE_BASE_IPI, u'Modalidade da base de cálculo', required=True,
            help=u'Como será definida a base de cálculo do IPI.'),
        'cst_ipi_entrada': fields.selection(ST_IPI_ENTRADA, u'Situação tributária nas entradas', required=True),
        'cst_ipi_saida': fields.selection(ST_IPI_SAIDA, u'Situação tributária do nas saídas', required=True),
        'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', fnct_search=_procura_descricao),
        }

    _defaults = {
        'al_ipi': 0.00,
        'md_ipi': MODALIDADE_BASE_IPI_ALIQUOTA,
        'cst_ipi_entrada': ST_IPI_ENTRADA_RECUPERACAO_CREDITO,
        'cst_ipi_saida': ST_IPI_SAIDA_TRIBUTADA,
        }

    _rec_name = 'descricao'
    _order = 'al_ipi'

    _sql_constraints = [
        ('al_ipi_md_ipi_unique', 'unique (al_ipi, md_ipi)',
        u'A alíquota do IPI não pode se repetir!'),
        ]

AliquotaIPI()


class AliquotaPISCOFINS(orm.Model):
    _description = u'Alíquota do PIS e da COFINS'
    _name = 'sped.aliquotapiscofins'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''

        for registro in self.browse(cursor, user_id, ids):
            if registro.al_pis == -1 and registro.al_cofins == -1:
                txt = u'Não tributado ou tributado pelo SIMPLES Nacional'
            else:
                if registro.md_pis_cofins == MODALIDADE_BASE_PIS_ALIQUOTA:
                    txt = u'PIS %.2f%%; COFINS %.2f%%' % (registro.al_pis, registro.al_cofins)
                elif registro.md_pis_cofins == MODALIDADE_BASE_PIS_QUANTIDADE:
                    txt = u'POR QUANTIDADE, PIS A R$ %.4f%%; COFINS A R$ %.4f%%' % (registro.al_pis, registro.al_cofins)

                txt = txt.replace(u'.', u',').replace(u';', u',')

                txt += u' - CST ENTRADA: %s, CST SAÍDA: %s' % (registro.cst_pis_cofins_entrada, registro.cst_pis_cofins_saida)

                if registro.codigo_justificativa:
                    txt += ' - JUSTIFICATIVA: ' + registro.codigo_justificativa

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]
        texto = texto.replace(',', '.')

        procura = [
            '|',
            ('al_pis', '>=', texto),
            '|',
            ('al_cofins', '>=', texto),
            '|',
            ('cst_pis_cofins_saida', 'ilike', texto),
            ('cst_pis_cofins_entrada', 'ilike', texto),
        ]
        return procura

    _columns = {
        'al_pis': CampoQuantidade(u'Alíquota do PIS', required=True),
        'al_cofins': CampoQuantidade(u'Alíquota da COFINS', required=True),
        'md_pis_cofins': fields.selection(MODALIDADE_BASE_PIS, u'Modalidade da base de cálculo do PIS e da COFINS', required=True),
        'cst_pis_cofins_entrada': fields.selection(ST_PIS_ENTRADA, u'Situação tributado nas entradas', required=True),
        'cst_pis_cofins_saida': fields.selection(ST_PIS_SAIDA, u'Situação tributado nas saída', required=True),
        'codigo_justificativa': fields.char(u'Código da justificativa', size=10),
        'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', fnct_search=_procura_descricao),
        }

    _defaults = {
        'al_pis': 0.00,
        'al_cofins': 0.00,
        'md_pis_cofins': MODALIDADE_BASE_PIS_ALIQUOTA,
        'cst_pis_cofins_entrada': ST_PIS_CRED_EXCL_TRIB_MERC_INTERNO,
        'cst_pis_cofins_saida': ST_PIS_TRIB_NORMAL,
        }

    _rec_name = 'descricao'
    _order = 'al_pis'

    _sql_constraints = [
        ('al_pis_al_cofins_md_pis_cofins_cst_pis_cofins_entrada_cst_pis_cofins_saida_codigo_justificativa_unique', 'unique (al_pis, al_cofins, md_pis_cofins, cst_pis_cofins_entrada, cst_pis_cofins_saida, codigo_justificativa)',
        u'As alíquotas do PIS e da COFINS não podem se repetir!'),
        ]

AliquotaPISCOFINS()


#
# Alíquotas padrão para o ISS
#
class AliquotaISS(orm.Model):
    _description = u'Alíquota do ISS'
    _name = 'sped.aliquotaiss'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''

        for registro in self.browse(cursor, user_id, ids):
            if registro.al_iss == -1:
                txt = u'Não tributado'
            else:
                txt = u'%.2f%%' % registro.al_iss
                txt = txt.replace('.', ',')

                if registro.observacao:
                    txt += u', ' + registro.observacao

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('al_iss', '>=', texto),
            ]
        return procura

    _columns = {
        'al_iss': CampoQuantidade(u'Alíquota', required=True),
        'observacao': fields.char(u'Observação', size=60),
        'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', fnct_search=_procura_descricao),
        }

    _defaults = {
        'al_iss': 0.00,
        }

    _rec_name = 'descricao'
    _order = 'al_iss'

    _sql_constraints = [
        ('al_iss_unique', 'unique (al_iss)',
        u'A alíquota do ISS não pode se repetir!'),
        ]

AliquotaISS()
