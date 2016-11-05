# -*- coding: utf-8 -*-

from osv import fields, osv
from integra_rh.models.hr_payslip_input import mes_atual, primeiro_ultimo_dia_mes
from openerp import pooler, sql_db


class finan_gera_nota(osv.osv_memory):
    _name = 'finan.gera_nota'
    _description = u'Gerar notas fiscais'

    def _set_input_ids(self, cr, uid, ids, nome_campo, valor_campo, arg, context=None):
        #
        # Salva manualmente as entradas
        #
        if not isinstance(ids, list):
            if ids:
                ids = [ids]
            else:
                ids = []

        if len(valor_campo) and len(ids):
            for gera_nota_obj in self.browse(cr, uid, ids):
                for operacao, entrada_id, valores in valor_campo:
                    #
                    # Cada lanc_item tem o seguinte formato
                    # [operacao, id_original, valores_dos_campos]
                    #
                    # operacao pode ser:
                    # 0 - criar novo registro (no caso aqui, vai ser ignorado)
                    # 1 - alterar o registro
                    # 2 - excluir o registro (também vai ser ignorado)
                    # 3 - desvincula o registro (no caso aqui, seria setar o res_partner_bank_id para outro id)
                    # 4 - vincular a um registro existente
                    #
                    if operacao == 1:
                        self.pool.get('hr.payslip.input').write(cr, uid, [entrada_id], valores)
                    elif operacao == 0:
                        self.pool.get('hr.payslip.input').create(cr, uid, valores)
                    elif operacao == 2:
                        entrada_obj = self.pool.get('hr.payslip.input').browse(cr, uid, entrada_id)
                        if not entrada_obj.payslip_id:
                            self.pool.get('hr.payslip.input').unlink(cr, uid, [entrada_id])

    def _get_lancamento_ids(self, cr, uid, ids, nome_campo, args=None, context={}):
        if ids:
            gera_nota_obj = self.browse(cr, uid, ids[0])
            data_inicial = gera_nota_obj.data_inicial
            data_final = gera_nota_obj.data_final

            if gera_nota_obj.company_id:
                company_id = gera_nota_obj.company_id.id
            else:
                company_id = False

            if gera_nota_obj.operacao_id:
                operacao_id = gera_nota_obj.operacao_id.id
            else:
                operacao_id = False

            if gera_nota_obj.partner_id:
                partner_id = gera_nota_obj.partner_id.id
            else:
                partner_id = False

            if gera_nota_obj.contrato_id:
                contrato_id = gera_nota_obj.contrato_id.id
            else:
                contrato_id = False
                
            if gera_nota_obj.grupo_economico_id:
                grupo_economico_id = gera_nota_obj.grupo_economico_id.id
            else:
                grupo_economico_id = False

        else:
            if 'data_inicial' not in context or 'data_final' not in context:
                return {}

            data_inicial = context['data_inicial']
            data_final = context['data_final']

            if not data_inicial or not data_final:
                raise osv.except_osv(u'Atenção', u'É preciso escolher um período!')

            company_id = context.get('company_id', False)
            operacao_id = context.get('operacao_id', False)
            grupo_economico_id = context.get('grupo_economico_id', False)


        sql = """
            select l.id
            from finan_lancamento l
            join finan_contrato c on c.id = l.contrato_id
            join res_company e on e.id = c.company_id
            left join res_company cc on cc.id = e.parent_id
            join res_partner p on p.id = l.partner_id

            where
              l.tipo = 'R'
              and (c.suspenso = False or c.suspenso is null)
              and l.sped_documento_id is null
              and l.situacao in ('A vencer', 'Vencido', 'Vence hoje')
              and c.operacao_fiscal_servico_id is not null
              and l.data_vencimento between '{data_inicial}' and '{data_final}'
        """

        if company_id:
            sql += """
            and (c.company_id = {company_id}
            or e.parent_id = {company_id}
            or cc.id = {company_id})
            """

        if operacao_id:
            sql += """
            and c.operacao_fiscal_servico_id = {operacao_id}
            """

        if contrato_id:
            sql += """
            and c.id = {contrato_id}
            """

        if partner_id:
            sql += """
            and l.partner_id = {partner_id}
            """
            
        if grupo_economico_id:
            sql += """
            and c.grupo_economico_id = {grupo_economico_id}
            """
            
        sql += """
        order by
            p.razao_social,
            p.cnpj_cpf,
            l.valor_documento desc
        """

        sql = sql.format(data_inicial=data_inicial, data_final=data_final, company_id=company_id, operacao_id=operacao_id, contrato_id=contrato_id, partner_id=partner_id,grupo_economico_id=grupo_economico_id)
        print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        lista_lancamentos = []
        for id, in dados:
            lista_lancamentos.append(id)

        res = {}
        if ids:
            for id in ids:
                res[id] = lista_lancamentos
        else:
            res = lista_lancamentos

        return res

    def _get_contrato_sem_vencimento_ids(self, cr, uid, ids, nome_campo, args=None, context={}):
        if ids:
            gera_nota_obj = self.browse(cr, uid, ids[0])
            data_inicial = gera_nota_obj.data_inicial
            data_final = gera_nota_obj.data_final

            if gera_nota_obj.company_id:
                company_id = gera_nota_obj.company_id.id
            else:
                company_id = False

            if gera_nota_obj.operacao_id:
                operacao_id = gera_nota_obj.operacao_id.id
            else:
                operacao_id = False

            if gera_nota_obj.partner_id:
                partner_id = gera_nota_obj.partner_id.id
            else:
                partner_id = False

            if gera_nota_obj.contrato_id:
                contrato_id = gera_nota_obj.contrato_id.id
            else:
                contrato_id = False
                
            if gera_nota_obj.grupo_economico_id:
                grupo_economico_id = gera_nota_obj.grupo_economico_id.id
            else:
                grupo_economico_id = False

        else:
            if 'data_inicial' not in context or 'data_final' not in context:
                return {}

            data_inicial = context['data_inicial']
            data_final = context['data_final']

            if not data_inicial or not data_final:
                raise osv.except_osv(u'Atenção', u'É preciso escolher um período!')

            company_id = context.get('company_id', False)
            operacao_id = context.get('operacao_id', False)
            grupo_economico_id = context.get('grupo_economico_id', False)


        sql = """
select
c.id
from finan_contrato c
join res_company e on e.id = c.company_id
left join res_company cc on cc.id = e.parent_id

where not exists
(select
  l.contrato_id
from finan_lancamento l
where l.tipo = 'R'
and l.contrato_id = c.id
and l.company_id = c.company_id
and l.data_vencimento between '{data_inicial}' and '{data_final}')
and c.ativo = True
and c.natureza = 'R'
        """

        if company_id:
            sql += """
            and (c.company_id = {company_id}
            or e.parent_id = {company_id}
            or cc.id = {company_id})
            """

        print(sql.format(data_inicial=data_inicial, data_final=data_final, company_id=company_id))
        cr.execute(sql.format(data_inicial=data_inicial, data_final=data_final, company_id=company_id))
        dados = cr.fetchall()

        print(dados)

        lista_contratos = []
        for id, in dados:
            lista_contratos.append(id)

        res = {}
        if ids:
            for id in ids:
                res[id] = lista_contratos
        else:
            res = lista_contratos

        return res

    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato'),
        'operacao_id': fields.many2one('sped.operacao', u'Operação fiscal'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'ignora_erros': fields.boolean(u'Ignorar mensagens de falta de configuração fiscal?'),
        'lancamento_ids': fields.function(_get_lancamento_ids, method=True, type='one2many', string=u'Contratos', relation='finan.lancamento'),  # , fnct_inv=_set_input_ids),
        'contrato_sem_vencimento_ids': fields.function(_get_contrato_sem_vencimento_ids, method=True, type='one2many', string=u'Contratos', relation='finan.contrato'),  # , fnct_inv=_set_input_ids),
        'grupo_economico_id': fields.many2one('finan.grupo.economico', u'Grupo econômico', ondelese='restrict'),        
    }

    _defaults = {
        'data_inicial': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_atual())[0],
        'data_final': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_atual())[1],
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.gera_nota', context=c),
        'ignora_erros': True,
    }

    def gera_notas_servico(self, cr, uid, ids, context={}):
        lancamentos = context['lancamento_ids']
        lancamento_ids = []

        ignora_erros = context.get('ignora_erros', False)

        for operacao, lancamento_id, valores in lancamentos:
            lancamento_ids += [lancamento_id]

        #
        # Verifica novamente os lancamentos a gerar notas, para evitar os casos de deadlock
        # Cria um novo cursor para evitar problemas de concorrência
        #
        db = sql_db.db_connect(cr.dbname) # You can get the db name from config
        cr_novo = db.cursor()
        lancamento_sem_nota_ids = []
        for lancamento_id in lancamento_ids:
            sql = '''
              select
              l.sped_documento_id
              from finan_lancamento l
              join sped_documento d on d.id = l.sped_documento_id
              where l.id = {lancamento_id}
            '''.format(lancamento_id=lancamento_id)
            cr_novo.execute(sql)
            ja_existe = cr_novo.fetchall()
            if len(ja_existe) == 0:
                lancamento_sem_nota_ids.append(lancamento_id)
        cr_novo.commit()
        cr_novo.close()

        for lancamento_obj in self.pool.get('finan.lancamento').browse(cr, uid, lancamento_sem_nota_ids):
            if ignora_erros:
                try:
                    lancamento_obj.gera_nfse()
                except:
                    try:
                        cr.execute('delete from sped_documento where finan_lancamento_id = {lancamento_id};'.format(lancamento_id=lancamento_obj.id))
                    except:
                        pass
            else:
                lancamento_obj.gera_nfse()

        lancamento_ids = self._get_lancamento_ids(cr, uid, ids, 'lancamento_ids', context=context)

        return self.write(cr, uid, ids, {'lancamento_ids': lancamento_ids})

    def busca_lancamentos(self, cr, uid, ids, context={}):
        #valores = {}
        #retorno = {'value': valores}

        lancamento_ids = self._get_lancamento_ids(cr, uid, ids, 'lancamento_ids', context=context)
        contrato_ids = self._get_contrato_sem_vencimento_ids(cr, uid, ids, 'contrato_sem_vencimento_ids', context=context)

        return self.write(cr, uid, ids, {'lancamento_ids': lancamento_ids, 'contrato_sem_vencimento_ids': contrato_ids})


finan_gera_nota()
