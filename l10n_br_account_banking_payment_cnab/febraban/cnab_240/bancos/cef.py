# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#    Copyright 2015 KMEE - www.kmee.com.br
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from ..cnab_240 import Cnab240
import re
import string
from decimal import Decimal


class Cef240(Cnab240):
    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import cef
        self.bank = cef

    def _prepare_header(self):
        '''

        :return:
        '''
        #import pudb;pu.db
        vals = super(Cef240, self)._prepare_header()
        #vals['cedente_agencia'] = vals['cedente_agencia']
        vals['cedente_agencia_dv'] = vals['cedente_dv_ag_cc']
        # TODO: adicionar campo para preencher o codigo do cedente no
        # cadastro da conta bancária
        #vals['cedente_nome'] = vals['cedente_nome']
        #vals['cedente_codigo_codCedente'] = vals['convenio']
        #vals['cedente_convenio'] = vals['convenio']
        #vals['nome_do_banco'] = u'CAIXA ECONOMICA FEDERAL'
        # Não pode pegar comentário da payment_line.
        vals['reservado_cedente_campo23'] = u'REMESSA-PRODUCAO'
        # reservado_banco_campo22 não é required. Código atualizado na
        # biblioteca cnab240
        vals['cedente_conta_dv'] = vals['cedente_dv_ag_cc']
        #vals['controleCobranca_remessaRetorno'] = 
        vals['data_credito_hd_lote'] = self.data_hoje()
        vals['controlecob_data_gravacao'] = self.data_hoje()

        return vals

    def _prepare_segmento(self, line):
        '''

        :param line:
        :return:
        '''
        vals = super(Cef240, self)._prepare_segmento(line)

        carteira, nosso_numero, digito = self.nosso_numero(
            line.move_line_id.transaction_ref)

        vals['cedente_agencia_dv'] = vals['cedente_dv_ag_cc']
        #vals['cedente_dv_ag_cc'] = unicode(str(
        #    vals['cedente_dv_ag_cc']), "utf-8")
        # Informar o Número do Documento - Seu Número (mesmo das posições
        # 63-73 do Segmento P)
        #vals['identificacao_titulo'] = unicode(str(
        #    vals['numero_documento']), "utf-8")
        # TODO: campo 27.3P CEF. Código do juros de mora
        vals['juros_cod_mora'] = 3
        #vals['carteira_modalidade'] = int(vals['boleto_modalidade'])
        vals['nosso_numero'] = int(nosso_numero)
        vals['nosso_numero_dv'] = int(digito)
        vals['prazo_baixa'] = unicode(str(
            '120'), "utf-8")

        # Precisam estar preenchidos
        # Header lote
        vals['servico_operacao'] = u'R'
        vals['servico_servico'] = 1
        vals['cedente_conta_dv'] = unicode(str(
            vals['cedente_conta_dv']), "utf-8")
        vals['cedente_codigo_codCedente'] = vals['boleto_convenio']
        #vals['codigo_protesto'] = vals['codigo_protesto']
        vals['codigo_baixa'] = 1
        vals['data_credito_hd_lote'] = vals['controlecob_data_gravacao']
        vals['cedente_convenio'] = vals['boleto_convenio']
        vals['desconto1_cod'] = 0
        vals['desconto1_data'] = 0
        vals['desconto1_percentual'] = Decimal('0.00')
        vals['valor_iof'] = Decimal('0.00')
        vals['sacado_inscricao_tipo'] = vals['sacado_inscricao_tipo']
        vals['sacado_inscricao_numero'] = vals['sacado_inscricao_numero']
        vals['sacado_nome'] = vals['sacado_nome']
        vals['sacado_endereco'] = vals['sacado_endereco']
        vals['sacado_bairro'] = vals['sacado_bairro']
        vals['sacado_cep'] = vals['sacado_cep']
        vals['sacado_cep_sufixo'] = vals['sacado_cep_sufixo']
        vals['sacado_cidade'] = vals['sacado_cidade']
        vals['sacado_uf'] = vals['sacado_uf']
        if vals['boleto_modalidade'] == 0:
            # bloqueto emitido pelo banco
            vals['carteira_titulo'] = 0
        vals['juros_mora_data'] = 0
        return vals

    # Override cnab_240.nosso_numero. Diferentes números de dígitos entre
    # CEF e Itau
    def nosso_numero(self, format):
        digito = format[-1:]
        carteira = 14
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito
