# -*- encoding: utf-8 -*-


from decimal import Decimal as D
from osv import osv, fields
#from plano_contas_antigo import PLANO_CONTAS
from copy import copy
from pybrasil.valor.decimal import Decimal as D
from moni import le_arquivo_moni
from pybrasil.inscricao import *
from pybrasil.data import hoje
from dateutil.relativedelta import relativedelta


class importa_moni(osv.Model):
    _name = 'importa.moni'
    _description = u'Importação do MONI'

    def _importado(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for moni_obj in self.browse(cr, uid, ids):
            res[moni_obj.id] = False

            if moni_obj.contrato_id:
                res[moni_obj.id] = True

        return res

    def _inadimplente(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for moni_obj in self.browse(cr, uid, ids):
            res[moni_obj.id] = False

            if not moni_obj.partner_id:
                continue

            sql = """
            select
                count(l.*)

            from
                finan_lancamento l

            where
                l.tipo = 'R'
                and l.situacao = 'Vencido'
                and l.data_vencimento <= '{data_vencimento}'
                and l.partner_id = {partner_id};
            """

            filtro = {
                'partner_id': moni_obj.partner_id.id,
                'data_vencimento': str(hoje() + relativedelta(days=-10))[:10]
            }

            sql = sql.format(**filtro)
            cr.execute(sql)
            dados = cr.fetchall()

            if dados[0][0]:
                res[moni_obj.id] = True

        return res

    _columns = {
        'importado': fields.function(_importado, type='boolean', string=u'Importado', store=True, select=True),
        'inadimplente': fields.function(_inadimplente, type='boolean', string=u'Inadimplente', store=True, select=True),

        'codigo_moni': fields.char(u'Código MONI', size=10, select=True),
        'codigo_cliente': fields.char(u'Código cliente', size=4, select=True),
        'cnpj_cpf': fields.char(u'CNPJ/CPF', size=18),
        'razao_social': fields.char(u'Razão Social', size=100),
        'fantasia': fields.char(u'Fantasia', size=100),
        'endereco': fields.char(u'Endereço', size=80),
        'numero': fields.char(u'Número', size=6),
        'bairro': fields.char(u'Bairro', size=30),
        'cidade': fields.char(u'Cidade', size=40),
        'estado': fields.char(u'Estado', size=2),
        'cep': fields.char(u'CEP', size=9),
        'contato': fields.char(u'Contato', size=15),

        'cancelado': fields.boolean(u'Cancelado?'),
        'cancelado_em': fields.datetime(u'Cancelado em'),
        'cancelado_por': fields.char(u'Cancelado por', size=20),
        'suspenso': fields.boolean(u'Suspenso?'),
        'suspenso_em': fields.datetime(u'Suspenso em'),
        'suspenso_por': fields.char(u'Suspenso por', size=20),

        'ultimo_open_close': fields.datetime(u'Último open/close'),
        'ultima_ocorrencia': fields.datetime(u'Última ocorrência'),
        'ultimo_teste_automatico': fields.datetime(u'Último teste automático'),
        'ultimo_disparo': fields.datetime(u'Último disparo'),

        'total_os': fields.integer(u'OSs abertas'),
        'total_ocorrencia': fields.integer(u'Ocorrências abertas'),
        'total_deslocamento': fields.integer(u'Deslocamentos registrados'),

        'partner_id': fields.many2one('res.partner', u'Cliente no Integra'),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato no Integra'),

        'recalculo': fields.integer(u'Campo para obrigar o recalculo dos itens'),
    }

    def importa_arquivo(self, cr, uid, ids, context={}):
        moni_pool = self.pool.get('importa.moni')
        partner_pool = self.pool.get('res.partner')
        contrato_pool = self.pool.get('finan.contrato')

        clientes = le_arquivo_moni()

        for cliente in clientes:
            moni_ids = moni_pool.search(cr, uid, [('codigo_moni', '=', cliente.moni_id)])

            if not moni_ids:
                dados = {
                    'codigo_moni': cliente.moni_id,
                    'codigo_cliente': cliente.codigo_cliente,
                    'cnpj_cpf': cliente.cnpj_cpf,
                    'razao_social': cliente.razao_social,
                    'fantasia': cliente.fantasia,
                    'endereco': cliente.endereco,
                    'numero': cliente.numero,
                    'bairro': cliente.bairro,
                    'cidade': cliente.cidade,
                    'estado': cliente.estado,
                    'cep': cliente.cep,
                    'contato': cliente.contato,
                }

                cnpj_cpf = ''
                if valida_cnpj(cliente.cnpj_cpf):
                    cnpj_cpf = formata_cnpj(cliente.cnpj_cpf)
                elif valida_cpf(cliente.cnpj_cpf):
                    cnpj_cpf = formata_cpf(cliente.cnpj_cpf)

                dados['cnpj_cpf'] = cnpj_cpf

                if cnpj_cpf:
                    partner_ids = partner_pool.search(cr, uid, [('cnpj_cpf', '=', cnpj_cpf)])
                    contrato_ids = contrato_pool.search(cr, uid, [('partner_id.cnpj_cpf', '=', cnpj_cpf)])

                    if len(contrato_ids) == 1:
                        dados['contrato_id'] = contrato_ids[0]
                    elif len(partner_ids):
                        dados['partner_id'] = partner_ids[0]

                moni_pool.create(cr, uid, dados)


importa_moni()
