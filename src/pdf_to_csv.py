#!/usr/bin/python

from tika import parser
import pandas as pd
import re
import sys, getopt
import numpy as np

###############################################
#                                             #
#    From PDF to CSV -- Based on structured   #
#    reports from Actualizacion_77            #
#                                             #
###############################################

def get_ccaa_tables(string, keywords):
    tabs = []
    for kw in keywords:
        i1 = string.find(kw)
        i1 = i1 + string[i1:].find('Andalucía')
        i2 = i1 + string[i1:].find('ESPAÑA')
        tabs.append(string[i1:i2])
    return tabs

def get_fecha(string):
    ind_ini = string.find('(COVID-19)')
    ind_fin = string.find('.20')
    return string[ind_ini+12:ind_fin].split('\n')[-1]+'.2020'

def new_ccaa(text):
    dic = {'Castilla La Mancha': 'CastillaLaMancha', '.': '', ',': '.',
           'Castilla y León': 'CastillayLeón', '\n' : '',
           'C. Valenciana': 'CValenciana',
           'País Vasco': 'PaísVasco',
           'La Rioja': 'LaRioja'}
    regex = re.compile("(%s)" % "|".join(map(re.escape, dic.keys())))
    return regex.sub(lambda mo: dic[mo.string[mo.start():mo.end()]], text)

def get_lines(string):
    ccaa_lst = ['Andalucía','Aragón','Asturias','Baleares','Canarias','Cantabria','CastillaLaMancha',
                'CastillayLeón','Cataluña','Ceuta','CValenciana','Extremadura','Galicia','Madrid',
                'Melilla','Murcia','Navarra','PaísVasco','LaRioja']
    
    lst = [string[string.find(ccaa):string.find(ccaa_lst[i+1])] for i, ccaa in enumerate(ccaa_lst[:-1])]
    fin = [string[string.find('LaRioja'):]]
    
    return lst + fin

def parse_list(lst):
    lst = [el.split(' ') for el in lst]
    return lst

def hasNumbers(inputString):
    return bool(re.search(r'\d', inputString))

def hasCharacters(inputString):
    return bool(re.search(r'[a-zA-Zñáéíóú]+', inputString))

def justNumbers(inputString):
    return re.search(r'[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?', inputString).group()

def justCharacter(inputString):
    return re.search("[a-zA-Zñáéíóú]+", inputString).group()

def ind_empty_spc(lst):
    indices = [i for i, x in enumerate(lst) if x == ""]
    if len(indices)>1:
        vect = np.array(indices)[1:] - np.array(indices)[:-1]
        inddel = [indices[i] for i in np.where(vect == 1)[0]][::-1]
        if inddel:
            return inddel

def cleanlst(lista):
    for i, l in enumerate(lista):
        inddel = ind_empty_spc(l)
        if inddel:
            [l.pop(i) for i in inddel]
        for j, el in enumerate(l):
            if hasNumbers(el):
                lista[i][j] = justNumbers(el)
            elif hasCharacters(el):
                lista[i][j] = justCharacter(el)
            else:
                lista[i][j] = el
    return lista

def main(argv):
    inputfile = ''
    try:
        opts, args = getopt.getopt(argv, "i:", ["ifile="])
    except getopt.GetoptError:
        print('pdf_to_csv.py -i <inputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-i", "--ifile"):
            inputfile = arg

    raw = parser.from_file(inputfile)
    fecha = get_fecha(raw['content'])
    
    tab1, tab2 = get_ccaa_tables(raw['content'], ['Tabla 1. Casos', 'Tabla 2. Casos'])
    
    lista1 = parse_list(get_lines(new_ccaa(tab1)))
    lista2 = parse_list(get_lines(new_ccaa(tab2)))
    
    lista1 = cleanlst(lista1)
    lista2 = cleanlst(lista2)
    
    colstab1 = ['CCAA', 'casos', 'nuevos', 'incr %', 'IA','drop']
    colstab2 = ['CCAA', 'Hospitalizados', 'HospitalizadosNuevos',
                'UCI', 'UCINuevos', 'muertes', 'muertesNuevos', 'drop']
    
    data1 = pd.DataFrame(lista1, columns = colstab1).drop('drop', axis=1)
    data2 = pd.DataFrame(lista2, columns = colstab2).drop('drop', axis=1)
    
    data = pd.merge(data1,data2, on='CCAA')
    data['fecha'] = fecha
    
    cols = ['CCAA', 'fecha', 'casos', 'nuevos', 'incr %', 'IA','Hospitalizados','HospitalizadosNuevos', 
            'UCI', 'UCINuevos', 'muertes', 'muertesNuevos']
    
    
    data[cols].to_csv('../data/csv_data/COVID_es_{}.csv'.format(fecha.replace('.', '_')), index=False)
    
    print('COVID_es_{}.csv created'.format(fecha.replace('.', '_')))


if __name__ == "__main__":
    main(sys.argv[1:])
