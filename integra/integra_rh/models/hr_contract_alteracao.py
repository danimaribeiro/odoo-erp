# -*- coding: utf-8 -*-


from osv import fields, osv
from hr_contract import (REGIME_PREVIDENCIARIO, REGIME_TRABALHISTA, NATUREZA_ATIVIDADE, CATEGORIA_TRABALHADOR, UNIDADE_SALARIO, TIPO_ESCALA, TIPO_JORNADA)
from pybrasil.data import formata_data

TIPO_ALTERACAO = [
    ('C', u'Cargo/atividade'),
    ('R', u'Remuneração'),
    ('D', u'Duração'),
    ('J', u'Jornada'),
    ('S', u'Filiação sindical'),
    ('A', u'Alvará judicial'),
    ('L', u'Local de trabalho'),
]


class hr_contract_alteracao(osv.Model):
    _name = 'hr.contract_alteracao'
    _description = 'Alteração contratual'
    #_inherit = 'hr.contract'
    _order = 'contract_id, tipo_alteracao, data_alteracao desc'

    def get_alteracao_id(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        contrato_pool = self.pool.get('hr.contract')

        for alteracao_obj in self.browse(cr, uid, ids):
            dados = {
                'contract_id': alteracao_obj.contract_id.id,
                'tipo_alteracao': alteracao_obj.tipo_alteracao,
            }

            sql = """
                select
                    ca.id

                from hr_contract_alteracao ca
                join hr_contract c on c.id = ca.contract_id
                join res_company co on co.id = c.company_id
                join hr_employee e on e.id = c.employee_id

                where
                    c.id = {contract_id} and ca.tipo_alteracao =  '{tipo_alteracao}'
                order by
                    e.nome;""".format(**dados)
            #print(sql)
            cr.execute(sql)
            alteracao_ids_lista = cr.fetchall()
            alteracao_ids = []
            for dados in alteracao_ids_lista:
                alteracao_ids.append(dados[0])
            #print(alteracao_ids)
            res[alteracao_obj.id] = alteracao_ids

        return res

    _columns = {
        'contract_id': fields.many2one('hr.contract', u'Contrato', select=True, ondelete='cascade'),
        'data_alteracao': fields.date(u'Data da alteração'),
        'tipo_alteracao': fields.selection(TIPO_ALTERACAO, u'Tipo da alteração'),

        #
        # Alterações de cargo
        #
        'regime_trabalhista': fields.selection(REGIME_TRABALHISTA, u'Regime trabalhista'),
        'regime_previdenciario': fields.selection(REGIME_PREVIDENCIARIO, u'Regime previdenciário'),
        'natureza_atividade': fields.selection(NATUREZA_ATIVIDADE, u'Natureza da atividade'),
        'categoria_trabalhador': fields.selection(CATEGORIA_TRABALHADOR, u'Categoria do trabalhador'),
        'codigo_cargo': fields.char(u'Código do cargo', size=30),
        'job_id': fields.many2one('hr.job', u'Função', select=True, ondelete='restrict'),
        'company_id': fields.related('contract_id', 'company_id',  type='many2one', relation='res.company', string=u'Empresa'),

        #
        # Alteração na remuneração
        #
        'wage': fields.float(u'Salário', digits=(18, 2)),
        'unidade_salario': fields.selection(UNIDADE_SALARIO, u'Unidade do salário'),
        'salario_variavel': fields.float(u'Salário variável', digits=(18, 2)),
        'unidade_salario_variavel': fields.selection(UNIDADE_SALARIO, u'Unidade do salário variável'),
        'horas_mensalista': fields.integer(u'Horas de trabalho no mês'),
        'struct_id': fields.many2one('hr.payroll.structure', u'Estrutura de salário', select=True, ondelete='restrict'),

        #'tipo_contrato': fields.selection(TIPO_CONTRATO, u'Tipo do contrato'),

        #
        # Alteração no local de trabalho
        #
        'department_id': fields.many2one('hr.department', 'Departmento/lotação', select=True, ondelete='restrict'),
        'lotacao_id': fields.many2one('res.partner', 'Lotação/cliente/fornecedor', select=True, ondelete='restrict'),

        #
        # Alteração no sindicato
        #
        'sindicato_id': fields.many2one('res.partner', u'Filiação sindical', select=True, ondelete='restrict'),

        #
        # Alteração na jornada de trabalho
        #
        'jornada_tipo': fields.selection(TIPO_JORNADA, 'Tipo de jornada de trabalho'),
        'jornada_segunda_a_sexta_id': fields.many2one('hr.jornada', u'Jornada padrão de segunda a sexta-feira', select=True, ondelete='restrict'),
        'jornada_segunda_id': fields.many2one('hr.jornada', u'Jornada na segunda-feira', select=True, ondelete='restrict'),
        'jornada_terca_id': fields.many2one('hr.jornada', u'Jornada na terça-feira', select=True, ondelete='restrict'),
        'jornada_quarta_id': fields.many2one('hr.jornada', u'Jornada na quarta-feira', select=True, ondelete='restrict'),
        'jornada_quinta_id': fields.many2one('hr.jornada', u'Jornada na quinta-feira', select=True, ondelete='restrict'),
        'jornada_sexta_id': fields.many2one('hr.jornada', u'Jornada na sexta-feira', select=True, ondelete='restrict'),
        'jornada_sabado_id': fields.many2one('hr.jornada', u'Jornada no sábado', select=True, ondelete='restrict'),
        'jornada_domingo_id': fields.many2one('hr.jornada', u'Jornada no domingo', select=True, ondelete='restrict'),
        'jornada_turno': fields.integer(u'Turno'),
        'jornada_turno_id': fields.many2one('hr.jornada', u'Jornada turno flexível', select=True, ondelete='restrict'),
        'jornada_escala': fields.selection(TIPO_ESCALA, u'Escala'),
        'jornada_escala_id': fields.many2one('hr.jornada', u'Jornada escala', select=True, ondelete='restrict'),
        'alteracao_ids': fields.function(get_alteracao_id, type='one2many', relation='hr.contract_alteracao', method=True, string=u'Alterações'),
        #'motivo': fields.char(u'Motivo', size=60),
        'motivo_id': fields.many2one('hr.motivo.alteracao.contratual', u'Motivo', ondelete='restrict'),
        'obs': fields.char(u'Obs', size=250),
    }

    _defaults = {
        'data_alteracao': fields.date.today,
    }

    def ajusta_contrato(self, cr, uid, ids, exclusao=False):
        print('ids das alterações', ids)
        contract_pool = self.pool.get('hr.contract')

        for alteracao_obj in self.browse(cr, uid, ids):
            if alteracao_obj.tipo_alteracao == 'C':
                lista_alteracoes = alteracao_obj.contract_id.alteracao_cargo_ids

            elif alteracao_obj.tipo_alteracao == 'R':
                lista_alteracoes = alteracao_obj.contract_id.alteracao_remuneracao_ids

            elif alteracao_obj.tipo_alteracao == 'D':
                lista_alteracoes = alteracao_obj.contract_id.alteracao_duracao_ids

            elif alteracao_obj.tipo_alteracao == 'J':
                lista_alteracoes = alteracao_obj.contract_id.alteracao_jornada_ids

            elif alteracao_obj.tipo_alteracao == 'S':
                lista_alteracoes = alteracao_obj.contract_id.alteracao_sindicato_ids

            elif alteracao_obj.tipo_alteracao == 'A':
                lista_alteracoes = alteracao_obj.contract_id.alteracao_alvara_ids

            elif alteracao_obj.tipo_alteracao == 'L':
                lista_alteracoes = alteracao_obj.contract_id.alteracao_lotacao_ids

            item_mais_recente = lista_alteracoes[0]
            print('lista_alteracoes', lista_alteracoes)
            print('item mais recente', item_mais_recente)

            if exclusao and len(lista_alteracoes) > 1:
                if alteracao_obj.id == item_mais_recente.id:
                    item_mais_recente = lista_alteracoes[1]

            dados = {}
            if alteracao_obj.tipo_alteracao == 'R':
                dados = {
                    'wage': item_mais_recente.wage,
                    'unidade_salario': item_mais_recente.unidade_salario,
                    'horas_mensalista': item_mais_recente.horas_mensalista,
                    'salario_variavel': item_mais_recente.salario_variavel,
                    'unidade_salario_variavel': item_mais_recente.unidade_salario_variavel,
                    'struct_id': item_mais_recente.struct_id.id,
                }

            elif alteracao_obj.tipo_alteracao == 'J':
                dados = {
                    'jornada_tipo': item_mais_recente.jornada_tipo,
                    'jornada_segunda_a_sexta_id': item_mais_recente.jornada_segunda_a_sexta_id.id,
                    'jornada_segunda_id': item_mais_recente.jornada_segunda_id.id,
                    'jornada_terca_id': item_mais_recente.jornada_terca_id.id,
                    'jornada_quarta_id': item_mais_recente.jornada_quarta_id.id,
                    'jornada_quinta_id': item_mais_recente.jornada_quinta_id.id,
                    'jornada_sexta_id': item_mais_recente.jornada_sexta_id.id,
                    'jornada_sabado_id': item_mais_recente.jornada_sabado_id.id,
                    'jornada_domingo_id': item_mais_recente.jornada_domingo_id.id,
                    'jornada_turno': item_mais_recente.jornada_turno,
                    'jornada_turno_id': item_mais_recente.jornada_turno_id.id,
                    'jornada_escala': item_mais_recente.jornada_escala,
                    'jornada_escala_id': item_mais_recente.jornada_escala_id.id,
                }

            elif alteracao_obj.tipo_alteracao == 'D':
                #lista_alteracoes = alteracao_obj.contract_id.alteracao_duracao_ids
                pass

            elif alteracao_obj.tipo_alteracao == 'C':
                dados = {
                    'regime_trabalhista': item_mais_recente.regime_trabalhista,
                    'regime_previdenciario': item_mais_recente.regime_previdenciario,
                    'natureza_atividade': item_mais_recente.natureza_atividade,
                    'categoria_trabalhador': item_mais_recente.categoria_trabalhador,
                    'job_id': item_mais_recente.job_id.id,
                }

            elif alteracao_obj.tipo_alteracao == 'S':
                dados = {
                    'sindicato_id': item_mais_recente.sindicato_id.id,
                }

            elif alteracao_obj.tipo_alteracao == 'A':
                #lista_alteracoes = alteracao_obj.contract_id.alteracao_alvara_ids
                pass

            elif alteracao_obj.tipo_alteracao == 'L':
                dados = {
                    'department_id': item_mais_recente.department_id.id,
                    'lotacao_id': item_mais_recente.lotacao_id.id,
                }

            print(dados)
            print(alteracao_obj.contract_id.id)
            contract_pool.write(cr, uid, [alteracao_obj.contract_id.id], dados)

    def create(self, cr, uid, dados, context={}):

        if 'data_alteracao' in dados and dados['data_alteracao']:
            data_alteracao = dados['data_alteracao']
            if 'contract_id' in dados and dados['contract_id']:
                contract_id =  dados['contract_id']
                contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_id)

                data_alter = str(data_alteracao)
                if data_alteracao < contract_obj.date_start:
                    date_start = str(contract_obj.date_start)
                    mensagem = u'Funcionário '
                    mensagem += contract_obj.employee_id.nome
                    mensagem += u', data da alteração contratual '

                    if dados['tipo_alteracao'] == 'R':
                        mensagem += u' da remuneração '
                    elif dados['tipo_alteracao'] == 'D':
                        mensagem += u' da duração '
                    elif dados['tipo_alteracao'] == 'J':
                        mensagem += u' da jornada '
                    elif dados['tipo_alteracao'] == 'S':
                        mensagem += u' da filiação sindical '
                    elif dados['tipo_alteracao'] == 'L':
                        mensagem += u' do local de trabalho '

                    mensagem +=  formata_data(data_alter)
                    mensagem += u' menor do que data de admissão '
                    mensagem += formata_data(date_start)
                    raise osv.except_osv(u'Erro!', mensagem)

                if contract_obj.date_end:
                    if data_alteracao > contract_obj.date_end:
                        date_end = str(contract_obj.date_end)
                        raise osv.except_osv(u'Erro!', u'Funcionário ' + contract_obj.employee_id.nome + ', data da alteração contratual ' +  formata_data(data_alter) + u' +  maior do que data de demissão '  +  formata_data(date_end))

        res = super(hr_contract_alteracao, self).create(cr, uid, dados, context=context)

        self.ajusta_contrato(cr, uid, [res])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        for so in self.browse(cr, uid, ids):
            data_alteracao = dados.get('data_alteracao', str(so.data_alteracao))

            mensagem = u'Data da alteração contratual '

            if so.tipo_alteracao == 'R':
                mensagem += u' da remuneração '
            elif so.tipo_alteracao == 'D':
                mensagem += u' da duração '
            elif so.tipo_alteracao == 'J':
                mensagem += u' da jornada '
            elif so.tipo_alteracao == 'S':
                mensagem += u' da filiação sindical '
            elif so.tipo_alteracao == 'L':
                mensagem += u' do local de trabalho '

            mensagem += formata_data(data_alteracao)

            if data_alteracao < so.contract_id.date_start:
                date_start = str(so.contract_id.date_start)
                mensagem += u' maior que data de admissão '
                mensagem +=  formata_data(date_start)

                raise osv.except_osv(u'Erro!', mensagem  )

            if so.contract_id.date_end:
                if data_alteracao > so.contract_id.date_end:
                    date_end = str(so.contract_id.date_end)
                    mensagem += u' maior que data de rescisão '
                    mensagem +=  formata_data(date_end)
                    raise osv.except_osv(u'Erro!', mensagem)

        res = super(hr_contract_alteracao, self).write(cr, uid, ids, dados, context=context)

        self.ajusta_contrato(cr, uid, ids)

        return res

    def unlink(self, cr, uid, ids, context={}):
        self.ajusta_contrato(cr, uid, ids, exclusao=True)
        res = super(hr_contract_alteracao, self).unlink(cr, uid, ids, context=context)
        return res

    def onchange_contract_id(self, cr, uid, ids, contract_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        print('contract_id', contract_id)

        if not contract_id:
            return res

        contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_id)

        valores = {
            'regime_trabalhista': contract_obj.regime_trabalhista,
            'regime_previdenciario': contract_obj.regime_previdenciario,
            'natureza_atividade': contract_obj.natureza_atividade,
            'categoria_trabalhador': contract_obj.categoria_trabalhador,
            'codigo_cargo': contract_obj.codigo_cargo,
            'job_id': contract_obj.job_id.id if contract_obj.job_id else False,
            'company_id': contract_obj.company_id.id if contract_obj.company_id else False,

            #
            # Alteração na remuneração
            #
            'wage': contract_obj.wage,
            'unidade_salario': contract_obj.unidade_salario,
            'salario_variavel': contract_obj.salario_variavel,
            'unidade_salario_variavel': contract_obj.unidade_salario_variavel,
            'horas_mensalista': contract_obj.horas_mensalista,
            'struct_id': contract_obj.struct_id.id if contract_obj.struct_id else False,

            #'tipo_contrato': contract_obj.tipo_contrato,

            #
            # Alteração no local de trabalho
            #
            'department_id': contract_obj.department_id.id if contract_obj.department_id else False,
            'lotacao_id': contract_obj.lotacao_id.id if contract_obj.lotacao_id else False,

            #
            # Alteração no sindicato
            #
            'sindicato_id': contract_obj.sindicato_id.id if contract_obj.sindicato_id else False,

            #
            # Alteração na jornada de trabalho
            #
            'jornada_tipo': contract_obj.jornada_tipo,
            'jornada_segunda_a_sexta_id': contract_obj.jornada_segunda_a_sexta_id.id if contract_obj.jornada_segunda_a_sexta_id else False,
            'jornada_segunda_id': contract_obj.jornada_segunda_id.id if contract_obj.jornada_segunda_id else False,
            'jornada_terca_id': contract_obj.jornada_terca_id.id if contract_obj.jornada_terca_id else False,
            'jornada_quarta_id': contract_obj.jornada_quarta_id.id if contract_obj.jornada_quarta_id else False,
            'jornada_quinta_id': contract_obj.jornada_quinta_id.id if contract_obj.jornada_quinta_id else False,
            'jornada_sexta_id': contract_obj.jornada_sexta_id.id if contract_obj.jornada_sexta_id else False,
            'jornada_sabado_id': contract_obj.jornada_sabado_id.id if contract_obj.jornada_sabado_id else False,
            'jornada_domingo_id': contract_obj.jornada_domingo_id.id if contract_obj.jornada_domingo_id else False,
            'jornada_turno': contract_obj.jornada_turno,
            'jornada_turno_id': contract_obj.jornada_turno_id.id if contract_obj.jornada_turno_id else False,
            'jornada_escala': contract_obj.jornada_escala,
            'jornada_escala_id': contract_obj.jornada_escala_id.id if contract_obj.jornada_escala_id else False,
        }

        res['value'] = valores

        print(valores)

        return res


    def onchange_data_alteracao(self, cr, uid, ids, data_alteracao, contract_id, context={}):

        if not contract_id:
            return

        contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_id)

        data_ater = str(data_alteracao)
        if data_alteracao < contract_obj.date_start:
            date_start = str(contract_obj.date_start)
            raise osv.except_osv(u'Erro!', u'Data de Locação ' +  formata_data(data_ater) + u' maior que Data de Admissão ' +  formata_data(date_start))

        if contract_obj.date_end:
            if data_alteracao > contract_obj.date_end:
                date_end = str(contract_obj.date_end)
                raise osv.except_osv(u'Erro!', u'Data de Locação ' +  formata_data(data_alteracao) + u' +  maior que Data de Demissão '  +  formata_data(date_end))
        return

hr_contract_alteracao()


class hr_contract(osv.Model):
    _name = 'hr.contract'
    _description = 'Contract'
    _inherit = 'hr.contract'

    _columns = {
        'alteracao_cargo_ids': fields.one2many('hr.contract_alteracao', 'contract_id', u'Alteração na informações do contrato', domain=[('tipo_alteracao', '=', 'C')]),
        'alteracao_remuneracao_ids': fields.one2many('hr.contract_alteracao', 'contract_id', u'Alterações na remuneração', domain=[('tipo_alteracao', '=', 'R')]),
        'alteracao_duracao_ids': fields.one2many('hr.contract_alteracao', 'contract_id', u'Alterações na duração', domain=[('tipo_alteracao', '=', 'D')]),
        'alteracao_jornada_ids': fields.one2many('hr.contract_alteracao', 'contract_id', u'Alterações na jornada', domain=[('tipo_alteracao', '=', 'J')]),
        'alteracao_sindicato_ids': fields.one2many('hr.contract_alteracao', 'contract_id', u'Alterações na filiação sindical', domain=[('tipo_alteracao', '=', 'S')]),
        'alteracao_alvara_ids': fields.one2many('hr.contract_alteracao', 'contract_id', u'Alterações no alvará judicial', domain=[('tipo_alteracao', '=', 'A')]),
        'alteracao_lotacao_ids': fields.one2many('hr.contract_alteracao', 'contract_id', u'Alterações no local de trabalho', domain=[('tipo_alteracao', '=', 'L')]),
    }


hr_contract()