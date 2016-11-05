# -*- coding: utf-8 -*-


from osv import osv, orm, fields
from datetime import date
from pybrasil.inscricao import formata_cpf, valida_cpf, limpa_formatacao
from pybrasil.inscricao import valida_certidao_civil, formata_certidao_civil, separa_certidao_civil
from pybrasil.inscricao import TIPO_CERTIDAO_CIVIL_NASCIMENTO, TIPO_CERTIDAO_CIVIL_CASAMENTO, TIPO_CERTIDAO_CIVIL_CASAMENTO_RELIGIOSO
from pybrasil.data import parse_datetime, idade_anos, hoje
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)
from pybrasil.inscricao import formata_titulo_eleitor, valida_titulo_eleitor

SEXO = [
    ('M', 'Masculino'),
    ('F', 'Feminino')
]

RACA_COR = [
    ('1', u'Indígena'),
    ('2', 'Branca'),
    ('4', 'Negra'),
    ('6', 'Amarela'),
    ('8', 'Parda'),
    ('9', u'Não informada')
]

ESTADO_CIVIL = [
    ('1', 'Solteiro(a)'),
    ('2', 'Casado(a)'),
    ('3', 'Divorciado(a)'),
    ('4', u'Viúvo(a)'),
    ('5', u'Em união estável'),
    ('6', 'Outros'),
]

ESTADO_CIVIL_SEXO = {
    '1': {u'M': u'solteiro', u'F': u'solteira'},
    '2': {u'M': u'casado', u'F': u'casada'},
    '3': {u'M': u'divorciado', u'F': u'divorciada'},
    '4': {u'M': u'viúvo', u'F': u'viúva'},
    '5': {u'M': u'em união estável', u'F': u'em união estável'},
    '6': {u'M': u'outros', u'F': u'outros'},
}

GRAU_INSTRUCAO = [
    ('01', 'Analfabeto'),
    ('02', u'Até o 5º ano incompleto do Ensino Fundamental (4ª série, 1º grau ou primário) ou alfabetizado sem ter frequentado escola regular'),
    ('03', u'5º ano completo do Ensino Fundamental (4ª série, 1º grau ou primário)'),
    ('04', u'Do 6º ao 9º ano incompletos do Ensino Fundamental (5ª a 8ª série, 1º grau ou ginásio)'),
    ('05', u'Ensino Fundamental completo (1ª a 8ª série, 1º grau ou primário e ginásio)'),
    ('06', u'Ensino Médio incompleto (2º grau, secundário ou colegial)'),
    ('07', u'Ensino Médio completo (2º grau, secundário ou colegial)'),
    ('08', u'Educação Superior incompleta'),
    ('09', u'Educação Superior completa'),
    ('10', u'Pós-graduação'),
    ('11', u'Mestrado'),
    ('12', u'Doutorado'),
]

ESTADO = [
    ('AC', u'Acre'),
    ('AL', u'Alagoas'),
    ('AP', u'Amapá'),
    ('AM', u'Amazonas'),
    ('BA', u'Bahia'),
    ('CE', u'Ceará'),
    ('DF', u'Distrito Federal'),
    ('ES', u'Espírito Santo'),
    ('GO', u'Goiás'),
    ('MA', u'Maranhão'),
    ('MT', u'Mato Grosso'),
    ('MS', u'Mato Grosso do Sul'),
    ('MG', u'Minas Gerais'),
    ('PA', u'Pará'),
    ('PB', u'Paraíba'),
    ('PR', u'Paraná'),
    ('PE', u'Pernambuco'),
    ('PI', u'Piauí'),
    ('RJ', u'Rio de Janeiro'),
    ('RN', u'Rio Grande do Norte'),
    ('RS', u'Rio Grande do Sul'),
    ('RO', u'Rondônia'),
    ('RR', u'Roraima'),
    ('SC', u'Santa Catarina'),
    ('SP', u'São Paulo'),
    ('SE', u'Sergipe'),
    ('TO', u'Tocantins'),
]

TIPO_DEPENDENTE = [
    ('01', u'Cônjuge ou companheiro(a) com o(a) qual tenha filho(s) ou viva há mais de 5 anos'),
    ('02', u'Filho(a) ou enteado(a) até 21 anos'),
    ('03', u'Filho(a) ou enteado(a) universatário(a) ou cursando escola técnica de 2º grau, até 24 anos'),
    ('04', u'Filho(a) ou enteado(a) universatário(a) ou cursando escola técnica de 2º grau, até 24 anos'),
]

TIPO_SANGUINEO = [
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
]

TIPO_CASAMENTO = [
    ('1', u'Comunhão Universal de Bens'),
    ('2', u'Comunhão Parcial de Bens'),
    ('3', u'Separação Total de Bens'),
]

TIPO_CADASTRO = [
    ('P', 'Pessoa Física'),
    ('S', 'Sócio'),
]


class hr_employee(orm.Model):
    _name = 'hr.employee'
    _description = u'Pessoa física/empregado'
    _inherit = 'hr.employee'
    _order = 'nome'
    _rec_name = 'descricao'

    def onchange_acha_estrutura(self, cr, uid, ids, employee_id, struct_id):
        valores = {}
        retorno = {'value': valores}
        contract_pool = self.pool.get('hr.contract')
        contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', employee_id), ('date_end', '=', False)])

        if contract_ids:
            if len(contract_ids) > 1:
                raise osv.except_osv(u'Inválido!', u'Há mais de 1 contrato ativo para o funcionário!')

            contract_id = contract_ids[0]
            valores['contract_id'] = contract_id
            contract_obj = contract_pool.browse(cr, uid, contract_id)
            valores['struct_id'] = contract_obj.struct_id.id

        return valores

    def _nome(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for employee_obj in self.browse(cr, uid, ids):
            res[employee_obj.id] = employee_obj.name

        return res

    def _descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for employee_obj in self.browse(cr, uid, ids):
            if employee_obj.codigo:
                res[employee_obj.id] = u'[' + unicode(employee_obj.id).zfill(4) + u'] ' + employee_obj.nome
            else:
                res[employee_obj.id] = employee_obj.nome

        return res

    def _procura_descricao(self, cr, uid, obj, nome_campo, args, context=None):
        texto = args[0][2]

        codigo = 0
        if texto.isdigit():
            codigo = int(texto)

        if codigo:
            procura = [
                '|',
                ('id', '=', codigo),
                ('nome', 'ilike', texto),
            ]
        else:
            procura = [('nome', 'ilike', texto)]

        return procura

    def _afastado(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for employee_obj in self.browse(cr, uid, ids):
            afastamento_ids = self.pool.get('hr.afastamento').search(cr, uid, [('employee_id', '=', employee_obj.id), ('data_final', '=', None)])

            res[employee_obj.id] = len(afastamento_ids) > 0

        return res

    def _company(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for employee_obj in self.browse(cr, uid, ids):
            contract_ids = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', employee_obj.id)], order='date_start desc, date_end desc')

            if len(contract_ids) > 0:
                contract_obj = self.pool.get('hr.contract').browse(cr, 1, contract_ids[0])

                if nome_campo == 'company_id':
                    if contract_obj.company_id:
                        res[employee_obj.id] = contract_obj.company_id.id
                    else:
                        res[employee_obj.id] = False

                elif nome_campo == 'department_id':
                    if contract_obj.department_id:
                        res[employee_obj.id] = contract_obj.department_id.id
                    else:
                        res[employee_obj.id] = False

            else:
                res[employee_obj.id] = False

        return res

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for employee_obj in self.browse(cr, uid, ids):
            res[employee_obj.id] = employee_obj.id

        return res

    def _partner(self, cr, uid, ids, nome_campo, args=None, context={}):
        #
        # Sincroniza o funcionário com os parceiros, pelo CPF, de forma automática
        #
        res = {}
        partner_pool = self.pool.get('res.partner')

        for employee_obj in self.browse(cr, uid, ids):
            print(employee_obj.nome, employee_obj.cpf)
            if (not employee_obj.cpf) or (not valida_cpf(employee_obj.cpf)):
                res[employee_obj.id] = False
                continue

            cpf = formata_cpf(employee_obj.cpf)

            partner_id = partner_pool.search(cr, 1, [('cnpj_cpf', '=', cpf)], order='id')

            dados = {
                'customer': False,
                'cnpj_cpf': cpf,
                'name': employee_obj.name,
                'razao_social': employee_obj.name,
                'fantasia': employee_obj.name,
                'endereco': employee_obj.endereco,
                'numero': employee_obj.numero,
                'complemento': employee_obj.complemento,
                'bairro': employee_obj.bairro,
                'municipio_id': employee_obj.municipio_id and employee_obj.municipio_id.id,
                'email_nfe': employee_obj.email,
                'email': employee_obj.email,
                'rg_numero': employee_obj.rg_numero,
                'rg_orgao_emissor': employee_obj.rg_orgao_emissor,
                'rg_data_expedicao': employee_obj.rg_data_expedicao,
                'sexo': employee_obj.sexo,
                'estado_civil': employee_obj.estado_civil,
                'pais_nacionalidade_id': employee_obj.pais_nacionalidade_id and employee_obj.pais_nacionalidade_id.id,
                'data_nascimento': employee_obj.data_nascimento,
            }

            if employee_obj.cep:
                cep = limpa_formatacao(employee_obj.cep)
                if cep.isdigit() and len(cep) == 8:
                    dados['cep'] = cep[:5] + '-' + cep[5:]

            if employee_obj.fone and valida_fone_fixo(employee_obj.fone):
                dados['fone'] = formata_fone(employee_obj.fone)

            if employee_obj.celular and valida_fone_celular(employee_obj.celular):
                dados['celular'] = formata_fone(employee_obj.celular)

            if partner_id:
                partner_id = partner_id[0]
                partner_employee_obj = partner_pool.browse(cr, 1, partner_id)

                mudou = False
                mudou = mudou or partner_employee_obj.name != employee_obj.nome
                mudou = mudou or partner_employee_obj.razao_social != employee_obj.nome
                mudou = mudou or partner_employee_obj.fantasia != employee_obj.nome
                mudou = mudou or partner_employee_obj.cnpj_cpf != cpf
                mudou = mudou or partner_employee_obj.endereco != employee_obj.endereco
                mudou = mudou or partner_employee_obj.numero != employee_obj.numero
                mudou = mudou or partner_employee_obj.complemento != employee_obj.complemento
                mudou = mudou or partner_employee_obj.bairro != employee_obj.bairro
                mudou = mudou or partner_employee_obj.municipio_id != employee_obj.municipio_id
                mudou = mudou or partner_employee_obj.cep != employee_obj.cep
                mudou = mudou or partner_employee_obj.fone != employee_obj.fone
                mudou = mudou or partner_employee_obj.celular != employee_obj.celular
                mudou = mudou or partner_employee_obj.email_nfe != employee_obj.email
                mudou = mudou or partner_employee_obj.rg_numero != employee_obj.rg_numero
                mudou = mudou or partner_employee_obj.rg_orgao_emissor != employee_obj.rg_orgao_emissor
                mudou = mudou or partner_employee_obj.rg_data_expedicao != employee_obj.rg_data_expedicao
                mudou = mudou or partner_employee_obj.sexo != employee_obj.sexo
                mudou = mudou or partner_employee_obj.estado_civil != employee_obj.estado_civil
                mudou = mudou or partner_employee_obj.pais_nacionalidade_id != employee_obj.pais_nacionalidade_id

                if mudou:
                    partner_pool.write(cr, 1, [partner_id], dados)

            else:
                partner_id = partner_pool.create(cr, 1, dados)

            res[employee_obj.id] = partner_id

        return res

    def _dependente_salario_familia(self, cr, uid, ids, nome_campo, args, context=None):
        if not len(ids):
            return {}

        if not context:
            context = {}

        res = {}

        for empregado_obj in self.browse(cr, uid, ids):
            dependentes = []

            for dependente_obj in empregado_obj.dependente_ids:
                if dependente_obj.tipo_dependente in ['02', '03', '04']:
                    idade = idade_anos(dependente_obj.data_nascimento, hoje())

                    if idade < 14:
                        dependentes.append(dependente_obj.id)

            res[empregado_obj.id] = dependentes

        return res

    _columns = {
        #'name': fields.char('Nome', size=80, required=True),
        'partner_id': fields.function(_partner, type='many2one', method=True, string=u'Parceiro', relation='res.partner', store=True),
        'company_id': fields.function(_company, type='many2one', method=True, string=u'Empresa', relation='res.company', store=True),
        'parent_company_id': fields.related('company_id', 'parent_id', type='many2one', string=u'Empresa superior', relation='res.company', store=True),
        'department_id': fields.function(_company, type='many2one', method=True, string=u'Departamento', relation='hr.department', store=True),

        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=False, select=True),
        'nome': fields.function(_nome, type='char', method=True, string=u'Nome', size=120, store=True),
        'descricao': fields.function(_descricao, type='char', string=u'Funcionário', fnct_search=_procura_descricao),

        'cpf': fields.char(u'CPF', size=14, required=True, select=True),
        'nis': fields.char(u'NIS (PIS, PASEP, NIT)', size=11, required=True, select=True),
        'sexo': fields.selection(SEXO, u'Sexo', required=True),
        'raca_cor': fields.selection(RACA_COR, u'Raça/cor', required=True),
        'estado_civil': fields.selection(ESTADO_CIVIL, u'Estado civil', required=True),
        'grau_instrucao': fields.selection(GRAU_INSTRUCAO, u'Grau de instrução', required=True),
        'tipo_sanguineo': fields.selection(TIPO_SANGUINEO, u'Tipo sanguíneo'),

        'endereco': fields.char(u'Endereço', size=60),
        'numero': fields.char(u'Número', size=60),
        'complemento': fields.char(u'Complemento', size=60),
        'bairro': fields.char(u'Bairro', size=60),
        'municipio_id': fields.many2one('sped.municipio', u'Município'),
        'cidade': fields.related('municipio_id', u'nome', type='char', string=u'Município', store=True),
        'estado': fields.related('municipio_id', u'estado', type='char', string=u'Estado', store=True),
        'cep': fields.char(u'CEP', size=9),
        'fone': fields.char(u'Fone', size=18),
        'celular': fields.char(u'Celular', size=18),
        'email': fields.char(u'Email', size=60),

        #'birthday': fields.date('Data de nascimento', required=True),
        'data_nascimento': fields.date(u'Data de nascimento'),
        'municipio_nascimento_id': fields.many2one('sped.municipio', u'Município de nascimento'),
        'pais_nacionalidade_id': fields.many2one('sped.pais', u'Nacionalidade'),
        'nome_mae': fields.char(u'Nome da mãe', size=80),
        'nome_pai': fields.char(u'Nome do pai', size=80),

        'carteira_trabalho_numero': fields.char(u'Nº da carteira de trabalho', size=11),
        'carteira_trabalho_serie': fields.char(u'Série da carteira de trabalho', size=11),
        'carteira_trabalho_estado': fields.selection(ESTADO, u'Estado da carteira de trabalho'),

        #'ric_numero': fields.char('RIC', size=14),
        #'ric_orgao_emissor': fields.char('Órgão emisssor do RIC', size=20),
        #'ric_data_expedicao': fields.date('Data de expedição do RIC'),

        'rg_numero': fields.char(u'RG', size=14),
        'rg_orgao_emissor': fields.char(u'Órgão emisssor do RG', size=20),
        'rg_data_expedicao': fields.date(u'Data de expedição do RG'),
        'numero_titulo_eleitor': fields.char(u'Nº título eleitor', size=16),
        'zona_eleitoral': fields.integer(u'Zona eleitoral'),
        'secao_eleitoral': fields.integer(u'Seção eleitoral'),
        'emancipado': fields.boolean(u'Emancipado'),
        'forma_emancipacao': fields.char(u'Forma emancipação', size=60),
        'tipo': fields.selection(TIPO_CADASTRO, u'Tipo'),

        #
        # Carteira de reservista
        #
        'carteira_reservista': fields.char(u'Reservista', size=12),

        #
        # Registro no órgão de classe (CRM, CRC, CRE, OAB)
        #
        'roc_numero': fields.char(u'Registro no órgão de classe', size=14),
        'roc_orgao_emissor': fields.char(u'Órgão emisssor do ROC', size=20),
        'roc_data_expedicao': fields.date(u'Data de expedição do ROC'),
        'roc_data_validade': fields.date(u'Data de validade do ROC'),

        'cnh_numero': fields.char(u'CNH', size=14),
        'cnh_categoria_a': fields.boolean(u'Categoria A'),
        'cnh_categoria_b': fields.boolean(u'Categoria B'),
        'cnh_categoria_c': fields.boolean(u'Categoria C'),
        'cnh_categoria_d': fields.boolean(u'Categoria D'),
        'cnh_categoria_e': fields.boolean(u'Categoria E'),
        'cnh_orgao_emissor': fields.char(u'Órgão emisssor da CNH', size=20),
        'cnh_data_expedicao': fields.date(u'Data de expedição da CNH'),
        'cnh_data_validade': fields.date(u'Data de validade da CNH'),

        'casa_propria': fields.boolean(u'Possui casa própria?'),
        'casa_propria_fgts': fields.boolean(u'Casa própria adquirida com recursos do FGTS?'),

        'deficiente_motor': fields.boolean(u'Deficiente motor?'),
        'deficiente_visual': fields.boolean(u'Deficiente visual?'),
        'deficiente_auditivo': fields.boolean(u'Deficiente auditivo?'),
        'deficiente_mental': fields.boolean(u'Deficiente mental?'),
        'deficiente_reabilitado': fields.boolean(u'Deficiente reabilitado?'),
        'deficiente_obs': fields.text(u'Deficiente - observações'),

        #
        # Estrangeiro
        #
        'estrangeiro_data_chegada': fields.date(u'Data de chegada ao Brasil'),
        'estrangeiro_data_naturalizacao': fields.date(u'Data de naturalização'),
        'estrangeiro_casado_com_brasileiro': fields.boolean(u'É casado(a) com brasileiro(a)?'),
        'estrangeiro_filho_com_brasileiro': fields.boolean(u'Tem filhos(as) com brasileiro(a)?'),

        #
        # Dependentes
        #
        'dependente_ids': fields.one2many('hr.employee_dependente', 'employee_id', u'Dependentes'),
        'dependente_salario_familia_ids': fields.function(_dependente_salario_familia, type='one2many', relation='hr.employee_dependente', method=True, string=u'Dependentes para salário família'),

        #
        # Informações bancárias
        #
        'bank_id': fields.many2one('res.bank', u'Banco', ondelete='restrict'),
        'banco_tipo_conta': fields.selection([('1', u'Conta salário'), ('2', u'Poupança')], u'Tipo da conta'),
        'banco_agencia': fields.char(u'Agência', size=15),
        'banco_conta': fields.char(u'Conta', size=20),

        'afastado': fields.function(_afastado, type='boolean', method=True, string=u'Afastado'),
        'afastamento_ids': fields.one2many('hr.afastamento', 'employee_id', string=u'Afastamentos'),

        'foto': fields.text(u'Foto'),

        #'country_id': fields.many2one('res.country', 'Nationality'),
        #'ssnid': fields.char('SSN No', size=32, help='Social Security Number'),
        #'sinid': fields.char('SIN No', size=32, help="Social Insurance Number"),


        #'identification_id': fields.char('Identification No', size=32),
        #'otherid': fields.char('Other Id', size=64),
        #'gender': fields.selection([('male', 'Male'),('female', 'Female')], 'Gender'),
        #'marital': fields.selection([('single', 'Single'), ('married', 'Married'), ('widower', 'Widower'), ('divorced', 'Divorced')], 'Marital Status'),
        #'department_id':fields.many2one('hr.department', 'Department'),
        #'address_id': fields.many2one('res.partner.address', 'Working Address'),
        #'address_home_id': fields.many2one('res.partner.address', 'Home Address'),
        #'partner_id': fields.related('address_home_id', 'partner_id', type='many2one', relation='res.partner', readonly=True, help="Partner that is related to the current employee. Accounting transaction will be written on this partner belongs to employee."),
        #'bank_account_id':fields.many2one('res.partner.bank', 'Bank Account Number', domain="[('partner_id','=',partner_id)]", help="Employee bank salary account"),
        #'work_phone': fields.char('Work Phone', size=32, readonly=False),
        #'mobile_phone': fields.char('Work Mobile', size=32, readonly=False),
        #'work_email': fields.char('Work E-mail', size=240),
        #'work_location': fields.char('Office Location', size=32),
        #'notes': fields.text('Notes'),
        #'parent_id': fields.many2one('hr.employee', 'Manager'),
        #'category_ids': fields.many2many('hr.employee.category', 'employee_category_rel', 'emp_id', 'category_id', 'Categories'),
        #'child_ids': fields.one2many('hr.employee', 'parent_id', 'Subordinates'),
        #'resource_id': fields.many2one('resource.resource', 'Resource', ondelete='cascade', required=True),
        #'coach_id': fields.many2one('hr.employee', 'Coach'),
        #'job_id': fields.many2one('hr.job', 'Job'),
        #'photo': fields.binary('Photo'),
        #'passport_id':fields.char('Passport No', size=64),
        #'color': fields.integer('Color Index'),
        #'city': fields.related('address_id', 'city', type='char', string='City'),
        #'login': fields.related('user_id', 'login', type='char', string='Login', readonly=1),
    }



    def create(self, cr, uid, dados, context=None):
        if 'cpf' in dados and dados['cpf']:
            cpf = dados['cpf']
            if not valida_cpf(cpf):
                raise osv.except_osv(u'Erro!', u'CPF inválido!')

            dados['cpf'] = formata_cpf(cpf)

        if 'data_nascimento' in dados and dados['data_nascimento']:
            ano = dados['data_nascimento'][:4]
            if ano <= '1915':
                raise osv.except_osv(u'Erro!', u'Data de nascimento inválida!')

        #if 'data_nascimento' in dados:
            #dados['birthday'] = dados['data_nascimento']

        #if 'sexo' in dados:
            #if dados['sexo'] == 'M':
                #dados['gender'] = 'male'
            #else:
                #dados['gender'] = 'female'

        ##if 'pais_nacionalidade_id' in dados:
            ##dados['country_id']

        if 'photo' in dados:
            dados['foto'] = dados['photo']

        res = super(hr_employee, self).create(cr, uid, dados, context)
        return res

    def write(self, cr, uid, ids, dados, context=None):
        if 'cpf' in dados and dados['cpf']:
            cpf = dados['cpf']
            if not valida_cpf(cpf):
                raise osv.except_osv(u'Erro!', u'CPF inválido!')

            dados['cpf'] = formata_cpf(cpf)

        if 'data_nascimento' in dados and dados['data_nascimento']:
            ano = dados['data_nascimento'][:4]
            if ano <= '1915':
                raise osv.except_osv(u'Erro!', u'Data de nascimento inválida!')

        #if 'data_nascimento' in dados:
            #dados['birthday'] = dados['data_nascimento']

        #if 'sexo' in dados:
            #if dados['sexo'] == 'M':
                #dados['gender'] = 'male'
            #else:
                #dados['gender'] = 'female'

        ##if 'pais_nacionalidade_id' in dados:
            ##dados['country_id']

        if 'photo' in dados:
            dados['foto'] = dados['photo']

        res = super(hr_employee, self).write(cr, uid, ids, dados, context)
        return res

    #def unlink(self, cr, uid, ids, context=None):
        #resource_obj = self.pool.get('resource.resource')
        #resource_ids = []
        #for employee in self.browse(cr, uid, ids, context=context):
            #resource = employee.resource_id
            #if resource:
                #resource_ids.append(resource.id)
        #if resource_ids:
            #resource_obj.unlink(cr, uid, resource_ids, context=context)
        #return super(hr_employee, self).unlink(cr, uid, ids, context=context)

    #def onchange_address_id(self, cr, uid, ids, address, context=None):
        #if address:
            #address = self.pool.get('res.partner.address').browse(cr, uid, address, context=context)
            #return {'value': {'work_email': address.email, 'work_phone': address.phone, 'mobile_phone': address.mobile}}
        #return {'value': {}}

    #def onchange_company(self, cr, uid, ids, company, context=None):
        #address_id = False
        #if company:
            #company_id = self.pool.get('res.company').browse(cr, uid, company, context=context)
            #address = self.pool.get('res.partner').address_get(cr, uid, [company_id.partner_id.id], ['default'])
            #address_id = address and address['default'] or False
        #return {'value': {'address_id' : address_id}}

    #def onchange_department_id(self, cr, uid, ids, department_id, context=None):
        #value = {'parent_id': False}
        #if department_id:
            #department = self.pool.get('hr.department').browse(cr, uid, department_id)
            #value['parent_id'] = department.manager_id.id
        #return {'value': value}

    #def onchange_user(self, cr, uid, ids, user_id, context=None):
        #work_email = False
        #if user_id:
            #work_email = self.pool.get('res.users').browse(cr, uid, user_id, context=context).user_email
        #return {'value': {'work_email' : work_email}}

    #def _get_photo(self, cr, uid, context=None):
        #photo_path = addons.get_module_resource('hr','images','photo.png')
        #return open(photo_path, 'rb').read().encode('base64')

    _defaults = {
        #'active': 1,
        #'photo': _get_photo,
        #'marital': 'single',
        #'color': 0,
        'sexo': 'M',
        'raca_cor': 8,
        'estado_civil': 1,
        'tipo': 'P',
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

    def filhos_menores_14_anos(self, cr, uid, ids, data_inicial, data_final, context={}):
        res = {}

        for empregado_obj in self.browse(cr, uid, ids):
            total = 0
            for dependente_obj in empregado_obj.dependente_ids:
                if dependente_obj.tipo_dependente in ['02', '03', '04']:
                    idade = idade_anos(dependente_obj.data_nascimento, data_final)

                    if idade < 14:
                        total += 1

            res[empregado_obj.id] = total

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def onchange_fone_celular(self, cr, uid, ids, fone, celular, context={}):
        print(fone, celular)
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

    def onchange_titulo_eleitor(self, cr, uid, ids, titulo_eleitor, context={}):

        if not valida_titulo_eleitor(titulo_eleitor):
            raise osv.except_osv(u'Erro!', u'Título inválido!')

        titulo_eleitor = formata_titulo_eleitor(titulo_eleitor)
        return {'value': {'numero_titulo_eleitor': titulo_eleitor}}

    def onchange_cep(self, cr, uid, ids, cep, contex={}):
        if not cep:
            return {}

        cep = limpa_formatacao(cep)
        if (not cep.isdigit()) or len(cep) != 8:
            raise osv.except_osv(u'Erro!', u'CEP inválido!')

        return {'value': {'cep': cep[:5] + '-' + cep[5:]}}



    _sql_constraints = [
        ('cpf_unique', 'unique(cpf)',
            u'O CPF não pode se repetir!'),
    ]

    #def _check_recursion(self, cr, uid, ids, context=None):
        #level = 100
        #while len(ids):
            #cr.execute('SELECT DISTINCT parent_id FROM hr_employee WHERE id IN %s AND parent_id!=id',(tuple(ids),))
            #ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            #if not level:
                #return False
            #level -= 1
        #return True

    #_constraints = [
        #(_check_recursion, 'Error ! You cannot create recursive Hierarchy of Employees.', ['parent_id']),
    #]

#hr_employee()

#class hr_department(orm.Model):
    #_description = "Department"
    #_inherit = 'hr.department'
    #_columns = {
        #'manager_id': fields.many2one('hr.employee', 'Manager'),
        #'member_ids': fields.one2many('hr.employee', 'department_id', 'Members', readonly=True),
    #}

#hr_department()


#class res_users(orm.Model):
    #_name = 'res.users'
    #_inherit = 'res.users'

    #def create(self, cr, uid, data, context=None):
        #user_id = super(res_users, self).create(cr, uid, data, context=context)

        ## add shortcut unless 'noshortcut' is True in context
        #if not(context and context.get('noshortcut', False)):
            #data_obj = self.pool.get('ir.model.data')
            #try:
                #data_id = data_obj._get_id(cr, uid, 'hr', 'ir_ui_view_sc_employee')
                #view_id  = data_obj.browse(cr, uid, data_id, context=context).res_id
                #self.pool.get('ir.ui.view_sc').copy(cr, uid, view_id, default = {
                                            #'user_id': user_id}, context=context)
            #except:
                ## Tolerate a missing shortcut. See product/product.py for similar code.
                #logging.getLogger('orm').debug('Skipped meetings shortcut for user "%s"', data.get('name','<new'))

        #return user_id

#res_users()


class hr_employee_dependente(orm.Model):
    _name = 'hr.employee_dependente'
    _description = 'Dependentes'
    _rec_name = 'nome'

    _columns = {
        'employee_id': fields.many2one('hr.employee', u'Funcionário'),
        'tipo_dependente': fields.selection(TIPO_DEPENDENTE, u'Tipo'),
        'nome': fields.char('Nome', size=80),
        'sexo': fields.selection(SEXO, 'Sexo'),
        'data_nascimento': fields.date('Data de nascimento'),
        'cpf': fields.char('CPF', size=11),
        'deduz_irrf': fields.boolean(u'Deduz do IRRF?'),
        'salario_familia': fields.boolean(u'Recebe salário-família?'),
        'cartorio': fields.char(u'Cartório', size=60),
        'registro_cartorio': fields.char(u'Nro Registro', size=15),
        'numero_livro': fields.char(u'Nro Livro', size=15),
        'folha': fields.char(u'Folha', size=15),
        'cidade_registro': fields.many2one('sped.municipio', u'Município de Registro'),
        'data_cadastro': fields.date('Data do cadastramento'),
        'matricula_certidao': fields.char(u'Matrícula da certidão', size=32),

        #Conjugue
        'numero_titulo_eleitor': fields.char(u'Nº título eleitor', size=16),
        'zona_eleitoral': fields.integer(u'Zona eleitoral'),
        'secao_eleitoral': fields.integer(u'Seção eleitoral'),
        'regime_casamento': fields.selection(TIPO_CASAMENTO, u'Regime casamento'),
        'profissao': fields.char(u'Profissão', size=40),
        'renda': fields.float(u'Renda'),
        'rg_numero': fields.char(u'RG', size=14),
        'rg_orgao_emissor': fields.char(u'Órgão emisssor do RG', size=20),
        'rg_data_expedicao': fields.date(u'Data de expedição do RG'),



    }

    _defaults = {
        'deduz_irrf': True,
        'salario_familia': True,
    }

    def onchange_matricula_certidao(self, cr, uid, ids, matricula_certidao, tipo_dependente):
        if not matricula_certidao:
            return {}

        #
        # Se é cônjuge, tem que ser certidão de casamento
        #
        if tipo_dependente == '01':
            certidao_valida = valida_certidao_civil(matricula_certidao, tipo_valido=TIPO_CERTIDAO_CIVIL_CASAMENTO)
            certidao_valida = certidao_valida or valida_certidao_civil(matricula_certidao, tipo_valido=TIPO_CERTIDAO_CIVIL_CASAMENTO_RELIGIOSO)

            if not certidao_valida:
                raise osv.except_osv(u'Inválido!', u'Matrícula da certidão de casamento inválida!')

        else:
            certidao_valida = valida_certidao_civil(matricula_certidao, tipo_valido=TIPO_CERTIDAO_CIVIL_NASCIMENTO)

            if not certidao_valida:
                raise osv.except_osv(u'Inválido!', u'Matrícula da certidão de nascimento inválida!')

        campos_matricula = separa_certidao_civil(matricula_certidao)

        valores = {
            'numero_livro': campos_matricula['livro'],
            'folha': campos_matricula['folha'],
            'registro_cartorio': campos_matricula['numero'],
        }

        return {'value': valores}


hr_employee_dependente()
