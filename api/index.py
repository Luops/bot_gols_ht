# vercel-python=python3

import requests
import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup
from urllib.request import urlopen, urlretrieve, Request
from urllib.error import URLError, HTTPError
from time import sleep
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])

def results():
  # Obter URL
  url = 'https://www.totalcorner.com/match/today'
  headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"}

  req = Request(url, headers=headers)
  response = urlopen(req)
  html = response.read()
  soup = BeautifulSoup(html,'html.parser')
  sleep(5)

  # Buscar tabela de dados
  lista = soup.find('table')

  dados = []
  linhas = lista.find_all('tr')  # Localizar todas as linhas da tabela
  for linha in linhas:
    # Localizar as células (colunas) da linha
    celulas = linha.find_all('td')
    linha_dados = []
    for celula in celulas:
      valor = celula.text.strip() if celula.text else ""  # Verificar se o texto da célula é None
      linha_dados.append(valor)
      dados.append(linha_dados)

  # Criar um DataFrame com os dados
  df = pd.DataFrame(dados)

  # Remover linhas vazias
  df.dropna(axis=1,how='all',inplace=True)

  # Remover colunas vazias
  df.dropna(axis=0,how='any',inplace=True)

  # Remover colunas
  df.drop(columns=[2, 12, 13], inplace=True)

  # Renomear colunas
  df.rename(columns={0: 'Numero do jogo', 1: 'Liga', 3: 'Tempo', 4: 'Time Casa', 5: 'Placar', 6: 'Time Fora', 7: 'Handicap', 8: 'Escanteios', 9: 'Linha de Gols', 10: 'Ataques Perigosos', 11: 'Chutes'}, inplace=True)

  # Converter tempo
  df['Tempo'] = df['Tempo'].apply(lambda a: 45 if a == 'Half' else a)
  df['Tempo'] = df['Tempo'].apply(lambda a: 0 if a == '' else a)
  df['Tempo'] = df['Tempo'].astype('int64')

  # Converter escanteios
  df['Escanteios'] = df['Escanteios'].apply(lambda a: re.findall(r'\d{1,} - \d{1,}',a))
  df['Escanteios'] = df['Escanteios'].apply(lambda a: list(map(int,a[0].split(' - '))) if a else [])

  # Converter Ataques Perigosos
  df['Ataques Perigosos'] = df['Ataques Perigosos'].apply(lambda a: re.findall(r'\d{1,} - \d{1,}',a))

  # Converter Placar
  df['Placar'] = df['Placar'].apply(lambda a: re.findall(r'\d{1,} - \d{1,}',a))

  # Converter Chutes
  df['Chutes'] = df['Chutes'].apply(lambda a: re.findall(r'\d{1,} - \d{1,}',a))

  # Remover valores nulos
  df['Ataques Perigosos'] = df['Ataques Perigosos'].apply(lambda a: a if a != [] else np.nan)
  df['Placar'] = df['Placar'].apply(lambda a: a if a != [] else np.nan)
  df['Chutes'] = df['Chutes'].apply(lambda a: a if a != [] else np.nan)
  df['Escanteios'] = df['Escanteios'].apply(lambda a: a if a != [] else np.nan)

  # Remover linhas vazias
  df.dropna(axis=0, how = 'any', inplace=True)

  # Converter Ataques Perigosos e Chutes
  df['Chutes'] = df['Chutes'].apply(lambda a: list(map(int,a[0].split(' - '))))
  df['Ataques Perigosos'] = df['Ataques Perigosos'].apply(lambda a: list(map(int,a[0].split(' - '))))

  # Converter Placar
  df['Placar'] = df['Placar'].apply(lambda a: list(map(int,a[0].split(' - '))))

  # Retirar \n
  df['Time Casa'] = df['Time Casa'].apply(lambda a: a.replace("\n", ""))
  df['Time Fora'] = df['Time Fora'].apply(lambda a: a.replace("\n", ""))
  df['Liga'] = df['Liga'].apply(lambda a: a.replace("\n", ""))
  df['Handicap'] = df['Handicap'].apply(lambda a: a.replace("\n", ""))
  df['Linha de Gols'] = df['Linha de Gols'].apply(lambda a: a.replace("\n", ""))

  def enviar_mensagem(msg):
    bot_token = '6438797881:AAEL5fBi2odqhejoQmBlELJu7UoaoivDoho'
    chat_id = -801501705
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={msg}'
    requests.post(url)

  mensagens_enviadas = []
  # Gols HT
  for i in range(len(df)):
    j = df.iloc[i]
    tempo = j['Tempo']

    appm_casa = round(j['Ataques Perigosos'][0]/tempo,1)
    appm_fora = round(j['Ataques Perigosos'][1]/tempo,1)
    appm_total = round((j['Ataques Perigosos'][0] + j['Ataques Perigosos'][1])/tempo,1)

    cg_casa = j['Escanteios'][0] + j['Chutes'][0]
    cg_fora = j['Escanteios'][1] + j['Chutes'][1]
    cg_total = cg_casa + cg_fora

    condicao_casa = (appm_casa >= 0.5 or cg_casa >= 12)
    condicao_fora = (appm_fora >= 0.5 or cg_fora >= 12) 
    condicao_total = (appm_total >= 0 and cg_total >= 2)

    print(f"Analisando jogo {i + 1} de {len(df)}")

    if condicao_total :
      casa = re.sub(r'^\d{1}','',j['Time Casa'])
      fora = re.sub(r'^\d{1}$','',j['Time Fora'])

      if f'{casa} X {fora}' not in mensagens_enviadas:
        msg = f'''
          Live
                  
          Jogo: {casa} X {fora}

          Placar: {j["Placar"][0]} X {j["Placar"][1]}

          Tempo: {j["Tempo"]} minutos

          Escanteios: {j["Escanteios"][0]} X {j["Escanteios"][1]}

          Chutes: {j["Chutes"][0]} X {j["Chutes"][1]}

          Ataques Perigosos: {j["Ataques Perigosos"][0]} X {j["Ataques Perigosos"][1]}

          Appm: {appm_casa} X {appm_fora}

          Chance de Gols: {cg_casa} X {cg_fora}
        '''
        print("Enviando mensagem...")
        enviar_mensagem(msg)
        mensagens_enviadas.append(f'{casa} X {fora}')
        print("Mensagem enviada")
        sleep(2)
  print("Loop concluído")
  return jsonify("Loop concluído"), 200

if __name__ == '__main__':
    app.run(debug=True)
