#manipulación de datos
import pandas as pd
import numpy as np
import sys
import itertools
import regex

#interfaz gráfica
import streamlit as st
from PIL import Image

### Library of functions ###
def check_sheets_existance(file):
    ''' Check the existance of needed spreadsheets on excel file'''
    check_file = pd.ExcelFile(file)
    list_of_sheets = check_file.sheet_names
    needed_sheets = ['Diccionario de Datos','Migration'] 
    check = [sheet for sheet in needed_sheets if sheet in list_of_sheets]
    not_found_sheets = [sheet for sheet in needed_sheets if sheet not in check]
    if len(check) == len(needed_sheets):
        return True
    else:
        st.write("No se encontró la hoja de cálculo '{}'. Verificar archivo KYD !!!".format(not_found_sheets[0]))
        return False
    
def find_skiprows_on_excel(file, name, cols_table): 
    ''' Find de integer where the table on excel is found '''
    df = pd.read_excel(file, sheet_name = name , header=0)        
    index_table = []
    for col in df.columns:
        for i in range(0, len(df), 1):
            for val in cols_table:
                if val in str(df.at[i, col]):
                    index_table.append(i+1)
    result = all(element == index_table[0] for element in index_table)
    if (result):
        st.write(r'$\checkmark$:  Tabla encontrada en {} !!!'.format(name))
        return True, index_table[0]
    else:
        st.write(r'$\otimes$:  Tabla no encontrada en {} !!!'.format(name))
        return False, [] 
    
def load_excel(file, ind_kyd, ind_mig):
    ''' Import excel file and load the data stored in Diccionario de Datos spreadsheet '''
    
    #Read data from sheet: 'Diccionario de Datos and skip first n rows of the excel file
    df = pd.read_excel(file, sheet_name='Diccionario de Datos' , header=0, skiprows=ind_kyd)
    df2 = pd.read_excel(file, sheet_name='Migration' , header=0, skiprows=ind_mig)
    
    #Erase 1st row of the dataframe that contain spanish column name
    df.drop(index=df.index[0], axis=0, inplace=True)
    df = df.reset_index()
    del df['index'] 
    
    #Erase all calumns that contain Unnamed
    column_name = [col for col in df.columns if 'Unnamed:' not in col]
    df = df[column_name]
    
    #Erase all columns that containt Unnamed
    column_name = [col for col in df2.columns if 'Unnamed:' not in col]
    df2 = df2[column_name]
    
    return df, df2
    
def check_columns_existence(df, columns, name):
    ''' Verify the existance of specific columns on excel file '''
    
    # remove empty spaces in column names
    for col in df.columns:
        df = df.rename(columns={col:remove_empty_spaces(col)})
    
    #Check existance of column name listed above and rename it
    match = []
    for col1 in columns:
        for col2 in df.columns:
            if col1 in col2:
                match.append(col1)
                df = df.rename(columns={col2:col1})
                
    missing_columns = [col for col in columns if col not in match]
  
    if len(match) == len(columns):
        st.write(r'$\checkmark$:  Validación nombre de columnas en {} !!!'.format(name))
        return df, True
    else:          
        st.write(r'$\otimes$:  Existen columnas con nombres distintos en archivo {} !!!'.format(name))
        st.write('Revisar columnas en archivo {} para seguir con el proceso'.format(name))
        st.write(" '{}' columna no encontrada".format(missing_columns[0]))
        return df, False
    
def show_duplicated_data(df, n_rows):
    """ Verify the existence of duplicated values """
    columns_to_check = ['NOMBRE LÓGICO TABLA','NOMBRE LÓGICO DEL CAMPO']
    
    df_check = df[columns_to_check].groupby(columns_to_check)[['NOMBRE LÓGICO DEL CAMPO']].count()
    df_check = df_check.rename(columns={'NOMBRE LÓGICO DEL CAMPO':'count'})
    df_check = df_check[df_check['count']>1]
    df_check = df_check.reset_index()
    
    position_1st = []
    position_2dn = []
    for table, group in df_check.groupby('NOMBRE LÓGICO TABLA'):
        for i,row in enumerate(group.itertuples()):
            cut = ((df['NOMBRE LÓGICO TABLA'] == row._1)&(df['NOMBRE LÓGICO DEL CAMPO'] == row._2))
            position_1st.append(df[columns_to_check][cut].index[0]+n_rows+3)
            position_2dn.append(df[columns_to_check][cut].index[1]+n_rows+3)
    df_check['posición 1ro'] = position_1st
    df_check['posición 2do'] = position_2dn
    
    if len(df_check) != 0: 
            st.write(r'$\otimes$:  Se detectaron valores repetidos en KYD !!!')
            st.write('Esto puede causar errores al momento de crear modelo en ERWIN')
            st.dataframe(df_check.astype(str))
            return False 
    else:
        st.write(r'$\checkmark$:  No existen valores repetidos en KYD !!!')
        return True
    
def check_json_objects(text):
    ''' check existance of '''
    text = str(text)
    pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}')
    text = pattern.findall(text)
    if len(text) == 0:
        return False
    else:
        return True
    
def show_existance_of_json_data(df, n_rows):
    """ Verify the existence of json values """
    
    dfjson = df.copy()
    
    dfjson['JSON check'] = dfjson[~(dfjson['VALORES ESPERADOS/ACEPTADOS'].isna())]['VALORES ESPERADOS/ACEPTADOS'].apply(check_json_objects)
    
    cut_tipo_dato = ((dfjson['TIPO DE DATO'] == 'JSON')|
                     (dfjson['TIPO DE DATO'] == 'ARRAY')|
                     (dfjson['TIPO DE DATO'] == 'STRUCT'))
    
    cut_json = (dfjson['JSON check'] == True)
    
    cut = (cut_tipo_dato | cut_json)
    
    df_json = dfjson[cut]

    ## Detect position in KYD
    position = []
    for i,row in enumerate(df_json.itertuples()):
        position.append(df_json.index[i]+n_rows+3)
    df_json['posición'] = position
    
    df_json = df_json[['posición','NOMBRE LÓGICO TABLA','NOMBRE LÓGICO DEL CAMPO','TIPO DE DATO','VALORES ESPERADOS/ACEPTADOS']]
     
    if len(df_json) != 0:
            st.write(r'$\otimes$:  Se detectaron datos de tipo JSON en KYD!! \n\n Esto se debe reportar al respectivo dominio !!!')
            st.dataframe(df_json.astype(str))
            return False
    else:
        st.write(r'$\checkmark$:  No existen datos de tipo JSON en KYD !!!')
        return True

def show_fk_tables_without_name(df, n_rows):
    ''' Check if a foreign key field has asigned a table name '''
    cut_fk = (df['LLAVE FK'] == 'SI')
    cut_name_fk = ((df['NOMBRE DE LA TABLA FK'] == 'SIN DATOS')|(df['NOMBRE DE LA TABLA FK'].isna()))
    
    nameless_tables = df[cut_fk&cut_name_fk][['NOMBRE LÓGICO TABLA','NOMBRE LÓGICO DEL CAMPO','LLAVE FK','NOMBRE DE LA TABLA FK']]
    
    ## Detect position in KYD
    position = []
    for i,row in enumerate(nameless_tables.itertuples()):
        position.append(nameless_tables.index[i]+n_rows+3)
    nameless_tables['posición'] = position
    
    if len(nameless_tables) == 0:
        st.write(r'$\checkmark$:  No existen campos foreign key sin nombres en KYD !!!')
        return True
    else:
        st.write(r"$\otimes$:  Se detectaron campos foreign key sin nombres en KYD !!!")
        st.write("Esto genera tablas foráneas sin nombre o con nombre 'SIN DATOS'")
        st.dataframe(nameless_tables.astype(str))
        return False
    
def fill_field_fk_parameters(df):
    ''' Fill the name of the field FK based on the existen PK fields  '''
    campos_PK = df[(df['LLAVE PK'] == 'SI')][['NOMBRE LÓGICO TABLA','NOMBRE LÓGICO DEL CAMPO']]
    campos_FK_dict = dict( zip(campos_PK['NOMBRE LÓGICO TABLA'], campos_PK['NOMBRE LÓGICO DEL CAMPO']) ) 
    
    for i, row in enumerate(df['NOMBRE DE LA TABLA FK']):
        table_name = None
        if (row == 'SIN DATOS'):
            df.at[i, 'NOMBRE DEL CAMPO FK'] = 'SIN DATOS'
        else:
            if (df.at[i, 'NOMBRE DEL CAMPO FK'] == 'SIN DATOS'):
                if row in campos_PK['NOMBRE LÓGICO TABLA'].tolist():
                    table_name = campos_FK_dict[row]
                    df.at[i, 'NOMBRE DEL CAMPO FK'] = table_name 
                else:
                    df.at[i, 'NOMBRE DEL CAMPO FK'] = df.at[i, 'NOMBRE LÓGICO DEL CAMPO']
                    
    return df     
    
def rename_columns(df):
    ''' Rename df columns '''
    df.rename(columns = {'NOMBRE LÓGICO TABLA':'table', 
                         'NOMBRE LÓGICO DEL CAMPO':'field',
                         'TIPO DE DATO':'type', 
                         'LLAVE PK':'key_pk',
                         'LLAVE FK':'key_fk',
                         'NOMBRE DE LA TABLA FK':'table_fk',
                         'NOMBRE DEL CAMPO FK':'field_fk',
                         '¿PUEDE SER NULO?':'is_null',
                         'CLASIFICACIÓN DE DATOS':'type_data'}, inplace=True)
    return df

def inverse_rename_columns(df):
    ''' Rename df columns '''
    df.rename(columns = {'table':'NOMBRE LÓGICO TABLA', 
                         'field':'NOMBRE LÓGICO DEL CAMPO',
                         'type':'TIPO DE DATO', 
                         'key_pk':'LLAVE PK',
                         'key_fk':'LLAVE FK',
                         'table_fk':'NOMBRE DE LA TABLA FK',
                         'field_fk':'NOMBRE DEL CAMPO FK', 
                         'is_null':'¿PUEDE SER NULO?',
                         'type_data':'CLASIFICACIÓN DE DATOS'}, inplace=True)
    return df

def show_missing_data(df, n_rows, name):
    """ Return a Pandas dataframe describing the contents of a source dataframe including missing values. It will return a dataframe with all the columns with missing values """
       
    columns = [col for col in df.columns]
    count   = [len(df[col]) for col in df.columns]
    missing = [df[col].isna().sum() for col in df.columns]
    pc_missing = [round( (df[col].isna().sum() / len(df[col]) ) * 100, 2) for col in df.columns]
  
    first_missing = []
    
    for col in df.columns:
        if df[col].isna().sum() > 0:
            first_missing.append( df[df[col].isnull()][col].index[0]+n_rows+3 )
        else:
            first_missing.append(0)

    df_output = pd.DataFrame({
                   'columna': columns, 
                   'nº total de filas': count,
                   'nº filas vacías': missing, 
                   '% filas vacías': pc_missing,
                   'posición 1ra fila vacía': first_missing
                            })    
    
    #list of columns with missing data
    list_col_with_missing_data = df_output[df_output['% filas vacías'] > 0.0].columna.tolist()
    
    #number of columns with missing data
    n_col_with_missing_data = len(list_col_with_missing_data)
    
    if (df_output['% filas vacías'].sum() != 0):
        if list_col_with_missing_data == ['¿PUEDE SER NULO?']:
            st.write(r'$\checkmark$:  No existen columnas con datos faltantes en {} !!!'.format(name))
            df[['¿PUEDE SER NULO?']] = df[['¿PUEDE SER NULO?']].replace(np.nan, 'NULL')
            return []
        else:
            st.write(r'$\otimes$:  Existen {} de {} columnas con datos faltantes en {} !!!'.format(n_col_with_missing_data, len(df_output), name))
            st.dataframe(df_output[df_output['% filas vacías'] > 0.0].astype(str)) 
            return list_col_with_missing_data
    else:
        st.write(r'$\checkmark$:  No existen columnas con datos faltantes en {} !!!'.format(name))
        #st.dataframe(df_output[df_output['%_nan'] > 0.0].astype(str)) 
        return []

def remove_empty_spaces(text):
    ''' Remove first, last and several spaces in between from string '''
    text = str(text)
    text = "".join(text.rstrip().lstrip())
    text = " ".join(text.split())
    return text

def replace_space_by_(text):
    ''' Replace empty spaces in between by _ from string '''
    text = str(text)
    if text != 'SIN DATOS':
        text = "_".join(text.split())
        return text
    else:
        return text

def transform_text(df):
    ''' Transform all columns to upper case, removing first and last empty space, change - by _, change space in between with _ on specific columns '''
    
    list_of_cols_to_consider = ['TABLA / DATASET / TÓPICO A MIGRAR',
                                'NOMBRE DE LA TABLA EN ORIGEN',
                                'NOMBRE LÓGICO TABLA',
                                'NOMBRE DEL CAMPO EN EL ORIGEN',
                                'NOMBRE LÓGICO DEL CAMPO',
                                'NOMBRE DE LA TABLA FK',
                                'NOMBRE DEL CAMPO FK']
    
    for col in df.columns:
        df[[col]] = df[[col]].apply(lambda x: x.str.upper())
        df[col] = df[col].apply(remove_empty_spaces)
        df[[col]] = df[[col]].apply(lambda x: x.str.replace('-','_'))   
        if col in list_of_cols_to_consider:
            df[col] = df[col].apply(replace_space_by_)
            
    return df

def transform_text_migration(df):
    ''' Transform all columns to upper case, removing first and last empty space and change space in between with _ on specific columns '''
    
    list_of_cols_to_consider = ['NOMBRE DE LA TABLA',
                                'TYPE OF LOAD',
                                'PERIODICIDAD DE CARGA',
                                'CANTIDAD DE DIAS A EXTRAER EN LA CARGA',
                                'COLUMNA DE FILTRADO']
        
    #Change to upper case, remove empty spaces and change ' ' to _
    for col in df.columns:
        df[[col]] = df[[col]].astype(str).apply(lambda x: x.str.upper())
        df[col] = df[col].apply(remove_empty_spaces)
        if col in list_of_cols_to_consider:
            df[col] = df[col].apply(replace_space_by_)
            
    return df

def fill_load_ts(df, df2):
    ''' Check from Migration spreadsheet the number of tables to add the field __TS'''
    
    df_tablas = df.groupby('NOMBRE LÓGICO TABLA').first()
    df_tablas = df_tablas.reset_index()
    
    missing_items = [col for col in df_tablas['NOMBRE LÓGICO TABLA'] if col not in df2['NOMBRE DE LA TABLA'].tolist() ]
    allowed_items = df2[df2['COLUMNA DE FILTRADO'] == 'NONE']['NOMBRE DE LA TABLA']
    df_tablas = df_tablas[df_tablas['NOMBRE LÓGICO TABLA'].isin(allowed_items)]
    
    if len(missing_items) == 0:
        df_load_ts = pd.DataFrame()
        for i in df_tablas.index:        
            df2 = pd.DataFrame(
                        {'FUENTE ORIGEN':[df_tablas['FUENTE ORIGEN'][i]],
                        'TABLA / DATASET / TÓPICO A MIGRAR':[df_tablas['TABLA / DATASET / TÓPICO A MIGRAR'][i]],
                        'NOMBRE DE LA TABLA EN ORIGEN':[df_tablas['NOMBRE DE LA TABLA EN ORIGEN'][i]],
                        'DESCRIPCIÓN DE LA TABLA':['DATA UPLOAD DATE AND TIME'],
                        'NOMBRE LÓGICO TABLA':[df_tablas['NOMBRE LÓGICO TABLA'][i]],
                        'NOMBRE DEL CAMPO EN EL ORIGEN':[df_tablas['NOMBRE DEL CAMPO EN EL ORIGEN'][i]],
                        'NOMBRE LÓGICO DEL CAMPO':['LOAD_TS'],
                        'DESCRIPCIÓN CAMPO':['DATA UPLOAD DATE AND TIME'],
                        'TIPO DE DATO':['DATETIME'],
                        '¿PUEDE SER NULO?':['NOT NULL'],
                        'LLAVE PK':['NO'],
                        'LLAVE FK':['NO'],
                        'NOMBRE DE LA TABLA FK':['SIN DATOS'],
                        'NOMBRE DEL CAMPO FK':['SIN DATOS'],
                        'VALORES ESPERADOS/ACEPTADOS':['SIN DATOS'],
                        'CLASIFICACIÓN DE DATOS':['NS'],
                        'NOMBRE FÍSICO TABLA/DATASET/TOPICO':['SIN DATOS'],
                        'NOMBRE FÍSICO CAMPO':['SIN DATOS']})
            df_load_ts = pd.concat([df_load_ts, df2])
        if len(df_load_ts) > 0:
            st.write(r'Se detectaron {} campos LOAD_TS. ¿Desea agregarlos al archivo .ddl?'.format(len(df_load_ts)))
            answer = question()
            
            if answer.upper() == 'SI':
                df = pd.concat([df, df_load_ts])
                st.write(r'$\checkmark$:  Se crearon correctamente {} campos LOAD_TS !!!'.format(len(df_load_ts)))    
                df = df.reset_index()
                del df['index']
                return df
            if answer.upper() == 'NO':
                st.write(r'$\checkmark$:  No se agregaron los campos LOAD_TS !!!')
                return df
    else:
        st.write(r"$\otimes$:  Faltan {} tablas en hoja 'Migration' !!! ".format(len(missing_items)))
        for col in missing_items:
            st.write(col)
        st.write("No se generaron campos LOAD_TS")
        return df

    
def replace_missing_values(df, list_columns):
    ''' Considere the list of columns to check and provide to the user the oportunity to fill the nan values found '''
    for i,col in enumerate(list_columns):
        df[[col]] = df[[col]].apply(lambda x: x.str.upper())
        st.write("{}- La columna '{}' contiene '{}' celdas vacías:".format(i+1, col,  df[col].isna().sum() ))
        #st.dataframe(df[df[[col]].isna()==True][[col]].astype(str))
        st.write("¿Que valor deseas reemplazar en celda vacía? (escribir en terminal)")
        new_word = str(input('Introduzca texto: '))
        #new_word = st.text_input('Texto: ', '')
        st.markdown(f"Se cambiara 'nan' por '{new_word}'")
        df[[col]] = df[[col]].replace(np.nan, new_word)
        df[[col]] = df[[col]].apply(lambda x: x.str.upper())
    
    return df

def standarize_data_on_columns(df):
    ''' Change the values specific cells for a standard one'''
    
    #type of data
    df[['TIPO DE DATO']] = df[['TIPO DE DATO']].apply(lambda x: x.str.upper())
    df['TIPO DE DATO'] = np.where( (df['TIPO DE DATO'] == 'STRING'), 'VARCHAR(255)', df['TIPO DE DATO'] )
    df['TIPO DE DATO'] = np.where( (df['TIPO DE DATO'] == 'TEXT'), 'VARCHAR(255)', df['TIPO DE DATO'] )
    df['TIPO DE DATO'] = np.where( (df['TIPO DE DATO'] == 'FLOAT'), 'DECIMAL(12,4)', df['TIPO DE DATO'] )
    df['TIPO DE DATO'] = np.where( (df['TIPO DE DATO'] == 'DOUBLE'), 'DECIMAL(12,4)', df['TIPO DE DATO'] )
    df['TIPO DE DATO'] = np.where( (df['TIPO DE DATO'] == 'TIMESTAMP'), 'DATETIME', df['TIPO DE DATO'] )
    df['TIPO DE DATO'] = np.where( (df['TIPO DE DATO'].str.contains('INT') ), 'INT', df['TIPO DE DATO'] ) 
        
    #primary key 
    df[['LLAVE PK']] = df[['LLAVE PK']].apply(lambda x: x.str.upper())
    df['LLAVE PK'] = np.where( (df['LLAVE PK'] == 'PK')|
                               (df['LLAVE PK'] == 'YES'), 'SI', df['LLAVE PK'] )
    df['LLAVE PK'] = np.where( (df['LLAVE PK'] == 'NO'), 'NO', df['LLAVE PK'] )
        
    #foreign key
    df[['LLAVE FK']] = df[['LLAVE FK']].apply(lambda x: x.str.upper())
    df['LLAVE FK'] = np.where( (df['LLAVE FK'] == 'FK')|
                               (df['LLAVE FK'] == 'YES'), 'SI', df['LLAVE FK'] )
    df['LLAVE FK'] = np.where( (df['LLAVE FK'] == 'NO'), 'NO', df['LLAVE FK'] )
    
    #is_null
    df[['¿PUEDE SER NULO?']] = df[['¿PUEDE SER NULO?']].apply(lambda x: x.str.upper())
    df['¿PUEDE SER NULO?'] = np.where( (df['¿PUEDE SER NULO?'] == 'SI')|
                                       (df['¿PUEDE SER NULO?'] == 'YES')|
                                       (df['¿PUEDE SER NULO?'] == 'NULL'), 'NULL', df['¿PUEDE SER NULO?'])
    df['¿PUEDE SER NULO?'] = np.where( (df['¿PUEDE SER NULO?'] == 'NO'), 'NOT NULL', df['¿PUEDE SER NULO?'] )
    
    #sensitivity of data
    df[['CLASIFICACIÓN DE DATOS']] = df[['CLASIFICACIÓN DE DATOS']].apply(lambda x: x.str.upper())
    df['CLASIFICACIÓN DE DATOS'] = np.where( (df['CLASIFICACIÓN DE DATOS'] == 'NO SENSIBLE'), 'NS', df['CLASIFICACIÓN DE DATOS'])
    df['CLASIFICACIÓN DE DATOS'] = np.where( (df['CLASIFICACIÓN DE DATOS'] == 'SENSIBLE'), 'SE', df['CLASIFICACIÓN DE DATOS'])
    df['CLASIFICACIÓN DE DATOS'] = np.where( (df['CLASIFICACIÓN DE DATOS'] == 'ALTAMENTE SENSIBLE'), 'HS', df['CLASIFICACIÓN DE DATOS'])
    
    return df

def split_on_sensitibity(df):
    '''Split dataframe depending of the type of sensitibity of the respective table'''
    
    df = rename_columns(df)
    
    cut_HS = (df['type_data']=='HS')
    cut_SE = (df['type_data']=='SE')
    cut_NS = (df['type_data']=='NS')
    
    list_HS = []
    list_SE = []
    
    #Select all the tables that contain HS data
    for table, group in df[cut_HS].groupby('table'):
        list_HS.append(table)
    df_HS = df[df['table'].isin(list_HS)]
       
    #Select all the rows that contain NS data
    df_NS = df[cut_NS]
        
    #Select all the tables that contain SE data and remove those who also contain HS data
    for table, group in df[cut_SE].groupby('table'):
        list_SE.append(table)
    list_SE_filtered = [table for table in list_SE if table not in list_HS]
    df_SE = df[df['table'].isin(list_SE_filtered)]
    #Select tables with NS data from 
    #list_of_tables_with_NS_data = df_SE[df_SE['field_fk']!='SIN DATOS'].table_fk.unique()
    #df_SE_fk = df_NS[(df_NS['table'].isin(list_of_tables_with_NS_data))&(df_NS['key_pk']=='SI')]
    #df_SE_final = pd.concat([df_SE, df_SE_fk])
  
    
    df_HS = inverse_rename_columns(df_HS)
    df_SE = inverse_rename_columns(df_SE)
    df_NS = inverse_rename_columns(df_NS)
    #df_SE_final = inverse_rename_columns(df_SE_final)
    
    return df_HS, df_SE, df_NS

def split_on_subdominio(df, df2):
    '''Split dataframe depending of the type of sub-dominio each table belong '''
    
    sub_dom = [sub_dom for sub_dom in df2['SUB-DOMINIO'].unique()]
    list_tables_per_sd = [df2[(df2['SUB-DOMINIO'] == sb)]['NOMBRE DE LA TABLA'].tolist() for sb in sub_dom]
    
    df_table_subdomains = []
    df_subdomains = []
    for i, lista_sd in enumerate(list_tables_per_sd):
        df_table_subdomains.append(pd.DataFrame({sub_dom[i]:lista_sd}))
        df_subdomains.append(df[df['NOMBRE DE LA TABLA EN ORIGEN'].isin(lista_sd)])
        
    zipped_df = list(zip(sub_dom, df_subdomains))
    final = pd.concat(df_table_subdomains, axis=1) 
    st.write('### Lista de tablas por subdominio')
    st.dataframe(final)      
        
    return zipped_df

def sensitive_data_name(data):
    ''' Depending on the choice in the data type returns the name of the category '''
    if data.upper() == 'HS': return 'High Sensitive'
    if data.upper() == 'SE': return 'Sensitive'
    if data.upper() == 'NS': return 'Non Sensitive'
    if data.upper() == 'ALL': return 'Sin restricción'
    else: return data.upper()

def create_modified_excel_file(df, sub_domain, type_data):
    ''' Generate a new excel file considering all the columns with missing values filled ''' 
    
    df = inverse_rename_columns(df)
    type_data_name = sensitive_data_name(type_data)
    
    if type_data == 'ALL':
        excel_output = pd.ExcelWriter('KYD_'+sub_domain+'.xlsx')
        st.write(r'$\checkmark$:  Archivo KYD_'+sub_domain+'.xlsx con datos '+type_data_name+' creado satisfactoriamente!')
    else:
        excel_output = pd.ExcelWriter('KYD_'+sub_domain+'_'+type_data+'.xlsx')
        st.write(r'$\checkmark$:  Archivo KYD_'+sub_domain+'_'+type_data+'.xlsx con datos '+type_data_name+' creado satisfactoriamente!')
    
    with excel_output as writer:
        df.to_excel(writer, sheet_name='KYD', startrow=5, startcol=2, index=False)
    
    return

def status_check_of_KYD(df, ind_kyd):
    ''' Function that collect different cross checks on KYD file '''
    
    #columns to be check
    columnas = ['FUENTE ORIGEN',
                'TABLA / DATASET / TÓPICO A MIGRAR',
                'NOMBRE DE LA TABLA EN ORIGEN',
                'DESCRIPCIÓN DE LA TABLA',
                'NOMBRE LÓGICO TABLA',
                'NOMBRE DEL CAMPO EN EL ORIGEN',
                'NOMBRE LÓGICO DEL CAMPO',
                'DESCRIPCIÓN CAMPO',
                'TIPO DE DATO',
                '¿PUEDE SER NULO?',
                'LLAVE PK',
                'LLAVE FK',
                'NOMBRE DE LA TABLA FK',
                'NOMBRE DEL CAMPO FK',
                'VALORES ESPERADOS/ACEPTADOS',
                'CLASIFICACIÓN DE DATOS',
                'NOMBRE FÍSICO TABLA/DATASET/TOPICO',
                'NOMBRE FÍSICO CAMPO']
    
    #check existence of key columns
    df, check_key_columns = check_columns_existence(df, columnas, 'KYD')
        
    #show duplicated values in case of existance
    check_duplicated = show_duplicated_data(df, ind_kyd)
            
    #show existance of json data
    check_json = show_existance_of_json_data(df, ind_kyd)
            
    #show existance of foreign tables nameless
    check_FK_table = show_fk_tables_without_name(df, ind_kyd)
    
    if (check_key_columns & check_duplicated & check_json & check_FK_table):
        return df, True
    else:
        return df, False
    
def status_check_of_Migration(df):
    ''' Function that collect different cross checks on Migration file '''
    
    columns = ['NOMBRE DE LA TABLA',
               'TYPE OF LOAD',
               'PERIODICIDAD DE CARGA',
               'CANTIDAD DE DIAS A EXTRAER EN LA CARGA',
               'COLUMNA DE FILTRADO']
                          
    #check existence of key columns
    df, check_key_columns = check_columns_existence(df, columns, 'Migration')
    
    if (check_key_columns):
        return df, True
    else:
        return df, False
    
def find_tables(file):
    ''' Find the tables on respectives spreadsheets based on the columns names listed below '''
    
    cols_kyd = ['FUENTE ORIGEN','TABLA / DATASET / TÓPICO A MIGRAR','NOMBRE DE LA TABLA EN ORIGEN']        
    cols_mig = ['NOMBRE DE LA TABLA','TYPE OF LOAD','PERIODICIDAD DE CARGA']
    
    check_kyd, ind_kyd = find_skiprows_on_excel(file, 'Diccionario de Datos', cols_kyd)
    check_mig, ind_mig = find_skiprows_on_excel(file, 'Migration', cols_mig)
    
    if (check_kyd & check_mig):
        return True, ind_kyd, ind_mig
    else:
        return False, ind_kyd, ind_mig
        
def check_subdominio(df):
    ''' Check for subdominio existance '''
    
    if 'SUB-DOMINIO' in df:
        sub_dom = [sub_dom for sub_dom in df['SUB-DOMINIO'].unique()]
        count = len(sub_dom)
        tab_per_sd = [len(df[df['SUB-DOMINIO']==sd]) for sd in sub_dom]
    
        df_output = pd.DataFrame({'sub dominio': sub_dom,
                                  'nº tablas por sub dom':tab_per_sd})    
    
        st.write('Archivo Migration contiene {} Sub-dominios'.format(count))
        st.dataframe(df_output)
        return sub_dom
    else:
        st.write('No existen Sub-dominios en archivo Migration')
        return []

def question():
    ''' Ask to the user to write a decision YES or NO'''
    allowed_answers = ['SI', 'NO']
    answer  = None
    count = 0
    while answer not in allowed_answers:
        answer = str(input('Respuesta: ')) 
        answer = answer.upper()
        if answer not in allowed_answers: 
            st.write("Solo acepto SI o NO como respuesta. Intenta nuevamente")
    
    st.write("tu respuesta fue: {}".format(answer))
    return answer

def write_ddl_file(df, sub_domain, type_data, list_primary_table_global):
    ''' Generate .ddl file '''
    indent = " "*4
    ispk = ['SI']
    isfk = ['SI']
   
    df = rename_columns(df)
    
    list_of_primary_tables = df['table'].unique()
    list_of_foreign_tables = [col for col in df['table_fk'].unique() if col not in list_of_primary_tables]
    if 'SIN DATOS' in list_of_foreign_tables: list_of_foreign_tables.remove('SIN DATOS') 
    list_primary_table_global_modified = [item for item in list_primary_table_global if item not in list_of_primary_tables]
    
    if type_data == 'ALL':
        file_name = 'FILE_'+sub_domain+'.ddl'
    else:
        file_name = 'FILE_'+sub_domain+'_'+type_data+'.ddl'   
        
    with open(file_name, "w") as file:
            foreign = []
            foreign_table = []
            #filling the main tables from KYD file
            for table, group in df.groupby("table"):
                file.write("CREATE TABLE K2_{} (\n".format(table))
                fields = [] 
                lenght = len(list(group.itertuples()))
                last = ""
                for i,row in enumerate(group.itertuples()):
                    
                    if i+1 < lenght:
                        last = ",\n"
                    else:
                        last = ""
                    file.write("{indent}{field} {indent}{type} {indent}{is_null}{last_val}".format(indent = indent,
                                                                                                     field = row.field.upper(),
                                                                                                     type = row.type.upper(),
                                                                                                     is_null = row.is_null.upper(), 
                                                                                                     last_val = last))
                    
                    #Check for primary key
                    if(row.key_pk.upper() in ispk):
                        fields.append(row.field.upper())
                    
                    #Check for foreign key
                    if(row.key_fk.upper() == 'SI'):
                        if row.table_fk in list_primary_table_global:
                            foreign.append([row.table.upper(), 
                                            row.field.upper(),
                                            row.table_fk.upper(),
                                            row.field_fk.upper()])
            
                if len(fields) >= 1:
                    file.write(",\n{indent}PRIMARY KEY ({field})".format(indent = indent,
                                                                           field = ",".join(fields)))
          
                file.write("\n);\n\n")

            #filling the foreign tables from KYD file
            for table, group in df[(df['key_fk'] == 'SI')].groupby('table_fk'):
                table = table.upper().replace(" ", "_")
                if table in list_of_foreign_tables:
                    if table in list_primary_table_global:
                        file.write("CREATE TABLE K2_{} (\n".format(table))
                    else:
                        file.write("CREATE TABLE #{} (\n".format(table))
                
                    last = ""
                    ckeck_PK = []
                    rows = []
                
                    # Remove identical rows from group
                    for row in group.itertuples():
                        rows.append([row.field_fk.upper(), row.type.upper(), row.is_null.upper()])
                    rows_new = []
                    for elem in rows:
                        if elem not in rows_new:
                            rows_new.append(elem)
                    length_row = len(rows_new)
                    for j, row in enumerate(rows_new):
                        if j+1 < length_row:
                            last = ",\n"
                        else:
                            last = ""
                        file.write("{indent}{field_fk} {indent}{type} {indent}{is_null}{last_val}".format(indent = indent,
                                                                                                            field_fk = row[0],
                                                                                                            type = row[1],
                                                                                                            is_null = row[2], 
                                                                                                            last_val = last))
                    
                    
                        ckeck_PK.append(row[0])
                        ckeck_PK = [*set(ckeck_PK)]
                    if len(ckeck_PK) >= 1:
                        file.write(",\n{indent}PRIMARY KEY ({field_fk})".format(indent = indent, 
                                                                           field_fk = ",".join(ckeck_PK)))
                
                    #Check for foreign key from outside table
                    for j, row in enumerate(group.itertuples()):
                        if((row.key_fk.upper() == 'SI')&(row.table_fk.upper().replace(" ","_") not in list_primary_table_global_modified)):
                            foreign_table.append([row.table, 
                                                  row.field,
                                                  row.table_fk,
                                                  row.field_fk])                        
                    
                    file.write("\n);\n\n")
                
            # foreign key section
            if len(foreign) >= 1:
                for line in foreign:
                    file.write('ALTER TABLE K2_{origin_table} ADD FOREIGN KEY ({origin_field}) REFERENCES K2_{table_fk} ({field_fk}) \n\n'.format(origin_table = line[0], 
             origin_field = line[1],  
             table_fk = line[2],
             field_fk = line[3])) 
                    
            if len(foreign_table) >= 1:
                for line in foreign_table:
                    file.write('ALTER TABLE K2_{origin_table} ADD FOREIGN KEY ({origin_field}) REFERENCES #{table_fk} ({field_fk}) \n\n'.format(origin_table = line[0], 
             origin_field = line[1],  
             table_fk = line[2],
             field_fk = line[3])) 
                    
    type_data_name = sensitive_data_name(type_data)                
    
    if type_data == 'ALL':
        st.write(r'$\checkmark$:  Archivo FILE_'+sub_domain+'.ddl con datos '+type_data_name+' creado satisfactoriamente!')
    else:
        st.write(r'$\checkmark$:  Archivo FILE_'+sub_domain+'_'+type_data+'.ddl con datos '+type_data_name+' creado satisfactoriamente!')

    st.write('Archivo contiene: {} Tablas principales y {} Tablas foraneas'.format(len(list_of_primary_tables), len(list_of_foreign_tables)))
    return 

        
#Entry point app
if __name__ == '__main__':
    
    st.title('Generador de DDL')
    st.write('Convierte tu Excel Know Your Data en un script de tipo ddl que usarás luego para crear el modelo Erwin.')
    st.write('El formato de tu Know Your Data debe respetar la estructura según el template original para que este convertidor funcione.')
    st.write("El archivo KYD debe contener las hojas 'Diccionario de Datos' y 'Migration' para su correcto funcionamiento.")
    
    #File uploader
    file = st.file_uploader("Por favor elige un archivo Excel")
    
    if file is not None:
        #Check existance of spreadsheets in excel file
        check_sheets = check_sheets_existance(file)
        
        if check_sheets:
            #find excel tables
            check_table, ind_kyd, ind_mig = find_tables(file)
        
            if check_table:
                #load excel file
                df, df_mig = load_excel(file, ind_kyd, ind_mig)
            
                # Several cross checks to make sure file KYD is OK
                df, status_ckeck_KYD = status_check_of_KYD(df, ind_kyd)
            
                # Several cross checks to make sure file KYD is OK
                df_mig, status_ckeck_Migration = status_check_of_Migration(df_mig)

                if (status_ckeck_KYD & status_ckeck_Migration):          
                    #checking missing values
                    list_cols_with_md = show_missing_data(df, ind_kyd, 'KYD')
                    list_cols_with_mig = show_missing_data(df_mig, ind_mig, 'Migration')
        
                    #replace missing values
                    if list_cols_with_md:
                        df = replace_missing_values(df, list_cols_with_md)
                    
                    #replace missing values
                    if list_cols_with_mig:
                        df_mig = replace_missing_values(df_mig, list_cols_with_mig)
                    
                    #transform text upper case, remove several empty spaces and change ' ' by _
                    df = transform_text(df)
                    df_mig = transform_text_migration(df_mig)
            
                    #add rows related to lead_ts field coming from MIGRATION spreadsheet
                    df = fill_load_ts(df, df_mig)
 
                    #Change cell values for some columns with a standard one 
                    df = standarize_data_on_columns(df) 
        
                    #fill foreign field parameter 
                    df = fill_field_fk_parameters(df)
            
                    #check final dataframe
                    st.write('### Vista final datos en archivo KYD')
                    st.dataframe(df.astype(str)) 
                
                    list_subdom = check_subdominio(df_mig)
                    list_primary_table_global = df['NOMBRE LÓGICO TABLA'].unique()
                
                    if len(list_subdom) < 2:
                        answer_dominio = 'NO'
                    else:
                        st.write("¿Desea separar el modelo por sub-dominio? (SI/NO) (escribir en terminal)")
                        answer_dominio = question()
                
                    if answer_dominio.upper() == 'NO':     
                        st.write("¿Desea separar el modelo dependiendo del la sensibilidad de los datos? (SI/NO) (escribir en terminal)")
                        answer = question()
                        sd_name = 'ALL_DOMAINS'
            
                        if answer.upper() == 'NO':     
                            write_ddl_file(df, sd_name, 'ALL', list_primary_table_global)
                            create_modified_excel_file(df, sd_name, 'ALL')
                        else:     
                            df_hs, df_se, df_ns = split_on_sensitibity(df)
                 
                            write_ddl_file(df_hs, sd_name, 'HS', list_primary_table_global)
                            create_modified_excel_file(df_hs, sd_name, 'HS')    
                    
                            write_ddl_file(df_se, sd_name, 'SE', list_primary_table_global)
                            create_modified_excel_file(df_se, sd_name, 'SE')
                    
                            write_ddl_file(df_ns, sd_name, 'NS', list_primary_table_global)
                            create_modified_excel_file(df_ns, sd_name, 'NS')

                        #show corporate image
                        image = Image.open('Gobierno_Datos.png')
                        st.image(image, caption='Gobierno de Datos')
                    
                    if answer_dominio.upper() == 'SI':
                        df_subdomains = split_on_subdominio(df, df_mig)  
                        st.write("¿Desea separar el modelo dependiendo del la sensibilidad de los datos? (SI/NO) (escribir en terminal)")
                        answer = question()
                    
                        if answer.upper() == 'NO':
                            for sb in df_subdomains:
                                sd_name = sb[0]
                                sd_df = sb[1]
                                write_ddl_file(sd_df, sd_name, 'ALL', list_primary_table_global)
                                create_modified_excel_file(sd_df, sd_name, 'ALL')
                        else:
                            for sb in df_subdomains:
                                sd_name = sb[0]
                                sd_df = sb[1]
                                df_hs, df_se, df_ns = split_on_sensitibity(sd_df)
                 
                                write_ddl_file(df_hs, sd_name, 'HS', list_primary_table_global)
                                create_modified_excel_file(df_hs, sd_name, 'HS')    
                    
                                write_ddl_file(df_se, sd_name, 'SE', list_primary_table_global)
                                create_modified_excel_file(df_se, sd_name, 'SE')
                    
                                write_ddl_file(df_ns, sd_name, 'NS', list_primary_table_global)
                                create_modified_excel_file(df_ns, sd_name, 'NS')
                else:
                    st.write('### Terminando programa') 
                    #show corporate image
                    image = Image.open('Gobierno_Datos.png')
                    st.image(image, caption='Gobierno de Datos')    
                
            else:
                st.write('### Terminando programa') 
                #show corporate image
                image = Image.open('Gobierno_Datos.png')
                st.image(image, caption='Gobierno de Datos')
        else:
            st.write('### Terminando programa') 
            #show corporate image
            image = Image.open('Gobierno_Datos.png')
            st.image(image, caption='Gobierno de Datos')
    else:
        #show corporate image
        image = Image.open('Gobierno_Datos.png')
        st.image(image, caption='Gobierno de Datos')
            