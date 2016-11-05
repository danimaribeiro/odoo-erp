# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from sped.constante_tributaria import *
from openerp import pooler, sql_db


CAMPOS_TRIBUTARIOS = [
    'regime_tributario',
    'ambiente_nfe',
    'serie_producao',
    'serie_homologacao',
    'tipo_emissao_nfe',
    'serie_scan_producao',
    'serie_scan_homologacao',
    'serie_rps',
    'serie_nfse',
    'ultimo_lote_nfse',
    'ambiente_nfse',
    'provedor_nfse',
    'ultimo_rps',
]


class res_company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        #'cnae': fields.many2one('sped.cnae', u'CNAE principal'),
        'matriz_id': fields.many2one('res.company', u'Usar configuração fiscal da matriz', ondelete='restrict', select=True),
        'regime_tributario': fields.selection(REGIME_TRIBUTARIO, u'Regime tributário'),
        'ambiente_nfe': fields.selection(AMBIENTE_NFE, u'Ambiente da NF-e'),
        'serie_producao': fields.char(u'Série em produção', size=3),
        'serie_homologacao': fields.char(u'Série em homologação', size=3),
        'tipo_emissao_nfe': fields.selection(TIPO_EMISSAO_NFE, u'Tipo de emissão da NF-e'),
        'serie_scan_producao': fields.char(u'Série emissão SCAN em produção', size=3),
        'serie_scan_homologacao': fields.char(u'Série emissão SCAN em homologação', size=3),
        'al_icms_sn_id': fields.many2one('sped.aliquotaicmssn', u'Alíquota de crédito de ICMS'),
        'familiatributaria_id': fields.many2one('sped.familiatributaria', u'Família tributária padrão'),
        'al_pis_cofins_id': fields.many2one('sped.aliquotapiscofins', u'Alíquota padrão do PIS-COFINS'),
        'operacao_id': fields.many2one('sped.operacao', u'Operação padrão para venda (pessoa jurídica/padrão)'),
        'operacao_pessoa_fisica_id': fields.many2one('sped.operacao', u'Operação padrão para venda (pessoa física)'),
        'operacao_ativo_id': fields.many2one('sped.operacao', u'Operação padrão para venda de ativo'),
        'operacao_faturamento_antecipado_id': fields.many2one('sped.operacao', u'Operação padrão para faturamento antecipado'),
        'serie_rps': fields.char(u'Série do RPS', size=3),
        'serie_nfse': fields.char(u'Série da NFS-e', size=3),
        'ultimo_lote_nfse': fields.integer(u'Último lote de NFS-e'),
        'ambiente_nfse': fields.selection(AMBIENTE_NFE, u'Ambiente da NFS-e'),
        'provedor_nfse': fields.selection(PROVEDOR_NFSE, u'Provedor da NFS-e'),
        'ultimo_rps': fields.integer(u'Último RPS'),
        'operacao_servico_id': fields.many2one('sped.operacao', u'Operação padrão para serviços'),
        'cnpj': fields.related('partner_id', 'cnpj_cpf', type='char', size=18, string=u'CNPJ'),
        'company_servico_id': fields.many2one('res.company', u'Empresa para faturamento dos serviços'),
        'natureza_juridica': fields.selection(NATURA_JURIDICA, u'Natureza Jurídica'),

        'simples_anexo': fields.selection(SIMPLES_NACIONAL_ANEXOS, u'Anexo do SIMPLES Nacional'),
        'simples_teto': fields.selection(SIMPLES_NACIONAL_TETOS, u'Faixa de faturamento'),
    }

    _defaults = {
        'regime_tributario': REGIME_TRIBUTARIO_SIMPLES,
        'ambiente_nfe': AMBIENTE_NFE_HOMOLOGACAO,
        'serie_producao': '1',
        'serie_homologacao': '100',
        'tipo_emissao_nfe': TIPO_EMISSAO_NFE_NORMAL,
        'serie_scan_producao': '900',
        'serie_scan_homologacao': '999',
        'serie_rps': '1',
        'serie_nfse': '1',
        'natureza_juridica': '2062',
        'simples_anexo': '1',
        'simples_teto': SIMPLES_NACIONAL_TETO_01,
    }

    def onchange_matriz_id(self, cr, uid, ids, matriz_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not matriz_id:
            return res

        matriz_obj = self.browse(cr, uid, matriz_id)

        valores.update({
            'regime_tributario': matriz_obj.regime_tributario,
            'ambiente_nfe': matriz_obj.ambiente_nfe,
            'serie_producao': matriz_obj.serie_producao,
            'serie_homologacao': matriz_obj.serie_homologacao,
            'tipo_emissao_nfe': matriz_obj.tipo_emissao_nfe,
            'serie_scan_producao': matriz_obj.serie_scan_producao,
            'serie_scan_homologacao': matriz_obj.serie_scan_homologacao,
            'serie_rps': matriz_obj.serie_rps,
            'serie_nfse': matriz_obj.serie_nfse,
            'ultimo_lote_nfse': matriz_obj.ultimo_lote_nfse,
            'ambiente_nfse': matriz_obj.ambiente_nfse,
            'provedor_nfse': matriz_obj.provedor_nfse,
            'ultimo_rps': matriz_obj.ultimo_rps,
        })

        if matriz_obj.al_icms_sn_id:
            valores['al_icms_sn_id'] = matriz_obj.al_icms_sn_id.id
        else:
            valores['al_icms_sn_id'] = False

        if matriz_obj.familiatributaria_id:
            valores['familiatributaria_id'] = matriz_obj.familiatributaria_id.id
        else:
            valores['familiatributaria_id'] = False

        if matriz_obj.al_pis_cofins_id:
            valores['al_pis_cofins_id'] = matriz_obj.al_pis_cofins_id.id
        else:
            valores['al_pis_cofins_id'] = False

        if matriz_obj.operacao_id:
            valores['operacao_id'] = matriz_obj.operacao_id.id
        else:
            valores['operacao_id'] = False

        if matriz_obj.operacao_pessoa_fisica_id:
            valores['operacao_id'] = matriz_obj.operacao_pessoa_fisica_id.id
        else:
            valores['operacao_id'] = False

        if matriz_obj.operacao_ativo_id:
            valores['operacao_id'] = matriz_obj.operacao_ativo_id.id
        else:
            valores['operacao_id'] = False

        if matriz_obj.operacao_servico_id:
            valores['operacao_servico_id'] = matriz_obj.operacao_servico_id.id
        else:
            valores['operacao_servico_id'] = False

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(res_company, self).write(cr, uid, ids, dados, context=context)

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for id in ids:
            company_obj = self.browse(cr, uid, id)

            #
            # Se a empresa possui uma matriz tributária, replica alguns
            # campos na matriz
            #
            if company_obj.matriz_id:
                campos = [
                ]
                matriz_obj = company_obj.matriz_id
            else:
                matriz_obj = company_obj

            novos_dados = {
                'matriz_id': matriz_obj.id,
                'este_id': id,
            }
            for campo in CAMPOS_TRIBUTARIOS:
                if campo in dados:
                    novos_dados[campo] = dados[campo]
                else:
                    novos_dados[campo] = getattr(matriz_obj, campo)

            if 'al_icms_sn_id' in dados:
                novos_dados['al_icms_sn_id'] = str(dados['al_icms_sn_id'])
            elif matriz_obj.al_icms_sn_id:
                novos_dados['al_icms_sn_id'] = str(matriz_obj.al_icms_sn_id.id)
            else:
                novos_dados['al_icms_sn_id'] = 'null'

            if 'al_pis_cofins_id' in dados:
                novos_dados['al_pis_cofins_id'] = str(dados['al_pis_cofins_id'])
            elif matriz_obj.al_pis_cofins_id:
                novos_dados['al_pis_cofins_id'] = str(matriz_obj.al_pis_cofins_id.id)
            else:
                novos_dados['al_pis_cofins_id'] = 'null'

            if 'familiatributaria_id' in dados:
                novos_dados['familiatributaria_id'] = str(dados['familiatributaria_id'])
            elif matriz_obj.familiatributaria_id:
                novos_dados['familiatributaria_id'] = str(matriz_obj.familiatributaria_id.id)
            else:
                novos_dados['familiatributaria_id'] = 'null'

            if 'operacao_id' in dados:
                novos_dados['operacao_id'] = str(dados['operacao_id'])
            elif matriz_obj.operacao_id:
                novos_dados['operacao_id'] = str(matriz_obj.operacao_id.id)
            else:
                novos_dados['operacao_id'] = 'null'

            if 'operacao_servico_id' in dados:
                novos_dados['operacao_servico_id'] = str(dados['operacao_servico_id'])
            elif matriz_obj.operacao_servico_id:
                novos_dados['operacao_servico_id'] = str(matriz_obj.operacao_servico_id.id)
            else:
                novos_dados['operacao_servico_id'] = 'null'

            #
            # Cria um novo cursor para evitar problemas de concorrência
            #
            print('vai criar cursor de company', cr.dbname)
            db = sql_db.db_connect(cr.dbname) # You can get the db name from config
            cr_novo = db.cursor()
            print('criou cursor de company', cr.dbname)
            #
            # Atualiza a matriz
            #
            if novos_dados['matriz_id'] != id:
                cr_novo.execute("""
                    update res_company set
                        regime_tributario = '%(regime_tributario)s',
                        ambiente_nfe = '%(ambiente_nfe)s',
                        serie_producao = '%(serie_producao)s',
                        serie_homologacao = '%(serie_homologacao)s',
                        tipo_emissao_nfe = '%(tipo_emissao_nfe)s',
                        serie_scan_producao = '%(serie_scan_producao)s',
                        serie_scan_homologacao = '%(serie_scan_homologacao)s',
                        serie_rps = '%(serie_rps)s',
                        serie_nfse = '%(serie_nfse)s',
                        ultimo_lote_nfse = %(ultimo_lote_nfse)d,
                        ambiente_nfse = '%(ambiente_nfse)s',
                        provedor_nfse = '%(provedor_nfse)s',
                        ultimo_rps = %(ultimo_rps)d,
                        al_icms_sn_id = %(al_icms_sn_id)s,
                        familiatributaria_id = %(familiatributaria_id)s,
                        operacao_id = %(operacao_id)s,
                        operacao_servico_id = %(operacao_servico_id)s
                    where id = %(matriz_id)d;""" % novos_dados)

            print('gerou a primeira atualizacao')
            #
            # Atualiza as filiais
            #
            cr_novo.execute("""
                update res_company set
                    regime_tributario = '%(regime_tributario)s',
                    ambiente_nfe = '%(ambiente_nfe)s',
                    serie_producao = '%(serie_producao)s',
                    serie_homologacao = '%(serie_homologacao)s',
                    tipo_emissao_nfe = '%(tipo_emissao_nfe)s',
                    serie_scan_producao = '%(serie_scan_producao)s',
                    serie_scan_homologacao = '%(serie_scan_homologacao)s',
                    serie_rps = '%(serie_rps)s',
                    serie_nfse = '%(serie_nfse)s',
                    ultimo_lote_nfse = %(ultimo_lote_nfse)d,
                    ambiente_nfse = '%(ambiente_nfse)s',
                    provedor_nfse = '%(provedor_nfse)s',
                    ultimo_rps = %(ultimo_rps)d,
                    al_icms_sn_id = %(al_icms_sn_id)s,
                    familiatributaria_id = %(familiatributaria_id)s,
                    operacao_id = %(operacao_id)s,
                    operacao_servico_id = %(operacao_servico_id)s
                where matriz_id = %(matriz_id)d and id != %(este_id)d;""" % novos_dados)

            print('gerou a segunda atualizacao')
            cr_novo.commit()
            print('comitou company')
            cr_novo.close()
            print('fechou company')

        return res


res_company()
