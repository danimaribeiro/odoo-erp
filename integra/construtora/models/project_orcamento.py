# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
import os
import base64
from finan.wizard.finan_relatorio import Report
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


STORE_ITEM = {
    'project.orcamento.item': (
        lambda item_pool, cr, uid, ids, context={}: [item_obj.orcamento_id.id for item_obj in item_pool.browse(cr, uid, ids)],
        ['vr_produto'],
        10  #  Prioridade
    ),
}

SITUACAO_ORCAMENTO = [
    ['P', u'Pendente'],
    ['A', u'Aprovado'],
    ['C', u'Cancelado'],
]

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)

MESES = (
    ('01', u'janeiro'),
    ('02', u'fevereiro'),
    ('03', u'março'),
    ('04', u'abril'),
    ('05', u'maio'),
    ('06', u'junho'),
    ('07', u'julho'),
    ('08', u'agosto'),
    ('09', u'setembro'),
    ('10', u'outubro'),
    ('11', u'novembro'),
    ('12', u'dezembro'),
)


class project_orcamento(osv.Model):
    _name = 'project.orcamento'
    _description = u'Orçamento do projeto'
    _rec_name = 'descricao'

    def _get_soma_funcao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for orc_obj in self.browse(cr, uid, ids):
            soma = D('0')
            for item_obj in orc_obj.item_ids:
                soma += D(str(getattr(item_obj, nome_campo, 0)))

            soma = soma.quantize(D('0.01'))

            res[orc_obj.id] = soma

        return res

    def _descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for orcamento_obj in self.browse(cr, uid, ids):

            nome = u'[versão ' + unicode(orcamento_obj.versao or '').strip()

            if orcamento_obj.mes and orcamento_obj.ano:
                nome += '-' + orcamento_obj.mes
                nome += '/' + str(orcamento_obj.ano)

            nome += u'] '

            if orcamento_obj.project_id:
                nome += orcamento_obj.project_id.analytic_account_id.name

            res[orcamento_obj.id] = nome

        return res

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for id in ids:
            res[id] = id

        return res

    _columns = {
        'codigo': fields.function(_codigo, type='integer', string=u'Código', store=True),
        'descricao': fields.function(_descricao, type='char', string=u'Descrição', store=True),
        'situacao': fields.selection(SITUACAO_ORCAMENTO, u'Situação', select=True),
        'project_id': fields.many2one('project.project', u'Projeto', ondelete='restrict'),
        'versao': fields.char(u'Versão', size=60, select=True),
        'mes': fields.selection(MESES, u'Mês', select=True),
        'ano': fields.integer(u'Ano', select=True),
        'etapa_ids': fields.one2many('project.orcamento.etapa', 'orcamento_id', u'Etapas'),
        'item_ids': fields.one2many('project.orcamento.item', 'orcamento_id', u'Itens do orçamento', domain=[('solicitacao_id', '=', False), ('parent_id', '=', False)]),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'vr_produto': fields.function(_get_soma_funcao, type='float', string=u'Valor dos produtos/serviços', store=STORE_ITEM, digits=(18, 2)),
        'obs': fields.text(u'Observação'),
    }

    _defaults = {
        'formato': 'pdf',
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]).zfill(2),
    }

    _defaults = {
        'situacao': 'P',
    }

    def imprime_orcamento_projeto(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        rel = Report(u'Orçamento do Projeto', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_orcamento_projeto.jrxml')
        rel.parametros['ORCAMENTO_ID'] = id
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()
        nome_documento =  u'orcamento_projeto.' + rel_obj.formato

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'project.orcamento'), ('res_id', '=', id), ('name', '=', nome_documento)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome_documento,
            'datas_fname': nome_documento,
            'res_model': 'project.orcamento',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def aprova_orcamento(self, cr, uid, ids, context={}):
        for orc_obj in self.browse(cr, uid, ids):
            for item_obj in orc_obj.item_ids:
                if not (item_obj.quantidade and item_obj.vr_unitario and item_obj.vr_produto):
                    raise osv.except_osv(u'Erro!', u'Não é permitido aprovar o projeto com itens sem quantidade e/ou valor!')

            orc_obj.write({'situacao': 'A'})

            cr.execute("update project_orcamento_item set situacao = 'A' where orcamento_id = " + str(orc_obj.id) + ";")

            #for item_obj in orc_obj.item_ids:
                #item_obj.cria_planejamento_solicitacao(data_aprovacao=fields.date.today())

        return ids

    def cancela_orcamento(self, cr, uid, ids, context={}):
        for orc_obj in self.browse(cr, uid, ids):
            if orc_obj.situacao == 'A':
                raise osv.except_osv(u'Erro!', u'Não é permitido cancelar um orçamento aprovado!')

            orc_obj.write({'situacao': 'C'})

            cr.execute("update project_orcamento_item set situacao = 'C' where orcamento_id = " + str(orc_obj.id) + ";")

        return ids

    def reabre_orcamento(self, cr, uid, ids, context={}):
        for orc_obj in self.browse(cr, uid, ids):
            if orc_obj.situacao == 'A':
                raise osv.except_osv(u'Erro!', u'Não é permitido reabrir um orçamento aprovado!')

            orc_obj.write({'situacao': 'P'})

            cr.execute("update project_orcamento_item set situacao = 'P' where orcamento_id = " + str(orc_obj.id) + ";")

        return ids

    def copy(self, cr, uid, ids, dados, context={}):
        dados['solicitacao_id'] = False
        dados['data_compra_solicitacao'] = False
        dados['percentual_planejado'] = False
        dados['item_ids'] = False
        dados['etapa_ids'] = False
        dados['planejamento_ids'] = False
        dados['versao'] = fields.date.today()[:4] + '-' + str(len(self.pool.get('project.orcamento').search(cr, uid, [('versao', 'ilike', fields.date.today()[:4] + '-')])) + 1).zfill(4)

        novo_orc_id = super(project_orcamento, self).copy(cr, uid, ids, dados, context)
        cr.commit()

        antigo_orc_obj = self.pool.get('project.orcamento').browse(cr, uid, ids)

        etapa_pool = self.pool.get('project.orcamento.etapa')
        item_pool = self.pool.get('project.orcamento.item')

        etapa_nova_da_antiga = {}
        etapa_antiga_da_nova = {}
        for etapa_obj in antigo_orc_obj.etapa_ids:
            nova_etapa_id = etapa_pool.copy(cr, uid, etapa_obj.id, {'orcamento_id': novo_orc_id, 'contas_filhas_ids': False}, context={})
            etapa_nova_da_antiga[etapa_obj.id] = nova_etapa_id
            etapa_antiga_da_nova[nova_etapa_id] = etapa_obj.id

        #
        # Ajusta as etapas pai
        #
        for etapa_nova_id in etapa_antiga_da_nova:
            sql = 'update project_orcamento_etapa set parent_id = {novo_parent_id} where parent_id = {antigo_parent_id} and orcamento_id = {orcamento_id};'
            cr.execute(sql.format(novo_parent_id=etapa_nova_id, antigo_parent_id=etapa_antiga_da_nova[etapa_nova_id], orcamento_id=novo_orc_id))

        for item_obj in antigo_orc_obj.item_ids:
            dados= {
                'orcamento_id': novo_orc_id,
                'solicitacao_id':  False,
                'data_compra_solicitacao': False,
                'percentual_planejado': False,
                'planejamento_ids': False,
            }

            if item_obj.etapa_id:
                dados['etapa_id'] = etapa_nova_da_antiga[item_obj.etapa_id.id]

            item_pool.copy(cr, uid, item_obj.id, dados, context={})

        return novo_orc_id

    def write(self, cr, uid, ids, dados, context={}):
        res = super(project_orcamento, self).write(cr, uid, ids, dados, context)

        for orcamento_obj in self.pool.get('project.orcamento').browse(cr, 1, ids):
            sql = """
            update project_orcamento_item set project_id = {project_id}
            where orcamento_id = {orcamento_id};

            update project_orcamento_item_planejamento set project_id = {project_id}
            where orcamento_id = {orcamento_id};

            update purchase_solicitacao_cotacao_item_orcado set project_id = {project_id}
            where orcamento_id = {orcamento_id};
            """.format(project_id=orcamento_obj.project_id.id, orcamento_id=orcamento_obj.id)
            cr.execute(sql)

        return res


project_orcamento()
