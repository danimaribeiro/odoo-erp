# -*- coding: utf-8 -*-

from osv import fields, osv
from pybrasil.data import parse_datetime, agora, formata_data, data_hora_horario_brasilia
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta
from datetime import timedelta


GUARDA_HORAS = True
GUARDA_TEMPO = True

IMPACTA_FINANCEIRO = (
    ('0', u'0 - desconhecido'),
    ('1', u'1 - baixo; menos de R$ 5.000,00'),
    ('2', u'2 - médio; entre R$ 5.000,01 a R$ 10.0000,00'),
    ('3', u'3 - alto; acima de R$ 10.0000,00'),
)

IMPACTA_TENDENCIA = (
    ('1', u'1 - somente a atividade'),
    ('2', u'2 - todo o setor'),
    ('3', u'3 - toda a empresa'),
)

STATUS_PONTUACAO = (
    ('0.0', u'Novo'),
    #('0.0', u'0 - Novo'),
    #('0.1', u'0 - Cancelado'),
    #('0.2', u'0 - Concluído'),
    #('0.3', u'0 - Adiado'),
    #('1.1', u'1 - Em tempo'),
    #('2.1', u'2 - Andamento'),
    ('2.1', u'Andamento'),
    #('2.2', u'2 - Concluído para validação'),
    ('2.2', u'Concluído para validação'),
    #('2.3', u'2 - Aguardando informações'),
    ('2.3', u'Aguardando informações'),
    #('3.1', u'3 - Atrasado'),
)

URGENCIA_SUBJETIVA = (
    ('1.00', u'Baixa (possibilidade de espera de 12 horas)'),
    ('2.00', u'Média (possibilidade de espera de 6 horas)'),
    ('3.00', u'Alta (possibilidade de espera de 1 horas)'),
)

TIPO = (
    ('C', u'Chamado'),
    ('T', u'Tarefa'),
)

CAUSAS = (
    ('1', u'Configuração/permissão incorreta'),
    ('2', u'Falha/dúvida de operação do usuário'),
    ('3', u'Falha técnica/programação Integra'),
    ('4', u'Solicitação de melhoria/nova funcionalidade'),
    #('5', u'Dúvida na operação do usuário'),
)


class project_task(osv.osv):
    _name = "project.task"
    _inherit = "project.task"
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'descricao'
    _order = 'urgencia_subjetiva desc, pontuacao desc, create_date'
    _rec_name = 'descricao'

    def _get_gravidade(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for tarefa_obj in self.browse(cr, uid, ids):
            gravidade = 0
            gravidade += 1 if tarefa_obj.impacta_legislacao else 0
            gravidade += 1 if tarefa_obj.impacta_processo_decisorio else 0
            gravidade += 1 if tarefa_obj.impacta_processo_melhora else 0
            gravidade += 1 if tarefa_obj.impacta_processo_retrabalho else 0
            gravidade += int(tarefa_obj.impacta_financeiro) if tarefa_obj.impacta_financeiro else 0
            gravidade += int(tarefa_obj.impacta_abrangencia) if tarefa_obj.impacta_abrangencia else 0

            res[tarefa_obj.id] = gravidade

        return res

    def _get_pontuacao(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for tarefa_obj in self.browse(cr, uid, ids):
            pontuacao = 0

            if tarefa_obj.gravidade <= 4:
                pontuacao = 1
            elif tarefa_obj.gravidade <= 7:
                pontuacao = 2
            else:
                pontuacao = 3

            if tarefa_obj.impacta_status:
                pontuacao += int(tarefa_obj.impacta_status[0])

            res[tarefa_obj.id] = pontuacao

        return res

    def _get_urgencia(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for tarefa_obj in self.browse(cr, uid, ids):
            urgencia = u'Baixa'

            if tarefa_obj.pontuacao >= 3 and tarefa_obj.pontuacao <= 4:
                urgencia = u'Média'
            elif tarefa_obj.pontuacao >= 5:
                urgencia = u'Alta'

            res[tarefa_obj.id] = urgencia

        return res

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            res[obj.id] = obj.id

        return res

    def _descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            res[obj.id] = u'[' + str(obj.id).zfill(6) + '] ' + obj.name

        return res

    def _hours_get(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        #cr.execute("SELECT task_id, COALESCE(SUM(hours),0) FROM project_task_work WHERE task_id IN %s GROUP BY task_id",(tuple(ids),))
        #hours = dict(cr.fetchall())
        #for task in self.browse(cr, uid, ids, context=context):
            #res[task.id] = {'effective_hours': hours.get(task.id, 0.0), 'total_hours': (task.remaining_hours or 0.0) + hours.get(task.id, 0.0)}
            #res[task.id]['delay_hours'] = res[task.id]['total_hours'] - task.planned_hours
            #res[task.id]['progress'] = 0.0
            #if (task.remaining_hours + hours.get(task.id, 0.0)):
                #res[task.id]['progress'] = round(min(100.0 * hours.get(task.id, 0.0) / res[task.id]['total_hours'], 99.99),2)
            #if task.state in ('done','cancelled'):
                #res[task.id]['progress'] = 100.0
            #res[task.id] = 0
        res = {}
        for id in ids:
            res[id] = {}
            res[id]['total_hours'] = '0'
            res[id]['planned_hours'] = '0'
            res[id]['effective_hours'] = '0'
            res[id]['progress_rate'] = '0'

        return res

    def _tempo_atendimento(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for tarefa_obj in self.browse(cr, uid, ids):
            tempo = D(0)

            #
            # Se a Integra abre o chamado, o tempo de atendimento é imediato
            #
            if tarefa_obj.create_uid and tarefa_obj.create_uid.user_email and '@erpintegra.com.br' in tarefa_obj.create_uid.user_email:
                pass

            elif len(tarefa_obj.work_ids):
                tempo = tarefa_obj.work_ids[-1].horas_intervalo

                if nome_campo == 'tempo_gasto':
                    tempo = D(0)
                    for atividade_obj in tarefa_obj.work_ids:
                        tempo += atividade_obj.horas_gastas

            res[tarefa_obj.id] = tempo

        return res

    def texto_status(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        DIC_STATUS_PONTUACAO = dict(STATUS_PONTUACAO)
        DIC_STATUS_PONTUACAO[False] = ''

        for tarefa_obj in self.browse(cr, uid, ids):
            if nome_campo == 'texto_status':
                if tarefa_obj.impacta_status in DIC_STATUS_PONTUACAO:
                    res[tarefa_obj.id] = DIC_STATUS_PONTUACAO[tarefa_obj.impacta_status]
                else:
                    res[tarefa_obj.id] = ''
            else:
                if tarefa_obj.state == 'draft':
                    res[tarefa_obj.id] = u'Novo'
                elif tarefa_obj.state == 'open':
                    res[tarefa_obj.id] = u'Em andamento'
                elif tarefa_obj.state == 'done':
                    res[tarefa_obj.id] = u'Concluído'
                elif tarefa_obj.state == 'pending':
                    res[tarefa_obj.id] = u'Pendente'
                elif tarefa_obj.state == 'cancelled':
                    res[tarefa_obj.id] = u'Cancelado'
                else:
                    res[tarefa_obj.id] = u''

        return res

    _columns = {
        'unidade_id': fields.many2one('cliente.unidade', u'Empresa/unidade'),
        'tipo': fields.selection(TIPO, u'Tipo', required=True, select=True),
        'codigo': fields.function(_codigo, string=u'Código', method=True, type='integer', store=True),
        'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', store=True),
        'name': fields.char(u'Resumo', size=128, required=True, select=True),
        'solicitante': fields.char(u'Solicitante', size=30, required=True, select=True),
        'objetivo': fields.text(u'Objetivo'),
        'solucao': fields.text(u'Solução'),
        'processo_atual': fields.text(u'Processo atual'),
        'processo_novo': fields.text(u'Processo novo'),
        'parent_id': fields.many2one('project.task', u'Tarefa dependente', select=True, ondelete='restrict'),
        'parent_user_id': fields.related('parent_id', 'user_id', type='many2one', relation='res.users', string=u'Delegada por', select=True, ondelete='restrict', store=True),
        'dependencia_ids': fields.one2many('project.task', 'parent_id', string=u'Dependências'),
        'parent_left': fields.integer(u'Conta à esquerda', select=True),
        'parent_right': fields.integer(u'Conta a direita', select=True),
        'description': fields.text(u'Descrição'),

        #'phase_id': fields.many2one('project.phase', u'Subfase', select=True, ondelete='restrict'),
        #'phase_parent_id': fields.related('phase_id', 'parent_id', type='many2one', relation='project.phase', string=u'Fase', select=True, ondelete='restrict', store=True),
        'os_id': fields.many2one('project.os', 'Projeto OS'),

        'create_date': fields.datetime(u'Create Date', readonly=True,select=True),
        'create_uid': fields.many2one('res.users', u'Criado por',readonly=True),
        'write_date': fields.datetime(u'Última alteração', readonly=True,select=True),
        'write_uid': fields.many2one('res.users', u'Alterado por',readonly=True),

        'impacta_legislacao': fields.boolean(u'Impacta legislação?'),
        'impacta_processo_decisorio': fields.boolean(u'Impacta processo decisório/indicadores?'),
        'impacta_processo_melhora': fields.boolean(u'Melhora o processo em geral?'),
        'impacta_processo_retrabalho': fields.boolean(u'Diminui ou elimina retrabalho?'),
        'impacta_financeiro': fields.selection(IMPACTA_FINANCEIRO, u'Impacto financeiro'),
        'impacta_abrangencia': fields.selection(IMPACTA_TENDENCIA, u'Abrangência'),
        'impacta_status': fields.selection(STATUS_PONTUACAO, u'Status'),

        'gravidade': fields.function(_get_gravidade, type='integer', string=u'Gravidade', store=True),
        'pontuacao': fields.function(_get_pontuacao, type='integer', string=u'Pontuação', store=True, select=True),
        'urgencia': fields.function(_get_urgencia, type='char', string=u'Prioridade técnica', store=True, select=True),
        'resumo_trabalho': fields.char(u'Resumo trabalho', size=512),
        'urgencia_subjetiva': fields.selection(URGENCIA_SUBJETIVA, u'Prioridade usuário', select=True),
        'momento_ultimo_email': fields.datetime(u'Último email enviado'),
        'texto_status': fields.function(texto_status, type='char', string=u'Status', store=True, select=True),
        'texto_state': fields.function(texto_status, type='char', string=u'State', store=True, select=True),

        'effective_hours': fields.float(u'Horas totais'),
        'total_hours': fields.float(u'Horas totais'),
        'progress': fields.float(u'Progresso'),
        'delay_hours': fields.float(u'Horas restantes'),

        'causa_cliente': fields.selection(CAUSAS, u'Causa segundo o cliente', select=True),
        'causa_integra': fields.selection(CAUSAS, u'Causa segundo a Integra', select=True),

        'tempo_inicio_atendimento': fields.function(_tempo_atendimento, type='float', string=u'Iniciamos em', store=GUARDA_TEMPO),
        'tempo_gasto': fields.function(_tempo_atendimento, type='float', string=u'Horas consumidas', store=GUARDA_TEMPO),

        'data_liberacao': fields.datetime(u'Liberado em'),
        'liberacao_uid': fields.many2one('res.users', u'Liberado por'),
    }

    _defaults = {
        'tipo': 'C',
        'impacta_status': '0.0',
        'impacta_financeiro': '0',
        'impacta_abrangencia': '1',
        'user_id': False,
        'solicitante': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).name,
        'urgencia_subjetiva': '1.00',
    }

    def assunto_email(self, cr, uid, ids, context={}):
        tarefa_obj = self.pool.get('project.task').browse(cr, uid, ids[0])

        if tarefa_obj.tipo == 'C':
            texto = u'[CHAMADO'
        else:
            texto = u'[TAREFA'

        texto += u'-' + tarefa_obj.codigo + u'] - '

        if tarefa_obj.project_id:
            texto += tarefa_obj.project_id.name + ' - '

        if tarefa_obj.tipo == 'C':
            texto += u' Chamado alterado ' + tarefa_obj.name
        else:
            texto += u' Tarefa alterada ' + tarefa_obj.name

        return texto

    def do_open(self, cr, uid, ids, context={}):
        if not isinstance(ids,list):
            ids = [ids]

        self.inicia_cronometro(cr, uid, ids, context)

        return super(project_task, self).do_open(cr, uid, ids, context=context)

    def do_close(self, cr, uid, ids, context={}):
        if not isinstance(ids,list):
            ids = [ids]

        self.parar_cronometro(cr, uid, ids, context)

        return super(project_task, self).do_close(cr, uid, ids, context=context)

    def action_close(self, cr, uid, ids, context={}):
        if not isinstance(ids,list):
            ids = [ids]

        self.parar_cronometro(cr, uid, ids, context)

        return super(project_task, self).action_close(cr, uid, ids, context=context)

    def inicia_cronometro(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        work_pool = self.pool.get('project.task.work')

        for task_obj in self.browse(cr, uid, ids):

            user_id = uid
            task_id = task_obj.id

            if len(task_obj.work_ids) > 0 :

                work_ids = work_pool.search(cr, uid, [('task_id', '=', task_id),('data_final','=', False)])

                if len(work_ids) > 0:
                    raise osv.except_osv(u'Inválido!', u'Atividade em aberto, finalize!')
                else:
                    dados = {
                    'name': task_obj.resumo_trabalho or u'Reiniciado Tarefa',
                    'task_id': task_id,
                    'user_id': user_id,
                    }

                    work_pool.create(cr, uid, dados)

            else:
                dados = {
                    'name': u'Iniciada Tarefa',
                    'task_id': task_id,
                    'user_id': user_id,
                }
                work_pool.create(cr, uid, dados)
            task_obj.write({'resumo_trabalho': ''})

        return

    def parar_cronometro(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for task_obj in self.browse(cr, uid, ids):
            if len(task_obj.work_ids) > 0 :
                for work_obj in task_obj.work_ids:
                    if not work_obj.data_final:
                        data_inicial = parse_datetime(work_obj.data_inicial)
                        data_final = parse_datetime(fields.datetime.now())

                        hora = data_final - data_inicial

                        hora_att = hora.days * 24.00
                        hora_att += hora.seconds / 60.00 / 60.00

                        dados = {
                            'hours': hora_att,
                            'data_final': data_final,
                        }
                        work_obj.write(dados)

        return

    def enviar_email(self, cr, uid, ids, tipo, context={}):
        tarefa_pool = self.pool.get('project.task')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid)
        mail_pool = self.pool.get('mail.message')
        attachment_pool = self.pool.get('ir.attachment')

        for tarefa_obj in tarefa_pool.browse(cr, uid, ids, context=context):
            print(tarefa_obj.state, tarefa_obj.momento_ultimo_email)

            if tarefa_obj.momento_ultimo_email:
                momento_ultimo_email = parse_datetime(tarefa_obj.momento_ultimo_email)
                momento_agora = parse_datetime(fields.datetime.now())
                tempo = momento_agora - momento_ultimo_email

                print('tempo')
                print(tempo, tempo.seconds / 60.0)

                if tempo.seconds / 60.0 < 5:
                    continue

            dados = {
                'model': 'project.task',
                'res_id': tarefa_obj.id,
                'user_id': uid,
                'email_to': tarefa_obj.create_uid.name + u' <' + (tarefa_obj.create_uid.user_email or '') + u'>',
                'email_from': 'Atendimento Integra <suporteerp@erpintegra.com.br>',
                'date': str(fields.datetime.now()),
                'headers': '{}',
                'email_cc': u'Atendimento Integra <suporteerp@erpintegra.com.br>',
                'reply_to': u'Atendimento Integra <suporteerp@erpintegra.com.br>',
                'state': 'outgoing',
                'message_id': False,
            }


            try:
                if tarefa_obj.write_uid and tarefa_obj.write_uid.id != tarefa_obj.create_uid.id and tarefa_obj.write_uid.user_email and tarefa_obj.write_uid.user_email not in dados['email_cc']:
                    dados['email_cc'] += u', ' + tarefa_obj.write_uid.name + u' <' + tarefa_obj.write_uid.user_email + u'>'
            except:
                pass

            try:
                if tarefa_obj.user_id and tarefa_obj.user_id.user_email and tarefa_obj.user_id.user_email not in dados['email_cc']:
                    dados['email_cc'] += u', ' + tarefa_obj.user_id.name + u' <' + tarefa_obj.user_id.user_email + u'>'
            except:
                pass

            try:
                if tipo == 'I' and tarefa_obj.project_id and tarefa_obj.project_id.user_id and tarefa_obj.project_id.user_id.user_email and tarefa_obj.project_id.user_id.user_email not in dados['email_cc']:
                    dados['email_cc'] += u', ' + tarefa_obj.project_id.user_id.name + u' <' + tarefa_obj.project_id.user_id.user_email + u'>'

                #if 'patrimonialseguranca' in dados['email_cc'] and 'juciel.cunico@patrimonialseguranca' not in dados['email_cc']:
                    #dados['email_cc'] += u' , Juciel Cunico <juciel.cunico@patrimonialseguranca.com.br> '

            except:
                pass

            if dados['email_cc'][0:2] == ', ':
                dados['email_cc'] = dados['email_cc'][2:]

            assunto = u'['

            if tarefa_obj.tipo == 'C':
                assunto += u'CHAMADO-'
            else:
                assunto += u'TAREFA-'

            assunto += str(tarefa_obj.id).zfill(6)
            assunto += u'] '

            if tarefa_obj.project_id:
                assunto += tarefa_obj.project_id.name + ' - '

            if tarefa_obj.tipo == 'C':
                assunto += u'Chamado '
            else:
                assunto += u'Tarefa '

            assunto += tarefa_obj.name

            if tipo == 'I':
                if tarefa_obj.tipo == 'C':
                    corpo = u'''
Olá!

Você está recebendo este email pois ocorreu a abertura de um novo chamado no
sistema de atendimento Integra.

Protocolo: {protocolo}
Título: {titulo}
Usuário: {usuario}
Data: {data}


Atenciosamente,
--
Atendimento Integra
'''
                else:
                    corpo = u'''
Olá!

Você está recebendo este email pois ocorreu a abertura de uma nova tarefa no
sistema de atendimento Integra.

Protocolo: {protocolo}
Título: {titulo}
Usuário: {usuario}
Data: {data}


Atenciosamente,
--
Atendimento Integra
'''
            elif tipo == 'A':
                if tarefa_obj.tipo == 'C':
                    corpo = u'''
Olá!

Você está recebendo este email pois ocorreu uma alteração num chamado no
sistema de atendimento Integra.

Protocolo: {protocolo}
Título: {titulo}
Usuário: {usuario}
Data: {data}

Atenciosamente,
--
Atendimento Integra
'''
                else:
                    corpo = u'''
Olá!

Você está recebendo este email pois ocorreu uma alteração numa tarefa no
sistema de atendimento Integra.

Protocolo: {protocolo}
Título: {titulo}
Usuário: {usuario}
Data: {data}


Atenciosamente,
--
Atendimento Integra
'''

            filtro = {
                'protocolo': str(tarefa_obj.id).zfill(6),
                'titulo': tarefa_obj.name,
                'data': formata_data(agora(), '%d/%m/%Y %H:%M:%S')
            }

            if tipo == 'I':
                filtro['usuario'] = tarefa_obj.create_uid.name
            else:
                filtro['usuario'] = tarefa_obj.write_uid.name

            dados['body_text'] = corpo.format(**filtro)
            dados['subject'] = assunto

            mail_id = mail_pool.create(cr, uid, dados)
            sql = "update project_task set momento_ultimo_email = '" + fields.datetime.now() + "' where id = " + str(tarefa_obj.id) + ";"
            print(sql)
            cr.execute(sql)
            cr.commit()

            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'project.task'), ('res_id', '=', tarefa_obj.id)])
            if len(attachment_ids):
                anexos = []
                for attachment_id in attachment_ids:
                    anexos.append((4, attachment_id))
                mail_pool.write(cr, uid, mail_id, {'attachment_ids': anexos})

            mail_pool.process_email_queue(cr, uid, [mail_id])

        return {'value': {}, 'warning': {'title': u'Confirmação', 'message': u'Email enviado para os usuários!'}}

    def create(self, cr, uid, dados, context={}):
        res = super(osv.Model, self).create(cr, uid, dados, context=context)

        tarefa_pool = self.pool.get('project.task')
        tarefa_pool.enviar_email(cr, uid, [res], 'I', context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        tarefa_pool = self.pool.get('project.task')
        usuario_pool = self.pool.get('res.users')
        usuario_obj = usuario_pool.browse(cr, uid, uid)

        #
        # Somente o admin pode alterar qq coisa numa tarefa/chamado fechado
        #
        if uid != 1:
            for tarefa_obj in tarefa_pool.browse(cr, uid, ids):
                #
                # A tarefa está fechada ou cancelada, e o usuário está tentando
                # classificar a causa do chamado
                #
                if tarefa_obj.state in ('done', 'cancelled'):
                    if '@erpintegra' not in usuario_obj.user_email:
                        if tarefa_obj.causa_cliente or len(dados) > 1 or 'causa_cliente' not in dados:
                            if tarefa_obj.tipo == 'C':
                                raise osv.except_osv(u'Inválido!', u'Chamados fechados ou cancelados não podem ser alterados!')
                            else:
                                raise osv.except_osv(u'Inválido!', u'Tarefas fechadas ou canceladas não podem ser alteradas!')

        print(dados)

        res = super(osv.Model, self).write(cr, uid, ids, dados, context=context)

        tarefa_pool.enviar_email(cr, uid, ids, 'A', context)

        return res

    def libera_chamado_patrimonial(self, cr, uid, ids, context={}):
        project_pool = self.pool.get('project.project')
        project_ids = project_pool.search(cr, uid, [('nome_completo', 'ilike', 'PATRIMONIAL')])

        #
        # Verifica se há chamados liberados ainda não concluído, e limita a liberação
        #
        task_pool = self.pool.get('project.task')
        task_ids = task_pool.search(cr, uid, [('project_id', 'in', project_ids), ('data_liberacao', '!=', False), ('state', '!=', 'done')])

        if len(task_ids) > 5:
            raise osv.except_osv(u'Inválido!', u'Máximo de chamados em execução excedido!')

        return task_pool.write(cr, uid, ids, {'data_liberacao': fields.datetime.now(), 'liberacao_uid': uid})


project_task()


class project_work(osv.osv):
    _name = 'project.task.work'
    _inherit = 'project.task.work'
    _order = 'task_id, data_final desc, data_inicial desc'

    def _calcula_horas(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for atividade_obj in self.browse(cr, uid, ids, context=context):
            horas = 0
            intervalo = timedelta(days=0, seconds=0)

            if nome_campo == 'horas_gastas':
                data_inicial = data_hora_horario_brasilia(parse_datetime(atividade_obj.data_inicial + ' UTC'))

                if atividade_obj.data_final:
                    data_final = data_hora_horario_brasilia(parse_datetime(atividade_obj.data_final + ' UTC'))
                else:
                    data_final = agora()

                intervalo = data_final - data_inicial

                #
                # Atividades da Integra tem um tempo gasto de pelo menos 15 minutos
                #
                if atividade_obj.user_id and atividade_obj.user_id.user_email and '@erpintegra.com.br' in atividade_obj.user_id.user_email:
                    if intervalo.days == 0 and intervalo.seconds < 900:
                        intervalo = timedelta(days=0, seconds=900)

            else:
                data_inicial = data_hora_horario_brasilia(parse_datetime(atividade_obj.data_inicial + ' UTC'))

                anterior_ids = self.search(cr, uid, [('task_id', '=', atividade_obj.task_id.id), ('data_final', '!=', False), ('data_final', '<=', atividade_obj.data_inicial)])

                if len(anterior_ids):
                    atividade_anterior_obj = self.browse(cr, uid, anterior_ids[0])
                    data_final = data_hora_horario_brasilia(parse_datetime(atividade_anterior_obj.data_final + ' UTC'))

                else:
                    data_final = data_hora_horario_brasilia(parse_datetime(atividade_obj.task_id.create_date + ' UTC'))


                #if data_inicial > data_final:
                    #intervalo = horas_uteis(data_final, data_inicial)
                #print(data_final, data_inicial, 'intervalo', intervalo)

            horas = D(intervalo.days * 24)
            horas += D(intervalo.seconds) / D(60) / D(60)

            res[atividade_obj.id] = horas

        return res

    _columns = {
        'name': fields.char(u'Resumo da atividade', size=512),
        'data_inicial': fields.datetime(u'Hora inicial'),
        'data_final': fields.datetime(u'Hora final'),
        'horas_gastas': fields.function(_calcula_horas, type='float', string=u'Horas consumidas', store=GUARDA_HORAS),
        'horas_intervalo': fields.function(_calcula_horas, type='float', string=u'Horas intervalo', store=GUARDA_HORAS),
        }

    _defaults = {
            'data_inicial': fields.datetime.now,
    }



project_work()

