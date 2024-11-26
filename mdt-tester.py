#import streamlit as st
import requests
from extruct import extract
from w3lib.html import get_base_url
import pandas as pd
import logging

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Funzione per appiattire i dizionari annidati
def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if isinstance(x, dict):
            for a in x:
                flatten(x[a], f'{name}{a}_')
        elif isinstance(x, list):
            i = 0
            for a in x:
                flatten(a, f'{name}{i}_')
                i += 1
        else:
            out[name[:-1]] = x
    flatten(y)
    return out

# Funzione per processare un singolo URL
def process_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html_content = response.text
        base_url = get_base_url(html_content, response.url)
        data = extract(html_content, base_url=base_url)

        results = {}

        # Processa i dati JSON-LD
        if data.get('json-ld'):
            json_ld_data = [flatten_json(item) for item in data['json-ld']]
            results['json-ld'] = pd.DataFrame(json_ld_data)
        else:
            results['json-ld'] = pd.DataFrame()

        # Processa i Microdata
        if data.get('microdata'):
            microdata_list = [flatten_json(item) for item in data['microdata']]
            results['microdata'] = pd.DataFrame(microdata_list)
        else:
            results['microdata'] = pd.DataFrame()

        # Processa i dati RDFa
        if data.get('rdfa'):
            rdfa_list = [flatten_json(item) for item in data['rdfa']]
            results['rdfa'] = pd.DataFrame(rdfa_list)
        else:
            results['rdfa'] = pd.DataFrame()

        # Processa i dati OpenGraph
        if data.get('opengraph'):
            opengraph_data = flatten_json(data['opengraph'])
            results['opengraph'] = pd.DataFrame([opengraph_data])
        else:
            results['opengraph'] = pd.DataFrame()

        return results
    except Exception as e:
        st.error(f"Errore durante l'elaborazione dell'URL {url}: {e}")
        return None

# Configura Streamlit
st.title("Markup Tester")
st.write("Analizza i dati strutturati (JSON-LD, Microdata, RDFa, OpenGraph) da un URL.")

# Input URL
url = st.text_input("Inserisci un URL da analizzare:")

# Pulsante per avviare l'analisi
if st.button("Analizza"):
    if url:
        st.info(f"Analizzando {url}...")
        results = process_url(url)
        if results:
            for data_type, df in results.items():
                if not df.empty:
                    st.subheader(f"Dati trovati: {data_type.upper()}")
                    st.dataframe(df)
                else:
                    st.warning(f"Nessun dato {data_type.upper()} trovato.")
    else:
        st.warning("Per favore, inserisci un URL valido.")
