# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#            Gustavo Lepri
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


class Santander240(Cnab240):
    """

    """

    def __init__(self):
        """

        :return:
        """
        super(Cnab240, self).__init__()
        from cnab240.bancos import santander
        self.bank = santander

    def _prepare_header(self):
        """

        :param order:
        :return:
        """
        vals = super(Santander240, self)._prepare_header()
        del vals['arquivo_hora_de_geracao']
        vals['cedente_dv_ag_cc'] = int(
            vals['cedente_dv_ag_cc'])
        vals['cedente_agencia_dv'] = int(
            vals['cedente_agencia_dv']),
        return vals

    def _prepare_segmento(self, line):
        """

        :param line:
        :return:
        """
        vals = super(Santander240, self)._prepare_segmento(line)

        carteira, nosso_numero, digito = self.nosso_numero(
            line.move_line_id.transaction_ref)

        vals['cedente_dv_ag_cc'] = int(
            vals['cedente_dv_ag_cc'])
        vals['cedente_agencia_conta_dv'] = int(
            vals['cedente_dv_ag_cc'])
        vals['carteira_numero'] = int(carteira)
        vals['nosso_numero'] = int(nosso_numero)
        vals['nosso_numero_dv'] = int(digito)
        dig_ag = int(vals['cedente_agencia_dv'])
        vals['cedente_agencia_dv'] = dig_ag
        vals['conta_cobranca'] = vals['cedente_conta']
        vals['conta_cobranca_dv'] = int(vals['cedente_conta_dv'])
        vals['forma_cadastramento'] = 1
        # tipo documento : 1- Tradicional , 2- Escritural
        vals['tipo_documento'] = 1 
        especie = 2
        if vals['especie_titulo'] == '01':
            especie = 2
        elif vals['especie_titulo'] == '02':
            especie = 12
        elif vals['especie_titulo'] == '08':
            especie = 4
        vals['especie_titulo'] = especie 
        vals['juros_mora_data'] = 0 

        return vals

    # Override cnab_240.nosso_numero. Diferentes números de dígitos entre
    # CEF e Itau
    def nosso_numero(self, format):
        digito = format[-1:]
        carteira = format[:3]
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito
