# -*- coding: utf-8 -*-

from osv import osv, fields
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)
from integra_rh.models.hr_employee import SEXO, ESTADO_CIVIL, ESTADO_CIVIL_SEXO
from pybrasil.valor.decimal import Decimal as D



class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _estatistica_financeira(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for id in ids:
            sql = """
            select
                count(l.sped_documento_id) as notas,
                sum(coalesce(case when l.sped_documento_id is null then 0 else l.valor_documento end, 0)) as vr_notas,

                count(*) as titulos,
                sum(coalesce(l.valor_documento, 0)) as vr_titulos,

                max(coalesce(l.data_quitacao, current_date) - l.data_vencimento) as maior_atraso,

                sum(coalesce(case when (l.situacao = 'A vencer' or l.situacao = 'Vence hoje') then 1 else 0 end, 0)) as a_vencer,
                sum(coalesce(case when l.situacao = 'A vencer' or l.situacao = 'Vence hoje' then l.valor_documento else 0 end, 0)) as vr_a_vencer,

                sum(coalesce(case when (l.situacao = 'Vencido') then 1 else 0 end, 0)) as vencidos,
                sum(coalesce(case when l.situacao = 'Vencido' then l.valor_documento else 0 end, 0)) as vr_vencido,

                sum(coalesce(case when (l.situacao = 'Quitado' or l.situacao = 'Quitado parcial') then 1 else 0 end, 0)) as quitados,
                sum(coalesce(case when (l.situacao = 'Quitado' or l.situacao = 'Quitado parcial') and l.data_quitacao > l.data_vencimento then 1 else 0 end, 0)) as quitados_atraso

            from
                finan_lancamento l

            where
                l.tipo = 'R'
                and (l.provisionado is null or l.provisionado = False)
                and l.partner_id = {partner_id};
            """
            sql = sql.format(partner_id=id)
            cr.execute(sql)
            dados = cr.fetchall()

            res[id] = {
                'qtd_notas': 0,
                'vr_notas': D(0),
                'qtd_titulos': 0,
                'vr_titulos': 0,
                'maior_atraso': 0,
                'qtd_a_vencer': 0,
                'vr_a_vencer': D(0),
                'qtd_vencidos': 0,
                'vr_vencidos': D(0),
                'qtd_quitados': 0,
                'qtd_quitados_em_dia': 0,
                'qtd_quitados_em_atraso': 0,
                'porcentagem_pago_em_dia': D(0),
                'porcentagem_pago_em_atraso': D(0),
                'cheques_devolvidos': D(0),
                'cheques_devolvidos_mais_vencidos': D(0),
            }

            if len(dados) > 0:
                qtd_notas, vr_notas, qtd_titulos, vr_titulos, maior_atraso, qtd_a_vencer, vr_a_vencer, qtd_vencidos, vr_vencido, qtd_quitados, qtd_quitados_atraso = dados[0]

                res[id]['qtd_notas'] = qtd_notas
                res[id]['vr_notas'] = vr_notas
                res[id]['qtd_titulos'] = qtd_titulos
                res[id]['vr_titulos'] = vr_titulos
                res[id]['maior_atraso'] = maior_atraso
                res[id]['qtd_a_vencer'] = qtd_a_vencer
                res[id]['vr_a_vencer'] = vr_a_vencer
                res[id]['qtd_vencidos'] = qtd_vencidos
                res[id]['vr_vencidos'] = vr_vencido
                res[id]['qtd_quitados'] = qtd_quitados
                res[id]['qtd_quitados_em_dia'] = D(qtd_quitados or 0) - D(qtd_quitados_atraso or 0)
                res[id]['qtd_quitados_em_atraso'] = qtd_quitados_atraso
                #res[id]['porcentagem_pago_em_dia'] = D(0)
                #res[id]['porcentagem_pago_em_atraso'] = D(0)

                if qtd_quitados:
                    qtd_dia = D(qtd_quitados or 0) - D(qtd_quitados_atraso or 0)
                    res[id]['porcentagem_pago_em_dia'] = qtd_dia / D(qtd_quitados or 1) * 100
                    res[id]['porcentagem_pago_em_atraso'] = D(qtd_quitados_atraso or 0) / D(qtd_quitados or 1) * 100

                elif qtd_quitados_atraso:
                    res[id]['porcentagem_pago_em_dia'] = 0
                    res[id]['porcentagem_pago_em_atraso'] = 100

            sql = """
            select
                sum(coalesce(c.valor, 0)) as cheques_devolvidos

            from
                finan_cheque c

            where
                c.partner_id = {partner_id}
                and c.situacao = 'DF';
            """
            sql = sql.format(partner_id=id)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados):
                res[id]['cheques_devolvidos'] = D(dados[0][0] or 0)
                res[id]['cheques_devolvidos_mais_vencidos'] = D(dados[0][0] or 0) + D(res[id]['vr_vencidos'] or 0)

        return res

    def _qtd_contratos(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for id in ids:
            sql = """
            select
                coalesce(count(c.*), 0) as qtd_contratos

            from
                finan_contrato c

            where
                c.natureza = 'R'
                and c.ativo = True
                and c.partner_id = {id};
            """
            sql = sql.format(id=id)
            cr.execute(sql)

            dados = cr.fetchall()

            res[id] = False

            if len(dados):
                res[id] = dados[0][0]

        return res

    def _search_qtd_contratos(self, cr, uid, partner_pool, texto, args, context={}):
        print(args[0])

        if args[0][1] == '=' and (args[0][2] == False or args[0][2] == 0):
            sql = """
            select
                p.id,
                c.id

            from
                res_partner p
                left join finan_contrato c on c.partner_id = p.id

            where
                c.id is null;
            """

        else:
            sql = """
            select
                p.id,
                count(*)

            from
                res_partner p
                join finan_contrato c on c.partner_id = p.id

            where
                c.natureza = 'R'
                and c.ativo = True

            group by
                p.id

            having
                count(*) {argumento} {qtd};
            """
            sql = sql.format(qtd=args[0][2], argumento=args[0][1])

        cr.execute(sql)
        dados = cr.fetchall()

        res = []

        partner_ids = []
        for partner_id, qtd in dados:
            partner_ids.append(partner_id)

        if len(partner_ids):
            res = [('id', 'in', partner_ids)]

        return res

    _columns = {
        'fone_comercial': fields.char(u'Fone Comercial', size=18),
        'eh_contato': fields.boolean(u'É contato'),
        'data_nascimento': fields.date(u'Data de nascimento'),
        'latitude': fields.float(u'Latitude', digits=(21, 10)),
        'longitude': fields.float(u'Longitude', digits=(21, 10)),

        'lancamento_receber_ids': fields.one2many('finan.lancamento', 'partner_id', u'Contas a receber', domain=[('tipo', '=', 'R'), ('provisionado', '=', False)]),
        'cheque_ids': fields.one2many('finan.cheque', 'partner_id', u'Cheques recebidos'),
        'contrato_ids': fields.one2many('finan.contrato', 'partner_id', u'Contratos', domain=[('ativo', '=', True), ('natureza', '=', 'R')]),
        'qtd_contratos': fields.function(_qtd_contratos, type='integer', string=u'Qtd. contratos', fnct_search=_search_qtd_contratos),

        'qtd_notas': fields.function(_estatistica_financeira, type='integer', string=u'Qtd. notas', multi='sums', store=False),
        'vr_notas': fields.function(_estatistica_financeira, type='float', digits=(18, 2), string=u'Vr. notas', multi='sums', store=False),
        'qtd_titulos': fields.function(_estatistica_financeira, type='integer', string=u'Qtd. títulos', multi='sums', store=False),
        'vr_titulos': fields.function(_estatistica_financeira, type='float', digits=(18, 2), string=u'Vr. títulos', multi='sums', store=False),
        'maior_atraso': fields.function(_estatistica_financeira, type='integer', string=u'Maior atraso', multi='sums', store=False),
        'qtd_a_vencer': fields.function(_estatistica_financeira, type='integer', string=u'Qtd. a vencer', multi='sums', store=False),
        'vr_a_vencer': fields.function(_estatistica_financeira, type='float', digits=(18, 2), string=u'Vr. a vencer', multi='sums', store=False),
        'qtd_vencidos': fields.function(_estatistica_financeira, type='integer', string=u'Qtd. vencidos', multi='sums', store=False),
        'vr_vencidos': fields.function(_estatistica_financeira, type='float', digits=(18, 2), string=u'Vr.vencidos', multi='sums', store=False),
        'qtd_quitados': fields.function(_estatistica_financeira, type='integer', string=u'Qtd. quitados', multi='sums', store=False),
        'qtd_quitados_em_dia': fields.function(_estatistica_financeira, type='integer', string=u'Qtd. quitados em dia', multi='sums', store=False),
        'qtd_quitados_em_atraso': fields.function(_estatistica_financeira, type='integer', string=u'Qtd. quitados em atraso', multi='sums', store=False),
        'porcentagem_pago_em_dia': fields.function(_estatistica_financeira, type='float', digits=(18, 2), string=u'% pago em dia', multi='sums', store=False),
        'porcentagem_pago_em_atraso': fields.function(_estatistica_financeira, type='float', digits=(18, 2), string=u'% pago em atraso', multi='sums', store=False),
        'cheques_devolvidos': fields.function(_estatistica_financeira, type='float', digits=(18, 2), string=u'Vr. devolvidos', multi='sums', store=False),
        'cheques_devolvidos_mais_vencidos': fields.function(_estatistica_financeira, type='float', digits=(18, 2), string=u'Vr. devolvidos + vencidos', multi='sums', store=False),
    }

    def onchange_cpf(self, cr, uid, ids, cpf, context={}):
        if not cpf:
            return {}

        if not valida_cpf(cpf):
            raise osv.except_osv(u'Erro!', u'CPF inválido!')

        cpf = limpa_formatacao(cpf)
        cpf = formata_cpf(cpf)

        if ids != []:
            cnpj_ids = self.pool.get('hr.employee').search(cr, uid, [('cpf', '=', cpf), '!', ('id', 'in', ids)])
        else:
            cnpj_ids = self.pool.get('hr.employee').search(cr, uid, [('cpf', '=', cpf)])

        if len(cnpj_ids) > 0:
            return {'value': {'cpf': cpf}, 'warning': {'title': u'Aviso!', 'message': u'CPF já existe no cadastro!'}}

        return {'value': {'cpf': cpf}}

    def onchange_fone_celular(self, cr, uid, ids, fone, celular, context={}):
        if fone is not None and fone:
            if not valida_fone_internacional(fone) and not valida_fone_fixo(fone):
                return {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Telefone fixo inválido!'}}

            fone = formata_fone(fone)
            return {'value': {'fone': fone}}

        elif celular is not None and celular:
            if not valida_fone_internacional(celular) and not valida_fone_celular(celular):
                return {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Celular inválido!'}}

            celular = formata_fone(celular)
            return {'value': {'celular': celular}}

    def onchange_cep_id(self, cr, uid, ids, cep_id):
        cep_pool = self.pool.get('res.cep')

        valores = cep_pool.onchange_consulta_cep(cr, uid, False, cep_id)

        return {'value': valores}

    def abre_google_maps(self, cr, uid, ids, context={}):
        partner_obj = self.pool.get('res.partner').browse(cr, uid, ids[0], context=context)

        url = u'http://maps.google.com/maps?oi=map&q='

        if partner_obj.endereco:
            url += partner_obj.endereco

        if partner_obj.numero:
            url += ', ' + partner_obj.numero

        if partner_obj.bairro:
            url += ', ' + partner_obj.bairro

        if partner_obj.cidade:
            url += ', ' + partner_obj.cidade

        if partner_obj.estado:
            url += ', ' + partner_obj.estado

        if partner_obj.cep:
            url += ', ' + partner_obj.cep

        url = url.replace(u' ', u'+')

        res = {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }

        return res


    def importa_inside_service(self, cr, uid, ids, context={}):
        COMPANY_FATURA = ('1', '130')

        arq = open('/home/monital/clientes.csv', 'r')
        rej = open('/home/monital/rejeitados.csv', 'w')
        partner_pool = self.pool.get('res.partner')
        address_pool = self.pool.get('res.partner.address')
        municipio_pool = self.pool.get('sped.municipio')
        company_pool = self.pool.get('res.company')
        contrato_pool = self.pool.get('finan.contrato')
        produto_pool = self.pool.get('finan.contrato_produto')

        for linha in arq.readlines():
            linha_original = linha
            linha = linha.replace('\n', '').replace('\r', '')
            print(linha)
            codigo, nome, razao_social, fantasia, cnpj_cpf, contribuinte, ie, im, endereco, numero, complemento, bairro, cidade, estado, cep, fone, email, email_nfe, dia_vencimento, valor_mensal, data_contrato, data_inicio, company_id, latitude, longitude, cancelamento = linha.split(';')

            #
            # Validamos o CPF/CNPJ
            #
            #if not cnpj_cpf:
                #rej.write('cnpj;' + linha_original)
                #continue

            #if not valida_cpf(cnpj_cpf) and not valida_cnpj(cnpj_cpf):
                #rej.write('cnpj;' + linha_original)
                #continue

            if valida_cpf(cnpj_cpf):
                cnpj_cpf = formata_cpf(cnpj_cpf)
            elif valida_cnpj(cnpj_cpf):
                cnpj_cpf = formata_cnpj(cnpj_cpf)
            else:
                cnpj_cpf = ''

            #
            # Validamos o CEP
            #
            cep = limpa_formatacao(cep)
            if not cep.isdigit() or len(cep) != 8:
                #rej.write('cep;' + linha_original)
                #continue
                cep = ''
            else:
                cep = cep[:5] + '-' + cep[5:]

            #
            # Validamos o município
            #
            sql = """
            select
                m.id
            from
                sped_municipio m
            where
                lower(unaccent(m.nome)) = lower(unaccent('{nome}'))
                and lower(unaccent(m.estado)) = lower(unaccent('{estado}'));
            """
            cr.execute(sql.format(nome=cidade, estado=estado))
            municipio_ids = cr.fetchall()

            if not municipio_ids:
                municipio_id = False
                #rej.write('municipio;' + linha_original)
                #continue
            else:
                municipio_id = municipio_ids[0][0]

            dados = {
                'ref': codigo,
                'name': nome,
                'razao_social': razao_social,
                'fantasia': fantasia,
                'cnpj_cpf': cnpj_cpf,
                'contribuinte': contribuinte,
                'im': im,
                'endereco': endereco.replace("'", "''"),
                'numero': numero,
                'complemento': complemento,
                'bairro': bairro.replace("'", "''"),
                'cep': cep,
                'email': email,
                'email_nfe': email_nfe,
                'municipio_id': municipio_id,
                #'company_id': int(company_id),
                'latitude': D(latitude or 0),
                'longitude': D(longitude or 0),
            }

            #
            # Validamos o fone
            #
            if valida_fone_fixo(fone):
                dados['fone'] = formata_fone(fone)
            elif valida_fone_celular(fone):
                dados['celular'] = formata_fone(fone)

            if cnpj_cpf:
                partner_ids = partner_pool.search(cr, uid, [('cnpj_cpf', '=', cnpj_cpf)])
            else:
                partner_ids = partner_pool.search(cr, uid, [('name', '=', nome)])

            if partner_ids:
                partner_id = partner_ids[0]
            else:
                partner_id = partner_pool.create(cr, uid, dados)

            dados_ie = {}
            if contribuinte == '2':
                if valida_inscricao_estadual(unicode(ie), estado):
                    dados_ie['ie'] = formata_inscricao_estadual(unicode(ie), estado)
                    dados_ie['contribuinte'] = '1'
                else:
                    dados_ie['contribuinte'] = '2'
            else:
                dados_ie['contribuinte'] = '2'

            partner_pool.write(cr, uid, [partner_id], dados_ie)

            dados['partner_id'] = partner_id
            dados['company_id'] = False

            address_ids = address_pool.search(cr, uid, [('partner_id', '=', partner_id), ('endereco', '=', endereco)])

            if address_ids:
                address_id = address_ids[0]
            else:
                address_id = address_pool.create(cr, uid, dados)

            cr.commit()

            if dia_vencimento == '0' or dia_vencimento == '31':
                dia_vencimento = '30'

            if company_id != 'NULL' and data_contrato.upper().strip() != 'NULL':
                #
                # Agora que temos o cliente e o endereço, vamos colocar o contrato
                #

                if company_id == '1001':
                    company_id = '136'
                elif company_id == '2':
                    company_id = '1'
                elif company_id == '1002':
                    company_id = '137'
                elif company_id == '3':
                    company_id = '134'
                elif company_id == '1003':
                    company_id = '135'
                elif company_id == '4':
                    #company_id = '135'
                    continue
                elif company_id == '1004':
                    #company_id = '135'
                    continue
                elif company_id == '5':
                    company_id = '133'
                elif company_id == '1005':
                    company_id = '137'

                dados = {
                    'company_id': int(company_id),
                    'partner_id': partner_id,
                    'res_partner_address_id': address_id,
                    'valor_mensal': D(valor_mensal),
                    'data_assinatura': data_contrato,
                    'data_inicio': data_contrato,
                    'dia_vencimento': dia_vencimento,
                    'numero': '2016-' + codigo.zfill(4),
                    'duracao': 24,
                    'conta_id': 2243,  # conta 3.01.01 - receita com monitoramento
                    'formapagamento_id': 1,  # Cobrança bancária
                    'documento_id': 11,  # NFS-e
                }

                if company_id not in COMPANY_FATURA:
                    dados['documento_id'] = 75  # Boleto somente, não NF

                ##
                ## Prottege
                ##
                #elif company_id == '1':
                    #dados['operacao_fiscal_servico_id'] = 328

                ##
                ## ProttSeg
                ##
                #elif company_id == '130':
                    #dados['operacao_fiscal_servico_id'] = 329

                ##
                ## Agora, a carteira para os boletos
                ##
                #if company_id == '1' or company_id == '129':
                    #dados['carteira_id'] = 19
                #elif company_id == '130' or company_id == '131':
                    #dados['carteira_id'] = 20

                contrato_id = contrato_pool.create(cr, uid, dados)
                alt = contrato_pool.onchange_data_assinatura(self, cr, [contrato_id], data_contrato, 24)
                contrato_pool.write(cr, uid, [contrato_id], alt['value'])

                #
                # Agora, vamos tratar os itens que vão ser faturados
                # (nem todas as empresas vão gerar faturamento)
                #
                if company_id in COMPANY_FATURA:
                    produtos = {
                        'contrato_id': contrato_id,
                        'product_id': 6688,  # Serviço de monitoramento
                        'quantidade': 1,
                        'vr_unitario': valor_mensal,
                        'vr_total': valor_mensal,
                    }
                    produto_pool.create(cr, uid, produtos)

                cr.commit()

        arq.close()
        rej.close()

        return True



res_partner()
