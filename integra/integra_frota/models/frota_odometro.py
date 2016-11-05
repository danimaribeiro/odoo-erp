# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from datetime import datetime
from osv import osv, fields
from pybrasil.data import parse_datetime, formata_data, data_hora_horario_brasilia, UTC
from pybrasil.valor.decimal import Decimal as D


class frota_odometro(osv.Model):
    _name = 'frota.odometro'
    _description = u'Registros de odômetro'
    _order = "data at time zone 'UTC' at time zone 'America/Sao_Paulo' desc"
    _rec_name = 'nome_completo'

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            nome = obj.veiculo_id.nome

            if obj.data:
                nome = nome + ' - ' + str(obj.data)

            res[obj.id] = nome

        return res

    def _get_dia(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = obj.data[:10]

        return res

    _columns = {
        'nome': fields.function(_get_nome_funcao, type='char', string='Nome', store=True),
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo', required=True),
        'company_id': fields.related('veiculo_id', 'res_company_id', type='many2one', relation='res.company', string=u'Empresa', store=True, select=True),
        'data': fields.datetime(u'Data da abertura', required=True),
        'servico_id': fields.many2one('frota.servico', u'Serviço/atividade'),
        'hr_employee_id': fields.many2one('hr.employee', u'Empregado/motorista'),
        'motorista_terceiro': fields.char(u'Motorista terceiro', size=30),
        'hr_department_id': fields.many2one('hr.department', u'Departamento/setor/posto'),
        'valor_atual': fields.float(u'km atual'),
        'valor_anterior': fields.float(u'km anterior'),
        'distancia': fields.float(u'Distância'),
        'os_id': fields.many2one('frota.os', 'OS'),
        'state': fields.selection([['A', u'Aberto'], ['F', u'Fechado']], string=u'Situação'),
        'dia': fields.function(_get_dia, type='date', string='Dia', store=True),
        'data_fechamento': fields.datetime(u'Data de fechamento'),
        'justificativa': fields.char(u'Justificativa', size=512),

        'cliente_id': fields.many2one('res.partner', u'Cliente'),
        'finan_contrato_id': fields.many2one('finan.contrato', u'Contrato/instalação'),
    }

    _defaults = {
        'data': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'state': 'A',
    }

    def search_odometro(self, cr, uid, ids, veiculo_id, data, context={}):
        valores = {}
        retorno = {'value': valores}

        data = parse_datetime(data)
        data = UTC.normalize(data)
        data = data_hora_horario_brasilia(data)

        sql = u"""
        select
            cast(coalesce(fo.valor_atual, 0) as numeric(18,2))

        from frota_odometro fo
        join frota_veiculo fv on fv.id = fo.veiculo_id

        where
            fo.data at time zone 'UTC' at time zone 'America/Sao_Paulo' < '{data}' and
            fv.id = {veiculo_id}

        order by
            fo.data at time zone 'America/Sao_Paulo' desc
        limit 1;
        """

        if veiculo_id:
            print(sql.format(data=data, veiculo_id=veiculo_id))
            cr.execute(sql.format(data=data, veiculo_id=veiculo_id))

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

    def atualiza_distancia(self, cr, ids):
        if isinstance(ids, (int, long)):
            ids = [int(ids)]

        ids = str(ids).replace('[', '(').replace(']', ')')

        cr.execute('update frota_odometro set distancia = coalesce(valor_atual, 0) - coalesce(valor_anterior, 0) where id in ' + ids + ';')
        cr.execute('update frota_veiculo v set odometro = coalesce((select max(o.valor_atual) from frota_odometro o where o.veiculo_id = v.id), 0);')

    def write(self, cr, uid, ids, dados, context={}):
        if isinstance(ids, (list, tuple)):
            od_obj = self.browse(cr, uid, ids[0])
        else:
            od_obj = self.browse(cr, uid, ids)

        valor_anterior = 0
        if 'valor_anterior' in dados:
            valor_anterior = D(dados['valor_anterior'] or 0)
        else:
            valor_anterior = D(od_obj.valor_anterior or 0)

        valor_atual = 0
        if 'valor_atual' in dados:
            valor_atual = D(dados['valor_atual'] or 0)
        else:
            valor_atual = D(od_obj.valor_atual or 0)

        if valor_atual < valor_anterior:
            raise osv.except_osv(u'Erro!', u'Quilometragem atual menor do que a anterior!')

        res = super(frota_odometro, self).write(cr, uid, ids, dados, context)

        self.atualiza_distancia(cr, ids)

        return res

    def create(self, cr, uid, dados, context={}):
        if 'valor_atual' in dados and 'valor_anterior' in dados:
            valor_anterior = D(dados['valor_anterior'] or 0)
            valor_atual = D(dados['valor_atual'] or 0)
            if valor_atual < valor_anterior:
                raise osv.except_osv(u'Erro!', u'Quilometragem atual menor do que a anterior!')

        #
        # Não deixa lançar odômetro desvinculado de OS se outro
        # odômetro estiver em aberto
        #
        if not 'os_id' in dados:
            abertos = self.search(cr, uid, [['veiculo_id', '=', dados['veiculo_id']], ['state', '=', 'A'], ['os_id', '=', False]])
            if len(abertos) >= 1:
                raise osv.except_osv(u'Erro!', u'Ainda há um registro de odômetro aberto para o veículo!')

        res = super(frota_odometro, self).create(cr, uid, dados, context)

        self.atualiza_distancia(cr, res)

        return res

    def fecha_odometro(self, cr, uid, ids, context={}):
        if not ids:
            return

        for os_obj in self.browse(cr, uid, ids):
            if not os_obj.valor_anterior:
                raise osv.except_osv(u'Erro!', u'Não é permitido fechar sem o preenchimento da quilometragem anterior!')

            if not os_obj.valor_atual:
                raise osv.except_osv(u'Erro!', u'Não é permitido fechar sem o preenchimento da quilometragem atual!')

            ##
            ## Acima de 200 km de distância, somente gerentes para fechar o
            ## odômetro
            ##
            #if os_obj.distancia > 200:
                #usuario_obj = self.pool.get('res.users').browse(cr, 1, uid)
                #pode_fechar = False
                #for grupo_obj in usuario_obj.groups_id:
                    #if grupo_obj.name == 'Integra / Gerente de Frota':
                        #pode_fechar = True

                #if not pode_fechar:
                    #raise osv.except_osv(u'Erro!', u'Você não tem permissão de fechar esse registro, pois a quilometragem é maior do que 200 km!')

                #if not os_obj.justificativa:
                    #raise osv.except_osv(u'Erro!', u'Você não pode fechar esse registro sem justificativa!')

            if not os_obj.data_fechamento:
                raise osv.except_osv(u'Erro!', u'Você não pode fechar esse registro sem preencher a data de fechamento!')

        return self.write(cr, uid, ids, {'state': 'F'})

    def abre_odometro(self, cr, uid, ids, context={}):
        if not ids:
            return

        return self.write(cr, uid, ids, {'state': 'A'})

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


frota_odometro()
