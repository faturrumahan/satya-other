from flask import Flask, jsonify, request, make_response, Response
from flask_cors import CORS
import requests
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64

import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)
app.config["DEBUG"] = True
#load data from database

def spk_mod(selected) :
    # get list posisi
    posisi = requests.get('http://127.0.0.1:4000/posisi').json()
    posisi_array = [item['nama'] for item in posisi['data']]

    # get list kriteria
    kriteria = requests.get('http://127.0.0.1:4000/kriteria').json()

    # add kecocokan_jurusan criteria
    kecocokan_jurusan = {
        'id': 99,
        'nama': 'kecocokan_jurusan',
        'tipe': 'benefit',
        'kepentingan': 'sangat penting',
        'created_at': None,
        'updated_at': None
    }
    kriteria['data'].append(kecocokan_jurusan)
    crit = kriteria['data']

    #df kriteria
    crit_df = pd.DataFrame(crit)
    crit_df = crit_df.drop(['id', 'tipe', 'created_at', 'updated_at'], axis=1)

    # get data alternatif
    response=requests.get('http://127.0.0.1:4000/hasil/alternatif').json()
    df=pd.DataFrame(response['data'])

    # split
    df = df.applymap(lambda x: x.split(',') if isinstance(x, str) else x)
    column_headers = list(df.columns.values)
    for i in range(len(column_headers)) :
        df = df.explode(column_headers[i]).reset_index(drop=True)

    # get data nilai jurusan
    response_2=requests.get('http://127.0.0.1:4000/hasil/jurusan').json()
    df_2=pd.DataFrame(response_2['data'])
    df_2 = df_2.drop(['id'], axis=1)
    melted_df = pd.melt(df_2, id_vars='nama_jurusan', var_name='posisi', value_name='kecocokan_jurusan')

    merged_df = pd.merge(df, melted_df, on=['nama_jurusan', 'posisi'], how='left')

    spk_df = merged_df.drop(['nama', 'nama_jurusan', 'posisi'], axis=1)

    # normalisasi kriteria
    for column in spk_df.columns: 
        for index, kriteria in enumerate(crit):
            # display(crit[index]['tipe'])
            if (column == crit[index]['nama']):
                if (crit[index]['tipe'] == 'benefit'):
                    spk_df[column] = spk_df[column]  / spk_df[column].abs().max()
                else:
                    spk_df[column] = spk_df[column]  / spk_df[column].abs().min()
    
    #replace tingkat kepentingan
    dict = {"sangat kurang penting" : '1', "kurang penting" : '2', "menengah": '3', "penting" : '4', "sangat penting": '5'}
    crit_df = crit_df.replace({'kepentingan': dict})

    #perbaikan bobot
    crit_df['kepentingan'] = crit_df['kepentingan'].astype(float)
    total_kepentingan = crit_df['kepentingan'].sum()
    crit_df['kepentingan'] = crit_df['kepentingan'] / total_kepentingan

    #transpose df
    crit_df = crit_df.set_index('nama').T

    # vektor S
    common_columns = []
    for column in spk_df.columns: 
        common_columns.append(column)
    spk_df = spk_df[common_columns]
    crit_df = crit_df[common_columns]
    df_result = spk_df ** crit_df.iloc[0]
    result_value = df_result.prod(axis=1)

    result_spk = merged_df[['nama', 'nama_jurusan', 'posisi']].copy()
    result_spk = result_spk.assign(skor=result_value/result_value.sum())
    result_spk = result_spk.sort_values(by=['skor'], ascending=False)

    if(selected != 'all'):
        for item in posisi_array:
            if(item != selected):
                result_spk = result_spk.drop(result_spk[result_spk['posisi'] == item].index)
    else:
        result_spk = result_spk.drop_duplicates(subset=["nama"])
    
    return(result_spk)

def spk_saw(selected) :
    # get list posisi
    posisi = requests.get('http://127.0.0.1:4000/posisi').json()
    posisi_array = [item['nama'] for item in posisi['data']]

    # get list kriteria
    kriteria = requests.get('http://127.0.0.1:4000/kriteria').json()

    # add kecocokan_jurusan criteria
    kecocokan_jurusan = {
        'id': 99,
        'nama': 'kecocokan_jurusan',
        'tipe': 'benefit',
        'kepentingan': 'sangat penting',
        'created_at': None,
        'updated_at': None
    }
    kriteria['data'].append(kecocokan_jurusan)
    crit = kriteria['data']

    #df kriteria
    crit_df = pd.DataFrame(crit)
    crit_df = crit_df.drop(['id', 'tipe', 'created_at', 'updated_at'], axis=1)

    # get data alternatif
    response=requests.get('http://127.0.0.1:4000/hasil/alternatif').json()
    df=pd.DataFrame(response['data'])

    # split
    df = df.applymap(lambda x: x.split(',') if isinstance(x, str) else x)
    column_headers = list(df.columns.values)
    for i in range(len(column_headers)) :
        df = df.explode(column_headers[i]).reset_index(drop=True)

    # get data nilai jurusan
    response_2=requests.get('http://127.0.0.1:4000/hasil/jurusan').json()
    df_2=pd.DataFrame(response_2['data'])
    df_2 = df_2.drop(['id'], axis=1)
    melted_df = pd.melt(df_2, id_vars='nama_jurusan', var_name='posisi', value_name='kecocokan_jurusan')

    merged_df = pd.merge(df, melted_df, on=['nama_jurusan', 'posisi'], how='left')

    spk_df = merged_df.drop(['nama', 'nama_jurusan', 'posisi'], axis=1)

    # normalisasi kriteria
    for column in spk_df.columns: 
        for index, kriteria in enumerate(crit):
            # display(crit[index]['tipe'])
            if (column == crit[index]['nama']):
                if (crit[index]['tipe'] == 'benefit'):
                    spk_df[column] = spk_df[column]  / spk_df[column].abs().max()
                else:
                    spk_df[column] = spk_df[column]  / spk_df[column].abs().min()
    
    #replace tingkat kepentingan
    dict = {"sangat kurang penting" : '1', "kurang penting" : '2', "menengah": '3', "penting" : '4', "sangat penting": '5'}
    crit_df = crit_df.replace({'kepentingan': dict})

    #perbaikan bobot
    crit_df['kepentingan'] = crit_df['kepentingan'].astype(float)
    crit_df['kepentingan'] = crit_df['kepentingan'] / 10

    #transpose df
    crit_df = crit_df.set_index('nama').T

    # pemeringkatan
    common_columns = []
    for column in spk_df.columns: 
        common_columns.append(column)
    spk_df = spk_df[common_columns]
    crit_df = crit_df[common_columns]
    df_result = spk_df * crit_df.iloc[0]
    result_value = df_result.sum(axis=1)

    result_spk = merged_df[['nama', 'nama_jurusan', 'posisi']].copy()
    result_spk = result_spk.assign(skor=result_value)
    result_spk = result_spk.sort_values(by=['skor'], ascending=False)

    if(selected != 'all'):
        for item in posisi_array:
            if(item != selected):
                result_spk = result_spk.drop(result_spk[result_spk['posisi'] == item].index)
    else:
        result_spk = result_spk.drop_duplicates(subset=["nama"])
    
    return(result_spk)

@app.route('/mod/<selected>', methods=['GET'])
def data(selected) :
    df=spk_mod(selected.replace("%20", " "))

    result = df.to_json(orient="table")
    response = json.loads(result)
    return response

@app.route('/saw/<selected>', methods=['GET'])
def atad(selected) :
    df=spk_saw(selected.replace("%20", " "))

    result = df.to_json(orient="table")
    response = json.loads(result)
    return response
app.run()