# Importamos las librerias a utilizar en la Aplicación
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from fastapi.templating import Jinja2Templates

# Configuración de NLTK
nltk.data.path.append("c:/Users/jorgeestrada/Library/Python/3.9/lib/python/site-packages/nltk")
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)

# Inicialización de la Aplicación
app = FastAPI(title="Infracciones de Tránsito", version="1.0.0")

# Definimos la ruta donde esta el archivo index.html para darle formato a la página
templates = Jinja2Templates(directory="/Users/jorgeestrada/BOOTCAMP_AI/proyecto_final/templates/index.html")

# Carga el dataset "datos_infracciones.csv" en la aplicación
def load_data(file_path: str):
    try:
        df = pd.read_csv(
            file_path,
            converters={'Estrato_socioeconomico': str, 'ID': str}
        )[[
            'ID', 'Estrato_socioeconomico', 'Tarifa_servicios_publicos',
            'Ingreso_estimado', 'Tipo_infracción', 'Valor_multa',
            'Porcentaje_carga', 'Porcentaje_salvaguarda'
        ]]
        df.columns = ['id', 'ssb', 'esp', 'income', 'tif', 'valmul', 'porcar', 'savepor']
        return df.fillna('').to_dict(orient='records')
    except Exception as e:
        raise RuntimeError(f"Error al cargar el archivo dedatos: {e}")

# Definimos la ruta donde tenemos el dataset "datos_infracciones.csv"
DATA_FILE = "/Users/jorgeestrada/BOOTCAMP_AI/proyecto_final/datos_infracciones.csv"
try:
        datos_list = load_data(DATA_FILE)
except RuntimeError as e:
        datos_list = []
        print(e)

# Definimos el Diccionario para convertir un número en palabras a números
palabras_a_numeros = {
        "uno": "1", "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10", "once": "11", "doce": "12", "trece": "13", "catorce": "14", "quince": "15", "dieciseis": "16", "diecisiete": "17", "dieciocho": "18", "diecinueve": "19", "veinte": "20"
    }
               
"""Extrae el primer número de estrato socioeconómico encontrado en la consulta del usuario."""
def extract_estrato(texto):
    match = re.search(r'\b\d+\b', texto) # Busca cuálquier número entero en el texto ingresado por el usuario
    if match: 
        return match.group()
    
    palabras = texto.lower().split()
    for palabra in palabras:
        if palabra in palabras_a_numeros:
            return palabras_a_numeros[palabra]
    return None

# Función para obtener sinónimos.
def get_synonyms(word: str):
    return {lemma.name().lower() for syn in wordnet.synsets(word) for lemma in syn.lemmas()}

# Definición de cada uno de los Endpoints de la API
@app.get('/', tags=['Página de Inicio'])
def home():
    return HTMLResponse("<h1>Bienvenido a la Aplicación de Infracciones de Tránsito</h1>")

@app.get('/datos/{id}', tags=['Consulta de Infracciones'])
def get_datos(id: str):
    data = next((item for item in datos_list if item['id'] == id), None)
    if data:
        return data
    raise HTTPException(status_code=404, detail="¡¡¡Registro no existe en la base de datos!!!")

@app.get('/chatbot', tags=['Chatbot para consulta de Infracciones según el estrato socioeconómico del infractor'])
def chatbot(query: str = Query(..., description="Consulta relacionada con el estrato socioeconómico del infractor:")):
    query_words = word_tokenize(query.lower())
 
 # Obtener sinónimos de las palabras en la consulta   
    synonyms = {word for q in query_words for word in get_synonyms(q)} | set(query_words)
    
 # Extraer el número o texto del estrato socioeconómico ingresado por el usuario o usar el primer valor encontrado o dejar vacio
    ssb_value = extract_estrato(query)
    if ssb_value is None:
        return JSONResponse(content={"respuesta": f"¡¡¡Estrato socioeconómico no válido!!!, por favor ingrese un valor entre 1 y 6.", "Multas": []})
    # Filtrar los resultados en datos_list comparando los valores   
    results = [item for item in datos_list if str(item['ssb']).strip() == ssb_value]
    
    response_message = f"Aquí tienes algunas multas relacionadas con el estrato socioeconómico: {ssb_value}" if results else f"Estrato ingresado: {ssb_value}. ¡¡¡Estrato socioeconómico no válido!!!, por favor ingrese un valor entre 1 y 6."
 
 # Devolver la respuesta    
    return JSONResponse(content={"respuesta": response_message, "Multas": results})
