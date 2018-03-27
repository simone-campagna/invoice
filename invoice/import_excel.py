"""
Import from excel
"""

import argparse
import collections
import datetime
import os

from openpyxl import load_workbook


Field = collections.namedtuple(
    'Field', 'header field type')


OUT_DATE_FMT = '%d/%m/%Y'


def mk_date(x):
    return datetime.date.fromordinal(datetime.date(1899,12, 30).toordinal() + x).strftime(OUT_DATE_FMT)


def mk_p_vat(x):
    if x.strip() == 'A10_18':
        return  mk_float(0)
    else:
        return  mk_float(x.strip())


def mk_float(x):
    return float(x)


def read_workbook(filename, cols):
    wb = load_workbook(filename)
    if len(wb.sheetnames) != 1:
        raise ValueError("file {}: sheetnames: {!r}".format(filename, wb.sheetnames))
    sheetname = wb.sheetnames[0]
    ws = wb[sheetname]
    iws = iter(ws.rows)
    header = [cell.value for cell in next(iws)]
    for index, field in sorted(cols.items(), key=lambda x: x[0]):
        hdr = str(header[index])
        if hdr != field.header:
            raise ValueError("file {}: col {}={!r} is not {!r}".format(filename, index, hdr, field.header))
    for row in iws:
        dct = {}
        for index, field in cols.items():
            dct[field.field] = field.type(row[index].value)
        yield dct


def read_clients(filename):
    cols = {
        0: Field('Cliente', 'name', str),
        1: Field('Indirizzo', 'address', str),
        2: Field('Comune', 'city', str),
        5: Field('CodiceFiscale', 'tax_code', str),
    }
    clients = {}
    for dct in read_workbook(filename, cols):
        if dct['name'] in clients:
            raise ValueError("client {!r} already defined".format(dct['name']))
        clients[dct['name']] = dct
    return clients


def create_document(filename, number, year, rows, clients):
    if len(rows) != 1:
        raise ValueError("unsupported number of entries #{} in invoice {}/{:03d}".format(len(rows), year, number))
    filename = filename.format(year=year, number=number)
    dirname = os.path.dirname(os.path.abspath(filename))
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    taxable_income = 0
    fee = 0
    for row in rows:
        taxable_income += sum(row.get(key, 0) for key in ['fee', 'cpa', 'refunds'])
        fee += row['fee']
    if taxable_income > 77.47 and row['vat'] == 0 and row['deduction'] == 0:
        taxes = 2.0
    else:
        taxes = 0.0
    # print(taxable_income, row['vat'], row['deduction'], taxes)

    template = """\
Fattura n° {year}/{number:03d}
						Casalecchio di Reno, {date}
                                                    Spett. {name}
{address}
12345 {city}
							Cod.Fisc. {tax_code}
                     
FAC SIMILE

N° 1 {service}	{fee} euro

Rimborso spese di viaggio	{refunds} euro
Contributo previdenziale {p_cpa}%	{cpa} euro
IVA {p_vat}%	{vat} euro
Ritenuta d'acconto {p_deduction}%	{deduction} euro
Bollo (abc)	{taxes} euro
Totale fattura	{income} euro
"""
    ref_row = rows[-1]
    name = ref_row['name']
    if name not in clients:
        raise ValueError("cliente {!r} non in anagrafica".format(name))
    client = clients[name]
    data = ref_row.copy()
    data.update({
        'refunds': 0.0,
        'fee': fee,
        'taxes': taxes,
        'address': client['address'],
        'tax_code': client['tax_code'],
        'city': client['city'],
    })
    def conv(k, v):
        if k in {'fee', 'cpa', 'vat', 'refunds', 'deduction', 'taxes', 'income'}:
            return str(v).replace('.', ',')
        else:
            return v
    test = template.format(**{k: conv(k, v) for k, v in data.items()})

    with open(filename, "w") as o_file:
        o_file.write(test)

def create_documents(clients, invoices, filename):
    for (year, number), rows in invoices.items():
        create_document(filename, year, number, rows, clients)

def read_invoices(filename):
    cols = {
        1: Field('Anno', 'year', int),
        2: Field('Numero', 'number', int),
        4: Field('Data', 'date', mk_date),
        8: Field('Cliente/Fornitore', 'name', str),
        9: Field('Numero riga', 'num_row', int),
        11: Field('Descrizione', 'service', str),
        16: Field('PrezzoTot', 'fee', mk_float),
        17: Field('Aliquota', 'p_vat', mk_p_vat),
        20: Field('Totale (val)', 'income', mk_float),
        22: Field('Imposta (val)', 'vat', mk_float),
        24: Field('Cassa Previdenza (%)', 'p_cpa', mk_float),
        25: Field('Cassa previdenza (val)', 'cpa', mk_float),
        27: Field('Ritenuta (%)', 'p_deduction', mk_float),
        28: Field('Ritenuta (val)', 'deduction', mk_float),
    }
    invoices = collections.defaultdict(list)
    for dct in read_workbook(filename, cols):
        invoices[(dct['year'], dct['number'])].append(dct)
    return invoices


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clients", "-c",
        required=True,
        type=str,
        help="anagrafica clienti")
    parser.add_argument(
        "--invoices", "-i",
        required=True,
        type=str,
        help="fatture")
    parser.add_argument(
        "--output", "-o",
        default="test-docs/{year}_{number}.doc",
        type=str,
        help="documento di output")

    namespace = parser.parse_args()

    # lettura anagrafica:
    clients = read_clients(namespace.clients)

    # lettura fatture:
    invoices = read_invoices(namespace.invoices)

    # creazione documenti:
    for (year, number), rows in invoices.items():
        create_document(namespace.output, year, number, rows, clients)


if __name__ == "__main__":
    main()
    
