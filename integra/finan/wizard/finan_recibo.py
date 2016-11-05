# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv
import os
from finan_relatorio import Report, JASPER_BASE_DIR
import base64


SQL_DIVIDA = """
select
  data_por_extenso(coalesce(max(l.data_quitacao), current_date)),
  me.nome || ' - ' || ufe.uf || ', ' || data_cabecalho(coalesce(max(l.data_quitacao), current_date)) as data_cabecalho,
  formata_valor(cast({valor_documento} as varchar)) as valor_documento_formatado,
  formata_valor(cast({valor_juros} as varchar)) as valor_juros_formatado,
  formata_valor(cast({valor_multa} as varchar)) as valor_multa_formatado,
  formata_valor(cast({valor_desconto} as varchar)) as valor_desconto_formatado,
  formata_valor(cast({valor} as varchar)) as valor_formatado,
  valor_por_extenso(cast({valor} as varchar)) as extenso,

  e.razao_social as nome_empresa,
  e.cnpj_cpf as cnpj_empresa,
  e.endereco as endereco_empresa,
  e.numero as numero_empresa,
  e.complemento as complemento_empresa,
  e.bairro as bairro_empresa,
  me.nome as cidade_empresa,
  ufe.uf as estado_empresa,
  e.cep as cep_empresa,
  c.photo as logo_empresa,

  case
    when l.tipo in ('R', 'E') then coalesce(p.razao_social, l.complemento)
    else coalesce(p.razao_social, '')
  end as nome_pagador,
  coalesce(p.cnpj_cpf, '') as cnpj_pagador,
  coalesce(p.endereco, '') as endereco_pagador,
  coalesce(p.numero, '') as numero_pagador,
  coalesce(p.complemento, '') as complemento_pagador,
  coalesce(p.bairro, '') as bairro_pagador,
  coalesce(mp.nome, '') as cidade_pagador,
  coalesce(ufp.uf, '') as estado_pagador,
  coalesce(p.cep, '') as cep_pagador,
  coalesce(l.historico, coalesce(l.complemento, '')) as historico,

  case
    when l.tipo in ('R', 'E') then coalesce(r.razao_social, '')
    else coalesce(r.razao_social, l.complemento)
  end as nome_recebedor,
  coalesce(r.cnpj_cpf, '') as cnpj_recebedor

from
  finan_lancamento l
  join res_company c on c.id = l.company_id
  join res_partner e on e.id = c.partner_id
  join sped_municipio me on me.id = e.municipio_id
  join sped_estado ufe on ufe.id = me.estado_id

  left join res_partner p on (l.tipo in ('R', 'E') and p.id = l.partner_id) or (l.tipo in ('P', 'S') and p.id = c.partner_id)
  left join sped_municipio mp on mp.id = p.municipio_id
  left join sped_estado ufp on ufp.id = mp.estado_id

  left join res_partner r on (l.tipo in ('R', 'E') and r.id = c.partner_id) or (l.tipo in ('P', 'S') and r.id = l.partner_id)
  left join sped_municipio mr on mr.id = r.municipio_id
  left join sped_estado ufr on ufr.id = mr.estado_id

  left join finan_documento d on d.id = l.documento_id

where
  l.id in {divida_ids}

group by
  me.nome,
  ufe.uf,
  e.razao_social,
  e.cnpj_cpf,
  e.endereco,
  e.numero,
  e.complemento,
  e.bairro,
  e.municipio_id,
  e.cep,
  c.photo,
  l.tipo,
  p.razao_social,
  l.complemento,
  p.cnpj_cpf,
  p.razao_social,
  p.endereco,
  p.numero,
  p.complemento,
  p.bairro,
  p.municipio_id,
  mp.nome,
  ufp.uf,
  p.cep,
  l.historico,
  r.razao_social,
  r.cnpj_cpf;
"""

SQL_PAGAMENTO = """
select
  divida.data_documento,
  divida.data_vencimento,
  l.data_quitacao,
  coalesce(d.nome, '') as tipo_documento,
  coalesce(divida.numero_documento, '') as numero_documento,
  formata_valor(cast(coalesce(l.valor_documento, coalesce(l.valor, 0)) as varchar)) as valor_documento_formatado

from
  finan_lancamento l
  join finan_lancamento divida on divida.id = l.lancamento_id
  left join finan_documento d on d.id = divida.documento_id

where
  l.lancamento_id in {divida_ids}
  {filtro_adicional}

order by
  l.data_quitacao;
"""

SQL_PAGAMENTO_PREVIO = """
select
  divida.data_documento,
  divida.data_vencimento,
  current_date as data_quitacao,
  coalesce(d.nome, '') as tipo_documento,
  coalesce(divida.numero_documento, '') as numero_documento,
  formata_valor(cast(coalesce(divida.valor_saldo, coalesce(divida.valor, 0)) as varchar)) as valor_documento_formatado

from
  finan_lancamento divida
  left join finan_documento d on d.id = divida.documento_id

where
  divida.id in {divida_ids};
"""



class finan_recibos(osv.osv_memory):
    _description = u'Recibos de lançamentos'
    _name = 'finan.recibos'
    _inherit = 'ir.wizard.screen'
    _rec_name = 'nome'
    _order = 'nome'

    _columns = {
        'nome': fields.char(u'Nome do arquivo', 60, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'data_quitacao': fields.date(u'Data de pagamento'),
        'recibo_previo': fields.boolean(u'Recibo prévio (antes do pagamento efetivo)?'),
        'inclui_multa_prevista': fields.boolean(u'Inclui multa e juros previstos?'),
    }

    _defaults = {
        #'nome': lambda *a: 'recibo.pdf',
    }

    def gerar_recibos(self, cr, uid, ids, context=None):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        lancamento_ids = context['active_ids']
        lancamento_pool = self.pool.get('finan.lancamento')

        lista_recibo = []
        partner_id = False
        tipo = ''
        complemento = ''
        #
        # Fazemos uma pré-validação das informações
        #
        for lancamento_obj in lancamento_pool.browse(cr, uid, lancamento_ids, context):
            if not partner_id:
                partner_id = lancamento_obj.partner_id.id
            elif lancamento_obj.partner_id.id != partner_id:
                raise osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos de clientes/fornecedores diferentes!')

            if tipo == '':
                tipo = lancamento_obj.tipo
            elif lancamento_obj.tipo != tipo:
                raise osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos de tipos diferentes!')

            if complemento == '':
                complemento = lancamento_obj.complemento

            elif lancamento_obj.complemento != complemento:
                raise osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos com complementos diferentes!')

        rel = Report('Recibo', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'recibo_financeiro_varios.jrxml')

        #
        # Prepara os dados
        #
        filtro = {
            'divida_ids': str(tuple(lancamento_ids)).replace(',)', ')'),
            'filtro_adicional': '',
            'valor_documento': "coalesce((select sum(coalesce(p.valor_documento, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
            'valor_juros': "coalesce((select sum(coalesce(p.valor_juros, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
            'valor_multa': "coalesce((select sum(coalesce(p.valor_multa, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
            'valor_desconto': "coalesce((select sum(coalesce(p.valor_desconto, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
            'valor': "coalesce((select sum(coalesce(p.valor_documento, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
        }

        rel_obj = self.browse(cr, uid, ids[0])

        if rel_obj.recibo_previo or tipo in ('E', 'S', 'T'):
            if tipo in ('E', 'S', 'T') or (not rel_obj.inclui_multa_prevista):
                filtro.update({
                    'valor_documento': "coalesce((select sum(coalesce(p.valor_saldo, coalesce(p.valor, 0))) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor_juros': "coalesce((select sum(coalesce(p.valor_juros, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor_multa': "coalesce((select sum(coalesce(p.valor_multa, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor_desconto': "coalesce((select sum(coalesce(p.valor_desconto, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor': "coalesce((select sum(coalesce(p.valor_saldo, coalesce(p.valor, 0))) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                })
            else:
                filtro.update({
                    'valor_documento': "coalesce((select sum(coalesce(p.valor_saldo, coalesce(p.valor, 0))) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor_juros': "coalesce((select sum(coalesce(p.valor_juros_previsto, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor_multa': "coalesce((select sum(coalesce(p.valor_multa_prevista, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor_desconto': "coalesce((select sum(coalesce(p.valor_desconto_previsto, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor': "coalesce((select sum(coalesce(p.valor_saldo, coalesce(p.valor, 0))) + sum(coalesce(p.valor_juros_previsto, 0)) + sum(coalesce(p.valor_multa_prevista, 0)) - sum(coalesce(p.valor_desconto_previsto, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                })

            sql_divida = SQL_DIVIDA.format(**filtro)
            sql_divida = sql_divida.format(**filtro)
            sql_pagamento = SQL_PAGAMENTO_PREVIO.format(**filtro)
            #print(sql_pagamento)

        else:
            if rel_obj.data_quitacao:
                filtro['filtro_adicional'] = "and l.data_quitacao = '{data_quitacao}'".format(data_quitacao=rel_obj.data_quitacao)

            sql_divida = SQL_DIVIDA.format(**filtro)
            sql_pagamento = SQL_PAGAMENTO.format(**filtro)

            if rel_obj.data_quitacao:
                filtro['filtro_adicional'] = "and p.data_quitacao = '{data_quitacao}'".format(data_quitacao=rel_obj.data_quitacao)

            sql_divida = sql_divida.format(**filtro)

        rel.parametros['SQL_DIVIDA'] = sql_divida.replace('\n', ' ')
        rel.parametros['SQL_PAGAMENTO'] = sql_pagamento.replace('\n', ' ')
        #rel.parametros['IDS_PLAIN'] = str(lancamento_ids).replace('[', '(').replace(']', ')')
        rel.parametros['COMPANY_ID'] = self.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio')

        pdf, formato = rel.execute()

        banco_de_dados = cr.dbname
        nome = 'Recibo_' + banco_de_dados + '.pdf'
        self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})


finan_recibos()
