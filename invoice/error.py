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
    'InvoiceUndefinedFieldError',
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
    pass

class InvoiceArgumentError(InvoiceError):
    pass

class InvoiceVersionError(InvoiceError):
    pass

class InvoiceSyntaxError(Exception):
    pass

class InvoiceValidationError(InvoiceError):
    pass

class InvoiceDuplicatedLineError(InvoiceValidationError):
    pass

class InvoiceMissingDocFileError(InvoiceValidationError):
    pass

class InvoiceUndefinedFieldError(InvoiceValidationError):
    pass

class InvoiceDateError(InvoiceValidationError):
    pass

class InvoiceYearError(InvoiceDateError):
    pass

class InvoiceNumberingError(InvoiceValidationError):
    pass

class InvoiceDuplicatedNumberError(InvoiceNumberingError):
    pass

class InvoiceWrongNumberError(InvoiceNumberingError):
    pass

class InvoiceUnsupportedCurrencyError(InvoiceValidationError):
    pass

class InvoiceMultipleNamesError(InvoiceValidationError):
    pass

class InvoiceTaxCodeError(InvoiceValidationError):
    pass

class InvoiceMalformedTaxCodeError(InvoiceTaxCodeError):
    pass

class InvoicePartialUpdateError(InvoiceValidationError):
    pass

class InvoiceUserValidatorError(InvoiceValidationError):
    pass
