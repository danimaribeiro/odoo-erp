# -*- coding: utf-8 -*-

from osv import osv, fields
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)
from integra_rh.models.hr_employee import SEXO, ESTADO_CIVIL, ESTADO_CIVIL_SEXO
from pybrasil.valor.decimal import Decimal as D



class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'


    _columns = {
        'fone_comercial': fields.char(u'Fone Comercial', size=18),
        'eh_contato': fields.boolean(u'É contato'),
        'data_nascimento': fields.date(u'Data de nascimento'),
        'latitude': fields.float(u'Latitude', digits=(21, 10)),
        'longitude': fields.float(u'Longitude', digits=(21, 10)),
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

        arq = open('/home/prottege/clientes.csv', 'r')
        rej = open('/home/prottege/rejeitados.csv', 'w')
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
            codigo, nome, razao_social, fantasia, cnpj_cpf, contribuinte, ie, im, endereco, numero, complemento, bairro, cidade, estado, cep, fone, email, email_nfe, dia_vencimento, valor_mensal, data_contrato, data_inicio, company_id, latitude, longitude = linha.split(';')

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
                'endereco': endereco,
                'numero': numero,
                'complemento': complemento,
                'bairro': bairro,
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

            if dia_vencimento == '0':
                dia_vencimento = '30'

            if company_id != 'NULL' and data_contrato.upper().strip() != 'NULL':
                #
                # Agora que temos o cliente e o endereço, vamos colocar o contrato
                #
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

                #
                # Prottege
                #
                elif company_id == '1':
                    dados['operacao_fiscal_servico_id'] = 328

                #
                # ProttSeg
                #
                elif company_id == '130':
                    dados['operacao_fiscal_servico_id'] = 329

                #
                # Agora, a carteira para os boletos
                #
                if company_id == '1' or company_id == '129':
                    dados['carteira_id'] = 19
                elif company_id == '130' or company_id == '131':
                    dados['carteira_id'] = 20

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
                        'product_id': 2,  # Serviço de monitoramento
                        'quantidade': 1,
                        'vr_unitario': valor_mensal,
                        'vr_total': valor_mensal,
                    }
                    produto_pool.create(cr, uid, produtos)

        arq.close()
        rej.close()

        return True



res_partner()
