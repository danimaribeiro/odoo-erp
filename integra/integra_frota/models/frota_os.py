# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from finan.wizard.finan_relatorio import Report
import os
import base64
from pybrasil.data import parse_datetime, formata_data
from pybrasil.valor.decimal import Decimal as D

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


STORE_VALOR = {
    'frota.os_item': (
        lambda item_pool, cr, uid, ids, context={}: [item_obj.os_id.id for item_obj in item_pool.browse(cr, uid, ids)],
        ['valor'],
        10  #  Prioridade
    ),
    #'frota.os': (
        #lambda os_pool, cr, uid, ids, context={}: ids,
        #['valor_combustivel'],
        #20  #  Prioridade
    #),
}


class frota_os(osv.Model):
    _name = 'frota.os'
    _description = 'Ordens de serviço'
    _order = 'id desc'
    _rec_name = 'veiculo_id'

    def monta_nome(self, cr, uid, id):
        obj = self.browse(cr, uid, id)

        nome = obj.modelo_id.nome + ' / ' + obj.placa

        return nome

    def get_nome(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for id in ids:
            res += [(id, self.monta_nome(cr, uid, id))]

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_nome(cr, uid, ids, context=context)
        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('veiculo_id.placa', 'ilike', texto),
        ]

        return procura

    def imprime_os(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('OS de Frota', cr, uid)

        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'os_frota.jrxml')
        frota = 'os_frota.pdf'

        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        if 'tipo' in context:
            rel.parametros['TIPO'] = context['tipo']
        else:
            rel.parametros['TIPO'] = 'V'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'frota.os'), ('res_id', '=', id), ('name', '=', frota)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': frota,
            'datas_fname': frota,
            'res_model': 'frota.os',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True

    def search_odometro(self, cr, uid, ids, veiculo_id, data, context={}):
        valores = {}
        retorno = {'value': valores}

        data = parse_datetime(data).date()
        data = str(data)[:10]

        if veiculo_id:
            cr.execute("""select
                      cast(fo.valor_atual as numeric(18,2))

                      from frota_odometro fo
                      join frota_veiculo fv on fv.id = fo.veiculo_id

                      where
                      fo.data < '""" + data + """' and
                      fv.id = """ + str(veiculo_id) + """

                      order by
                      fo.data desc
                      limit 1;""")

            dados = cr.fetchall()
            if dados:
                for ret in dados:
                    odometro = float(ret[0])
                    print(odometro)
                valores['valor_anterior'] = odometro
                return retorno
            else:
                valores['valor_anterior'] = 0
                return retorno
        else:
            return retorno

    def _get_numero(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for id in ids:
            res[id] = str(id)

        return res

    def _get_soma_funcao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for os_obj in self.browse(cr, uid, ids):
            #soma = D(os_obj.valor_combustivel or 0)
            soma = D(0)

            for item_obj in os_obj.os_item_ids:
                soma += D(getattr(item_obj, nome_campo, 0))

            soma = soma.quantize(D('0.01'))

            res[os_obj.id] = soma

        return res

    _columns = {
        'state': fields.selection([['P', u'Pendente'], ['A', u'Em andamento'], ['F', u'Fechada']], u'Situação', select=True),
        'compra': fields.selection([['E', u'Abastecimento (gerador)'], ['R', u'Reposição'], ['M', u'Manutenção'], ['A', u'Aquisição']], u'Compra', select=True),
        #'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', fnct_search=_procura_nome),
        'res_company_id': fields.many2one('res.company', u'Empresa'),
        #'numero': fields.char(u'Número da OS', size=30, required=True),
        'numero': fields.function(_get_numero, type='char', size=30, string=u'Número da OS', store=True, select=True),
        'data': fields.datetime(u'Data'),
        'data_fechamento': fields.datetime(u'Data de fechamento'),
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo', required=False),
        'servico_id': fields.many2one('frota.servico', u'Serviço/atividade', required=True),
        'odometro_ids': fields.one2many('frota.odometro', 'os_id', u'Registros de odômetro'),
        'os_item_ids': fields.one2many('frota.os_item', 'os_id', u'Itens de serviço'),

        #
        # Responsáveis e fornecedor
        #
        'hr_employee_id': fields.many2one('hr.employee', u'Empregado/motorista'),
        'motorista_terceiro': fields.char(u'Motorista terceiro', size=30),
        'hr_department_id': fields.many2one('hr.department', u'Departamento/setor/posto'),
        'res_partner_id': fields.many2one('res.partner', u'Fornecedor'),

        #
        # Abastecimento
        #
        'quantidade_combustivel': fields.float(u'Quantidade abastecimento'),
        'unitario_combustivel': fields.float(u'Valor unitário'),
        'valor_combustivel': fields.float(u'Valor abastecimento'),

        #
        # Obs
        #
        'obs': fields.text(u'Observações'),
        'tipo': fields.selection([('P', u'Própria'), ('T', u'Terceiros')], u'Tipo', select=True),

        'valor': fields.function(_get_soma_funcao, type='float', store=STORE_VALOR, digits=(18, 2), string=u'Valor da OS'),
        'justificativa': fields.text(u'Justificativa'),
        'avarias': fields.text(u'Avarias'),
        'data_devolucao': fields.datetime(u'Data de devolução'),
        'locacao_km_inicial': fields.float(u'km inicial'),
        'locacao_km_final': fields.float(u'km final'),

        'cliente_id': fields.many2one('res.partner', u'Cliente'),
        'finan_contrato_id': fields.many2one('finan.contrato', u'Contrato/instalação'),
    }

    _defaults = {
        'tipo': 'P',
        'state': 'P',
        'compra': 'E',
        'data': fields.datetime.now,
    }

    def muda_state(self, cr, uid, ids, context={}):
        if not ids:
            return

        for os_obj in self.browse(cr, uid, ids):
            if os_obj.state == 'P':
                os_obj.write({'state': 'A'})
            elif os_obj.state == 'A':
                os_obj.write({'state': 'F', 'data_fechamento': fields.datetime.now()})
            elif os_obj.state == 'F':
                os_obj.write({'state': 'P'})

        return ids

    def onchange_servico_id(self, cr, uid, ids, veiculo_id, servico_id, res_partner_id, context={}):
        if not veiculo_id or not servico_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        padrao_pool = self.pool.get('frota.veiculo.servico')

        padrao_ids = padrao_pool.search(cr, uid, [('veiculo_id', '=', veiculo_id), ('servico_id', '=', servico_id)])

        if len(padrao_ids) > 0:
            padrao_obj = padrao_pool.browse(cr, uid, padrao_ids[0])
            valores['res_partner_id'] = padrao_obj.partner_id.id

        return res

    def onchange_cliente_id(self, cr, uid, ids, company_id, cliente_id, data, context={}):
        if not company_id or not cliente_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        contrato_pool = self.pool.get('finan.contrato')

        contrato_ids = contrato_pool.search(cr, uid, [('company_id', '=', company_id), ('partner_id', '=', cliente_id), ('natureza', '=', 'R'), '|', ('data_distrato', '=', False), ('data_distrato', '>', data)])

        if len(contrato_ids) > 0:
            valores['finan_contrato_id'] = contrato_ids[0]

        return res

    def valida_abastecimento(self, cr, uid, ids):
        item_pool = self.pool.get('frota.os_item')

        for os_obj in self.browse(cr, uid, ids):
            if 'ABASTECIMENTO' not in os_obj.servico_id.nome.upper():
                continue

            item_abastecimento_obj = None

            excluir_ids = []
            for item_obj in os_obj.os_item_ids:
                if 'ABASTECIMENTO' in item_obj.servico_id.nome.upper():
                    item_abastecimento_obj = item_obj
                    break

            dados = {
                'os_id': os_obj.id,
                'servico_id': os_obj.servico_id.id,
            }

            if os_obj.valor_combustivel:
                dados['valor'] = os_obj.valor_combustivel

            if not item_abastecimento_obj:
                item_pool.create(cr, uid, dados)

            else:
                item_pool.write(cr, uid, [item_abastecimento_obj.id], dados)

    def create(self, cr, uid, dados, context={}):
        if 'quantidade_combustivel' in dados and dados['quantidade_combustivel']:
            if ('unitario_combustivel' not in dados) or (not dados['unitario_combustivel']):
                raise osv.except_osv(u'Erro!', u'É obrigatório preencher o valor unitário!')

            if ('valor_combustivel' not in dados) or (not dados['valor_combustivel']):
                raise osv.except_osv(u'Erro!', u'É obrigatório preencher o valor do abastecimento!')

        if 'unitario_combustivel' in dados and dados['unitario_combustivel']:
            if ('quantidade_combustivel' not in dados) or (not dados['quantidade_combustivel']):
                raise osv.except_osv(u'Erro!', u'É obrigatório preencher a quantidade!')

            if ('valor_combustivel' not in dados) or (not dados['valor_combustivel']):
                raise osv.except_osv(u'Erro!', u'É obrigatório preencher o valor do abastecimento!')

        if 'valor_combustivel' in dados and dados['valor_combustivel']:
            if ('quantidade_combustivel' not in dados) or (not dados['quantidade_combustivel']):
                raise osv.except_osv(u'Erro!', u'É obrigatório preencher a quantidade!')

            if ('valor_combustivel' not in dados) or (not dados['valor_combustivel']):
                raise osv.except_osv(u'Erro!', u'É obrigatório preencher o valor do abastecimento!')

        res = super(frota_os, self).create(cr, uid, dados, context=context)

        self.valida_abastecimento(cr, uid, [res])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(frota_os, self).write(cr, uid, ids, dados, context=context)

        self.valida_abastecimento(cr, uid, ids)

        return res


frota_os()
