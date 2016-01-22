# -*- coding: utf-8 -*-
#
# Copyright 2015 Simone Campagna
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__author__ = "Simone Campagna"
__all__ = [
    'InvoiceError',
    'InvoiceVersionError',
    'InvoiceArgumentError',
    'InvoiceSyntaxError',
    'InvoiceDuplicatedLineError',
    'InvoiceMissingDocFileError',
    'InvoiceValidationError',
    'InvoiceUserValidatorError',
    'InvoiceMultipleNamesError',
    'InvoiceMultipleTaxCodesError',
    'InvoiceMultipleInvoicesPerDayError',
    'InvoiceUndefinedFieldError',
    'InvoiceInconsistentIncomeError',
    'InvoiceInconsistentCpaError',
    'InvoiceInconsistentVatError',
    'InvoiceInconsistentDeductionError',
    'InvoicePartialUpdateError',
    'InvoiceYearError',
    'InvoiceDateError',
    'InvoiceNumberingError',
    'InvoiceDuplicatedNumberError',
    'InvoiceWrongNumberError',
    'InvoiceTaxCodeError',
    'InvoiceMalformedTaxCodeError',
    'InvoiceUnsupportedCurrencyError',
    'InvoicePartialUpdateError',
]

class InvoiceError(Exception):
    EXC_CODE = None
    EXC_DESCRIPTION = None

    @classmethod
    def subclasses(cls, include_self=False):
        if include_self: # pragma: no cover
            yield cls
        clist = [cls]
        while clist:
            sclist = []
            for c in clist:
                for sc in c.__subclasses__():
                    yield sc
                    sclist.append(sc)
            clist = sclist

    @classmethod
    def exc_description(cls):
        if cls.EXC_DESCRIPTION is not None:
            return cls.EXC_DESCRIPTION
        else: # pragma: no cover
            s = cls.__name__
            return s

    @classmethod
    def exc_code(cls):
        if cls.EXC_CODE is not None:
            return cls.EXC_CODE
        else: # pragma: no cover
            s = cls.__name__
            if s.startswith('Invoice'):
                s = s[len('Invoice'):]
            return s

class InvoiceArgumentError(InvoiceError):
    pass

class InvoiceVersionError(InvoiceError):
    pass

class InvoiceSyntaxError(Exception):
    pass

class InvoiceValidationError(InvoiceError):
    pass

class InvoiceDuplicatedLineError(InvoiceValidationError):
    EXC_CODE = '001'
    EXC_DESCRIPTION = 'la fattura contiene linee duplicate'

class InvoiceMissingDocFileError(InvoiceValidationError):
    EXC_CODE = '002'
    EXC_DESCRIPTION = 'il DOC file è assente'

class InvoiceNumberingError(InvoiceValidationError):
    EXC_CODE = '003'
    EXC_DESCRIPTION = 'la numerazione delle fatture è inconsistente'

class InvoiceDuplicatedNumberError(InvoiceNumberingError):
    EXC_CODE = '004'
    EXC_DESCRIPTION = 'la numerazione contiene dei duplicati'

class InvoiceWrongNumberError(InvoiceNumberingError):
    EXC_CODE = '005'
    EXC_DESCRIPTION = 'la numerazione contiene numeri non consecutivi'

class InvoiceUnsupportedCurrencyError(InvoiceValidationError):
    EXC_CODE = '006'
    EXC_DESCRIPTION = 'la valuta non è supportata'

class InvoiceMultipleNamesError(InvoiceValidationError):
    EXC_CODE = '007'
    EXC_DESCRIPTION = 'più nomi sono associati allo stesso codice fiscale'

class InvoiceMultipleTaxCodesError(InvoiceValidationError):
    EXC_CODE = '008'
    EXC_DESCRIPTION = 'più codici fiscali sono associati allo stesso nome'

class InvoiceMultipleInvoicesPerDayError(InvoiceValidationError):
    EXC_CODE = '009'
    EXC_DESCRIPTION = 'sono state generate più fatture per lo stesso cliente nello stesso giorno'

class InvoiceTaxCodeError(InvoiceValidationError):
    EXC_CODE = '010'
    EXC_DESCRIPTION = 'il codice fiscale non è corretto'

class InvoiceMalformedTaxCodeError(InvoiceTaxCodeError):
    EXC_CODE = '011'
    EXC_DESCRIPTION = 'il codice fiscale è malformato'

class InvoiceUserValidatorError(InvoiceValidationError):
    EXC_CODE = '012'
    EXC_DESCRIPTION = 'un validatore fornisce errore'

class InvoiceUndefinedFieldError(InvoiceValidationError):
    EXC_CODE = '013'
    EXC_DESCRIPTION = 'un campo obbligatorio non è definito'

class InvoiceDateError(InvoiceValidationError):
    EXC_CODE = '014'
    EXC_DESCRIPTION = 'la data non è corretta'

class InvoiceYearError(InvoiceDateError):
    EXC_CODE = '015'
    EXC_DESCRIPTION = "l'anno non è corretto"

class InvoiceInconsistentIncomeError(InvoiceValidationError):
    EXC_CODE = '016'
    EXC_DESCRIPTION = "l'incasso non corrisponde alla somma delle singole componenti"

class InvoiceInconsistentCpaError(InvoiceValidationError):
    EXC_CODE = '017'
    EXC_DESCRIPTION = "la CPA non è consistente con quanto dichiarato"

class InvoiceInconsistentVatError(InvoiceValidationError):
    EXC_CODE = '018'
    EXC_DESCRIPTION = "l'IVA non è consistente con quanto dichiarato"

class InvoiceInconsistentDeductionError(InvoiceValidationError):
    EXC_CODE = '019'
    EXC_DESCRIPTION = "la ritenuta d'acconto non è consistente con quanto dichiarato"

