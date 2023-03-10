import streamlit as st  # pip install streamlit
import pandas as pd  # pip install pandas
import numpy as np  # pip install numpy
from PIL import Image
import keyword
from tabulate import tabulate

### Library of functions ###
def check_sheets_existence(file):
    ''' Checks for the existence of necessary sheets in the excel file. 
        In case one of the 2 sheets is not found the output will be False and the program will ends '''
    
    check_file = pd.ExcelFile(file)
    list_of_sheets = check_file.sheet_names
    needed_sheets = ['Models','KYD','Migration'] 
    check = [sheet for sheet in needed_sheets if sheet in list_of_sheets]
    not_found_sheets = [sheet for sheet in needed_sheets if sheet not in check]
    if len(check) == len(needed_sheets):
        return True
    else:
        st.write("No se encontró la hoja de cálculo '{}'. Verificar archivo KYD !!!".format(not_found_sheets[0]))
        return False
    
def find_skiprows_on_excel(file, name, cols_table): 
    ''' Find de integer where the table on sheet starts, based on the list of columns as inputs.
        In case the table is not found the output will be False, otherwise the output will be True and the row number where the table starts will be provided '''
    
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
   
def find_skiprows_on_excel_for_readme(file, name):
    ''' Find the information header needed to build the readme file '''
    
    cols_read = ['DOMAIN',
                 'SUB-DOMINIO',
                 'DATA OWNER',
                 'DATA STEWARD',
                 'TECHNICAL DATA STEWARD',
                 'DATA SET TARGET',
                 'DATA RETENTION PERIOD (Months)',
                 'AD GROUP',
                 'UNIX GROUP',
                 'DATA SOURCE / DATABASE',
                 'CANTIDAD DATA ELEMENT']
  
    #Rename column names
    df = pd.read_excel(file, sheet_name = name , header=0) 
    for i, col in enumerate(df.columns):
        df = df.rename(columns={col:i})
    
    col_table = []
    for col in df.columns:
        for i in range(0, len(df), 1):
            for val in cols_read:
                if val == str(df.at[i, col]):
                    col_table.append(int(col))
    
    selected_col = max(set(col_table), key=col_table.count)
    
    name = []
    valor = []
    for i in range(0, len(df), 1):
        for val in cols_read:
            if val == str(df.at[i, selected_col]):
                name.append(val)
                valor.append(str(df.at[i, selected_col+1]))
    
    encabezado = dict(zip(name, valor))            
    
    mising_names = [name for name in encabezado.keys() if encabezado[name] == 'nan']
    
    if len(mising_names) == 0:
        st.write(r'$\checkmark$:  Campos encontrados correctamente !!!')
        return True, encabezado
    else:
        st.write(r'$\otimes$:  Falta información en los siguientes campos !!!')
        st.dataframe(mising_names)
        return False, [] 

def load_excel(file, ind_kyd, ind_mig):
    ''' Imports excel file and load the data stored in each sheet, based on the integer provided.
        The output will be 3 dataframes: Models, Diccionario de Datos and Migration '''
    
    #Read data from sheets and skip first n rows of the excel file
    df_Models = pd.read_excel(file, sheet_name='Models', header=0, skiprows=2)
    df_KYD = pd.read_excel(file, sheet_name='KYD' , header=0, skiprows=ind_kyd)
    df_Migration = pd.read_excel(file, sheet_name='Migration' , header=0, skiprows=ind_mig)
    
    return df_Models, df_KYD, df_Migration

def clean_dataframes(df_Models, df_KYD, df_Migration):
    ''' Remove columns not relevant to the analysis'''
    
    #Erase all irrelevant calumns from df_Models
    columns_to_be_erased = ['Unnamed:',
                            'Alternate',
                            'Index',
                            'Constraint',
                            'Dimensional',
                            'Inversion',
                            'Level',
                            'Description',
                            'Comment',
                            'Default',
                            'All (no filter)',
                            'View',
                            'Type']
    
    for colum in columns_to_be_erased:
        column_name = [col for col in df_Models.columns if colum not in col]
        df_Models = df_Models[column_name]
    
    #Erase all calumns that contain Unnamed
    column_name = [col for col in df_KYD.columns if 'Unnamed:' not in col]
    df_KYD = df_KYD[column_name]
    
    #Erase all columns that containt Unnamed
    column_name = [col for col in df_Migration.columns if 'Unnamed:' not in col]
    df_Migration = df_Migration[column_name]
    
    return df_Models, df_KYD, df_Migration

def check_columns_existence_KYD(df):
    ''' Verifies the existence of specific columns on excel file based on the input list. 
        In case any of the columns is not found the output will be False and will show which colum is missing,
        otherwise the output will be True '''
    
    # remove empty spaces in column names
    for col in df.columns:
        df = df.rename(columns={col:remove_empty_spaces(col)})

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
        
    #Check existence of column name listed above and rename it
    match = []
    for col1 in columnas:
        for col2 in df.columns:
            if col1 in col2:
                match.append(col1)
                df = df.rename(columns={col2:col1})
                
    missing_columns = [col for col in columnas if col not in match]
  
    if len(match) == len(columnas):
        st.write(r'$\checkmark$:  Validación nombre de columnas en KYD !!!')
        return True, df
    else:          
        st.write(r"$\otimes$:  Existen columnas con nombres distintos en archivo 'KYD' !!!")
        st.write("Revisar columnas en archivo 'KYD' para seguir con el proceso")
        st.write(" '{}' columna no encontrada".format(missing_columns[0]))
        return False, df

def check_columns_existence_Migration(df):
    ''' Verifies the existence of specific columns on excel file based on the input list. 
        In case any of the columns is not found the output will be False and will show which colum is missing,
        otherwise the output will be True '''
    
    # remove empty spaces in column names
    for col in df.columns:
        df = df.rename(columns={col:remove_empty_spaces(col)})

    #columns to be check
    columnas = ['NOMBRE DE LA TABLA',
                'TIPO DE CARGA',
                'PERIODICIDAD DE CARGA',
                'CANTIDAD DE DIAS A EXTRAER EN LA CARGA',
                'COLUMNA DE FILTRADO']
        
    #Check existence of column name listed above and rename it
    match = []
    for col1 in columnas:
        for col2 in df.columns:
            if col1 in col2:
                match.append(col1)
                df = df.rename(columns={col2:col1})
                
    missing_columns = [col for col in columnas if col not in match]
  
    if len(match) == len(columnas):
        st.write(r'$\checkmark$:  Validación nombre de columnas en Migration !!!')
        return True, df
    else:          
        st.write(r"$\otimes$:  Existen columnas con nombres distintos en archivo 'Migration' !!!")
        st.write("Revisar columnas en archivo 'Migration' para seguir con el proceso")
        st.write(" 'Migration' columna no encontrada".format(missing_columns[0]))
        return False, df   

def show_fk_tables_without_name(df):
    ''' Check if a foreign key field has asigned a table name '''
    
    cut_fk = (df['key_type_fk'] == 'FK')
    cut_name_fk = ((df['source2_fk'] == 'SIN DATOS')|(df['source2_fk'].isna()))
    
    nameless_tables = df[cut_fk&cut_name_fk][['TableName','Name','B_AttriName']]
    
    ## Detect position in KYD
    position = []
    for i,row in enumerate(nameless_tables.itertuples()):
        position.append(nameless_tables.index[i])
    nameless_tables['posición'] = position
    
    if len(nameless_tables) == 0:
        st.write(r'$\checkmark$:  No existen campos foreign key sin nombre en YAML !!!')
        return
    else:
        st.write(r"$!$  :  Se detectaron campos foreign key sin nombre en YAML !!!")
        st.write("Esto genera campos foráneos sin source en archivo file.yaml")
        st.dataframe(nameless_tables.astype(str))
        return
    
def find_tables(file):
    ''' Finds the number of rows where the tables are in respectives sheets based on the columns names listed for each case. 
        In case one of the 2 tables is not found the output will be False and the program will ends, otherwise the output will be True and the row number where each table starts will be provided '''
    
    cols_kyd = ['FUENTE ORIGEN','TABLA / DATASET / TÓPICO A MIGRAR','NOMBRE DE LA TABLA EN ORIGEN']        
    cols_mig = ['NOMBRE DE LA TABLA','TIPO DE CARGA','PERIODICIDAD DE CARGA']
    
    check_kyd, ind_kyd = find_skiprows_on_excel(file, 'KYD', cols_kyd)
    check_mig, ind_mig = find_skiprows_on_excel(file, 'Migration', cols_mig)
    check_rdm, head_readme = find_skiprows_on_excel_for_readme(file, 'Migration')
    
    if (check_kyd & check_mig & check_rdm):
        return True, ind_kyd, ind_mig, head_readme
    else:
        return False, ind_kyd, ind_mig, head_readme
    
def rename_columns_from_models(df):
    ''' Rename specific columns '''
    
    df['TableName']       = df['Name.2']
    df['B_TableName']     = df['Business Name'] 
    df['Name']            = df['Name.3']
    df['B_AttriName']     = df['Business Name.1'] 
    df['Native_DataType'] = df['Native Name'] 
   
    columns_to_keep = ['TableName','B_TableName','Name','B_AttriName','Native_DataType']
    df = df[columns_to_keep]
    return df

def transform_text_migration(df):
    ''' Transform all values on the list of columns listed above applying:
         - lower to upper case
         - removing first and last empty space
         - change space in between with _ '''
    
    list_of_cols_to_consider = ['NOMBRE DE LA TABLA',
                                'TIPO DE CARGA',
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

def fill_nan_with_table_name(df, col):
    ''' In the process of merging KYD with Model dataframes this function fill the empty values el the col with the first non empty previous value found'''
    for i,row in enumerate(df[col]):
        if (row != 'NAN'):
            table_name = row
        else:
            df.at[i, col] = table_name
    return df
    
def merge_info_from_KYD_and_Model(df_KYD, df_Models):
    ''' Do the match between KYD table and Erwin output table'''

    #Replace nan values per NULL 
    df_KYD[['¿PUEDE SER NULO?']] = df_KYD[['¿PUEDE SER NULO?']].replace(np.nan, 'NULL')
       
    #Remove special characters (k2_, #) from TableName
    df_Models['B_TableName'] = df_Models['B_TableName'].apply(remove_special_symbols)
 
    #Recognize foreign tables comming from KYD file
    list_foreign_tables = df_KYD[df_KYD['LLAVE FK'] == 'SI']['NOMBRE DE LA TABLA FK'].unique().tolist()
    foreign_tables = df_Models[df_Models['B_TableName'].isin(list_foreign_tables)]
    #if len(foreign_tables) != 0: 
    #    st.write('Se encontraron {} tablas foraneas'.format(len(foreign_tables)))
    #else:
    #    st.write('No se encontraron tablas foraneas')
        
    #Fill NAN values with table names 
    df_Models = fill_nan_with_table_name(df_Models, 'B_TableName')
    
    #Fill missing cells with table names 
    df_Models = df_Models.ffill()
    
    df_Models['col_merge_A'] = df_Models['B_TableName']
    df_Models['col_merge_B'] = df_Models['B_AttriName']  
    
    df_KYD['col_merge_A'] = df_KYD['NOMBRE LÓGICO TABLA']
    df_KYD['col_merge_B'] = df_KYD['NOMBRE LÓGICO DEL CAMPO']
    
    #st.write('## Models')
    #st.dataframe(df_Models)
    #st.write('## KYD')
    #st.dataframe(df_KYD)
    #st.write('## Foreign tables')
    #st.dataframe(foreign_tables)
    
    df = pd.merge(df_Models, df_KYD, on=('col_merge_A','col_merge_B'), how='inner')
    
    df = df.rename(columns={'FUENTE ORIGEN':'source',
                            'TABLA / DATASET / TÓPICO A MIGRAR':'source2',
                            'NOMBRE LÓGICO TABLA':'table_name',
                            'NOMBRE DEL CAMPO EN EL ORIGEN':'source3',
                            'DESCRIPCIÓN CAMPO':'Description',
                            'LLAVE PK':'key_type_pk',
                            'LLAVE FK':'key_type_fk',
                            '¿PUEDE SER NULO?':'nullable',
                            'CLASIFICACIÓN DE DATOS':'pii'})
    
    columns_to_keep = ['TableName',
                       'table_name',
                       'B_TableName',
                       'Name',
                       'B_AttriName',
                       'Native_DataType',
                       'source',
                       'source2',
                       'source3',
                       'Description',
                       'key_type_pk',
                       'key_type_fk',
                       'nullable',
                       'pii']
    
    df = df[columns_to_keep]
    
    #Change cell values for key_type_pk and key_type_fk
    df['key_type_pk'] = np.where( (df['key_type_pk'] == 'SI'), 'PK', df['key_type_pk'] )
    df['key_type_pk'] = np.where( (df['key_type_pk'] == 'SIN DATOS'), 'NO', df['key_type_pk'] )
    
    df['key_type_fk'] = np.where( (df['key_type_fk'] == 'SI'), 'FK', df['key_type_fk'] )
    df['key_type_fk'] = np.where( (df['key_type_fk'] == 'SIN DATOS'), 'NO', df['key_type_fk'] )
   
    #find primary key fields
    df_pk = df[df['key_type_pk'] == 'PK'].rename(columns={'source':'source_fk',
                                                          'source2':'source2_fk',
                                                          'source3':'source3_fk'})
    
    #find load_ts fields
    df_loadts = df[df['Name'] == 'LOAD_TS'].rename(columns={'source':'source_fk',
                                                            'source2':'source2_fk',
                                                            'source3':'source3_fk'})
    
    
    df_foreign = foreign_tables[['TableName','Name','B_TableName','B_AttriName']]
    df_foreign['TableName'] = df_foreign['TableName'].apply(remove_gato_symbol)
    #df_foreign = df_foreign.rename(columns={'B_TableName':'source2_fk','B_AttriName':'source3_fk'})
    df_foreign = df_foreign.rename(columns={'TableName':'source2_fk','B_AttriName':'source3_fk'})
    
    #create and fill with 'SIN DATOS' source_fk columns to avoid bug in write_yaml_file
    df['source_fk'] = 'SIN DATOS'
    df['source2_fk'] = 'SIN DATOS'
    df['source3_fk'] = 'SIN DATOS'
    
    #st.write('## DF merged')
    #st.dataframe(df)
    #st.write('## Primary tables')
    #st.dataframe(df_pk)
    #st.write('## Foreign tables')
    #st.dataframe(df_foreign)
    #st.write('## Load TS')
    #st.dataframe(df_loadts)
    
    #Fill source of primary fields 
    for index, row in df_pk[['Name','source_fk','source2_fk','source3_fk']].iterrows():
        cut = ((df['key_type_fk'] == 'FK')&(df['Name'] == row.Name))
        df.loc[cut, 'source_fk'] = row.source_fk
        df.loc[cut, 'source2_fk'] = row.source2_fk
        df.loc[cut, 'source3_fk'] = row.source3_fk
        
    #Fill source of foreign fields    
    for index, row in df_foreign[['Name','source2_fk','source3_fk']].iterrows():
        cut = ((df['key_type_fk'] == 'FK')&(df['Name'] == row.Name))
        #df.loc[cut, 'source_fk'] = row.source_fk
        df.loc[cut, 'source2_fk'] = row.source2_fk
        df.loc[cut, 'source3_fk'] = row.source3_fk
    
    st.write('### Vista final datos')
    columns_to_keep = ['TableName',
                       'B_TableName',
                       'Name',
                       'B_AttriName',
                       'Native_DataType',
                       'source',
                       'source2',
                       'source3',
                       'key_type_pk',
                       'key_type_fk',
                       'nullable',
                       'pii',
                       'source2_fk',
                       'source3_fk',
                       'Description']
    df = df[columns_to_keep]
    st.dataframe(df)
    
    return df

def remove_empty_spaces(text):
    ''' Remove first, last and several in between empty space from string '''
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

def remove_special_symbols(text):
    ''' Remove first and last empty space from string '''
    text = str(text)
    text = "".join(text.upper().replace("#", ""))
    text = "".join(text.upper().replace("K2_", ""))
    text = text.replace("_HS", "")
    text = text.replace("_SE", "")
    text = text.replace("_NS", "")
    return text
                                                              
def remove_gato_symbol(text):
    ''' Remove # from string '''
    text = str(text)
    text = "".join(text.upper().replace("#", ""))
    return text

def write_readme(df, dict_info, migration):
    ''' Create README.MD file '''
    
    df_tabla = df.copy()
    df_load = df.copy()
    df_mig = migration.copy()
    
    #Select only columns that matters and remove duplicated values
    df_tabla = df_tabla[['TableName','B_TableName']]
    df_tabla = df_tabla.rename(columns={'B_TableName':'NOMBRE DE LA TABLA'})
    df_tabla = df_tabla.drop_duplicates()
    
    #Select tables with load_ts fields
    df_load = df_load[df_load['Name'] == 'LOAD_TS']['TableName'].tolist()
    
    #Merge KYD with Migration
    df_final = pd.merge(migration, df_tabla, on=('NOMBRE DE LA TABLA'), how='inner')
    df_final = df_final.rename(columns={'TableName':'Tabla',
                                        'TIPO DE CARGA (Incremental/Bulk)':'Tipo Carga',
                                        'PERIODICIDAD DE CARGA':'Periodicidad'})
    
    df_final = df_final[['Tabla','Tipo Carga','Periodicidad']]
    
    #Assign incremental value for load_ts tables
    for tabla in df_final['Tabla'].tolist():
        cut = (df_final['Tabla'] == tabla)
        if tabla in df_load:
            df_final.loc[cut, 'Tipo Carga'] = df_final.loc[cut, 'Tipo Carga'] +str('(last_change_ts)')
        else:
            df_final.loc[cut, 'Tipo Carga'] = df_final.loc[cut, 'Tipo Carga'] +str('(last_update_ts)')
    
    #Needed information
    governance_list = ['DOMAIN','SUB-DOMINIO','DATA OWNER','DATA STEWARD','TECHNICAL DATA STEWARD']
    dataset_target_list = ['DATA SET TARGET']
    ad_group_list = ['AD GROUP']
    
    indent1 = " "
    indent2 = "  "
    
    with open("ReadME.md", "w") as file: 
        ##############################
        file.write('## GOVERNANCE \n')
        for val in governance_list:
            file.write('{indent2}- {val}: {info_val}'.format(indent2 = indent2,
                                                             val = val,
                                                             info_val = dict_info[val]))
            
            file.write("\n")
        file.write("\n\n")
        ##############################
        file.write('## DATA SOURCE \n')
        file.write("\n\n")
        ##############################
        file.write('## DATASET TARGET \n')
        for val in dataset_target_list:
            file.write('{indent2}- {val}: {info_val}'.format(indent2 = indent2,
                                                             val = val,
                                                             info_val = dict_info[val]))
            
            file.write("\n")
        file.write("\n\n")
        ##############################
        file.write('## DATA ELEMENT \n')
        for table, group in df.groupby("TableName"):
            file.write("{indent2}- {table}{indent2}:{indent1}{number} \n".format(table = table, 
                                                                                 indent1 = indent1,
                                                                                 indent2 = indent2,
                                                                                 number = len(group)))
        
        file.write('{indent2}- Total{indent2}:{indent1}{number} \n'.format(indent1 = indent1, indent2 = indent2, number = len(df)))
        file.write("\n\n")
        ##############################
        file.write('## CONTACTO DEL DOMINIO \n')
        file.write("\n\n")
        ##############################
        file.write('## AD GROUP \n')
        for val in ad_group_list:
            file.write('{indent2}- {val}: {info_val}'.format(indent2 = indent2,
                                                             val = val,
                                                             info_val = dict_info[val]))
            
            file.write("\n")
        file.write("\n\n")
        ##############################
        file.write('## DENSIDAD/INYECCION DATOS \n')
        file.write(tabulate(df_final, headers='keys', tablefmt='psql', showindex=False))
        file.write("\n\n")
        
    st.subheader('El archivo ReadMe.md ha sido generado !!!') 
    

def write_yaml_file(df):
    ''' Generate .yaml file '''
    
    indent2 = "  "
    indent4 = "     "
    indents = " "*3
    indents2 = " "*3
    key="key"
    tipo="type"
    type="type"
    desc="desc"
    sensibilidad="pii"
    null="nullable"
    fuente="source"
    is_null=["NULL"]
    is_notnull=["NOT NULL"]
    # --is_pk=["PK"]
    # --is_fk=["FK"]

    with open("file.yaml", "w") as file:
        for table, group in df.groupby("TableName"):
            file.write("{}:\n".format(table.upper()))
            for row in group.itertuples():
                Name = row.Name.upper()
                key_type_pk = row.key_type_pk.upper()
                key_type_fk = row.key_type_fk.upper()
                Native_DataType = row.Native_DataType.upper()
                Description = row.Description
                pii = row.pii
                nullable = row.nullable
                source = '.'.join(str(x) for x in [row.source, row.source2, row.source3])
                source_fk = '.'.join(str(x) for x in [row.source2_fk, row.source3_fk])
                
                if ((key_type_pk == 'PK')&(key_type_fk == 'NO')):
                    if(Name == 'LOAD_TS'):
                        string = "{indent2}{Name}: \n {indents}{key}: \n {indent4}{tipo}: {key_type_pk} \n {indents}{type}: {Native_DataType}\n {indents2}{desc}: '{Description}'\n {indents}{sensibilidad}: {pii}\n {indents}{null}: {nullable}\n {indents}{fuente}: \n{indent4} static: GETDATE() #Fecha de Ingesta "
                        
                    else:
                        string = "{indent2}{Name}: \n {indents}{key}: \n {indent4}{tipo}: {key_type_pk} \n {indents}{type}: {Native_DataType}\n {indents2}{desc}: '{Description}'\n {indents}{sensibilidad}: {pii}\n {indents}{null}: {nullable}\n {indents}{fuente}: {source} "
                    file.write(string.format(indent2 = indent2, 
                                             Name = Name, 
                                             key = key, 
                                             indent4 = indent4, 
                                             tipo = tipo, 
                                             key_type_pk = key_type_pk, 
                                             indents = indents, 
                                             type = type, 
                                             Native_DataType = Native_DataType, 
                                             indents2 = indents2, 
                                             desc = desc, 
                                             Description = Description, 
                                             sensibilidad = sensibilidad, 
                                             pii = pii, 
                                             null = null, 
                                             nullable = nullable, 
                                             fuente = fuente, 
                                             source = source)) 
                    
                if ((key_type_pk == 'NO')&(key_type_fk == 'FK')):
                    if(Name == 'LOAD_TS'):
                        string = "{indent2}{Name}: \n {indents}{key}: \n {indent4}{tipo}: {key_type_fk} \n {indent4}{fuente}: {source_fk} \n {indents}{type}: {Native_DataType}\n {indents2}{desc}: '{Description}'\n {indents}{sensibilidad}: {pii}\n {indents}{null}: {nullable}\n {indents}{fuente}: \n{indent4} static: GETDATE() #Fecha de Ingesta" 
                    else:
                        string = "{indent2}{Name}: \n {indents}{key}: \n {indent4}{tipo}: {key_type_fk} \n {indent4}{fuente}: {source_fk} \n {indents}{type}: {Native_DataType}\n {indents2}{desc}: '{Description}'\n {indents}{sensibilidad}: {pii}\n {indents}{null}: {nullable}\n {indents}{fuente}: {source} " 
                        
                    file.write(string.format(indent2 = indent2, 
                                             Name = Name, 
                                             key = key, 
                                             indent4 = indent4,
                                             tipo = tipo, 
                                             key_type_fk = key_type_fk, 
                                             indents = indents, 
                                             type = type, 
                                             Native_DataType = Native_DataType, 
                                             indents2 = indents2, 
                                             desc = desc, 
                                             Description = Description,  
                                             sensibilidad = sensibilidad, 
                                             pii = pii, 
                                             null = null, 
                                             nullable = nullable, 
                                             fuente = fuente, 
                                             source = source, 
                                             source_fk = source_fk))
                
                if ((key_type_pk == 'NO')&(key_type_fk == 'NO')):
                    if(Name == 'LOAD_TS'):
                        string = "{indent2}{Name}: \n {indents}{type}: {Native_DataType}\n {indents2}{desc}: '{Description}'\n {indents}{sensibilidad}: {pii}\n {indents}{null}: {nullable}\n {indents}{fuente}: \n{indent4} static: GETDATE() #Fecha de Ingesta "
                    
                    else:
                        string = "{indent2}{Name}: \n {indents}{type}: {Native_DataType}\n {indents2}{desc}: '{Description}'\n {indents}{sensibilidad}: {pii}\n {indents}{null}: {nullable}\n {indents}{fuente}: {source} "
                    
                    file.write(string.format(indent2 = indent2, 
                                             Name = Name, 
                                             indents = indents, 
                                             type = type, 
                                             Native_DataType = Native_DataType, 
                                             indents2 = indents2, 
                                             desc = desc, 
                                             Description = Description, 
                                             sensibilidad = sensibilidad, 
                                             pii = pii, 
                                             null = null, 
                                             nullable = nullable, 
                                             fuente = fuente, 
                                             source = source,
                                             indent4 = indent4))                         
                file.write("\n")
                
    st.subheader('El archivo YAML ha sido generado con el nombre file.yaml!')
    
#Entry point app
if __name__ == '__main__':

    st.set_page_config(page_title='Generador de YAML')
    st.title('Generador de YAML  📈')
    st.subheader('Convierte tu archivo Models tipo excel en un script de tipo yaml que usarás luego para realizar el Pull Request')
    st.write('Antes de subir el archivo Models a esta automatización recuerda copiar las siguientes pestañas:')
    st.write('     - Hoja "KYD" del archivo excel generado por la automatización ddl')
    st.write('     - Hoja Migration" del archivo KYD original')

    #File uploader
    file = st.file_uploader("Por favor sube el archivo Excel extraído desde Erwin")

    if file is not None:
        #Check existence of spreadsheets in excel file
        check_sheets = check_sheets_existence(file)
        
        if check_sheets:
            #find excel tables
            check_table, ind_kyd, ind_mig, read_info = find_tables(file)
            
            if check_table:
                #load excel file
                df_Models, df_KYD, df_Migration = load_excel(file, ind_kyd, ind_mig)

                #Clean irrelevant columns
                df_Models, df_KYD, df_Migration = clean_dataframes(df_Models, df_KYD, df_Migration)
                
                #check existence of key columns
                check_KYD, df_KYD = check_columns_existence_KYD(df_KYD)
                check_Mig, df_Mig = check_columns_existence_Migration(df_Migration)
                
                if check_KYD & check_Mig:
        
                    #rename columns from Models
                    df_Models = rename_columns_from_models(df_Models)
                
                    #transform text upper case, remove several empty spaces and change ' ' by _
                    df_Migration = transform_text_migration(df_Migration)
                
                    # Merge KYD with Models
                    df = merge_info_from_KYD_and_Model(df_KYD, df_Models)
                    
                    #check foreign keys without source name
                    show_fk_tables_without_name(df)
                    
                    #write yaml file
                    write_yaml_file(df) 
                    
                    #write readme file
                    write_readme(df, read_info, df_Migration)
                    
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
    
