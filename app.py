import streamlit as st
from openai import OpenAI
import os
from streamlit_mic_recorder import mic_recorder
from difflib import SequenceMatcher

# --- CONFIGURACIÓN DE SEGURIDAD ---
# En la nube, configuraremos la API KEY en los "Secrets" de la plataforma
# Si estás en local, la leerá de tus variables de entorno.
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("Por favor, configura la OPENAI_API_KEY en los Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="TOMÁS - MUSEU DE CARCAIXENT", layout="wide", initial_sidebar_state="collapsed")

# --- DISEÑO (CSS mejorado para tablets) ---
st.markdown("""
    <style>
    .stApp { background-color: #FEF9E7; }
    .stButton>button { 
        height: 4em !important; 
        font-size: 20px !important; /* Más grande para tablets */
        border-radius: 12px !important; 
        background-color: #1B4F72 !important; 
        color: white !important;
    }
    .stChatMessage { border-radius: 15px; border: 1px solid #D4AC0D; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN ---
if 'idioma' not in st.session_state: st.session_state.idioma = "es"
if 'historial' not in st.session_state: st.session_state.historial = []
if 'audio_key' not in st.session_state: st.session_state.audio_key = 0

def reset_memoria():
    st.session_state.historial = []
    st.rerun()

# --- PANEL DE CONTROL ---
st.markdown("<h1 style='text-align: center; color: #1B4F72;'>🏛️ Museu de Carcaixent</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("CASTELLANO"): st.session_state.idioma = "es"; reset_memoria()
with col2:
    if st.button("VALENCIÀ"): st.session_state.idioma = "ca"; reset_memoria()
with col3:
    if st.button("ENGLISH"): st.session_state.idioma = "en"; reset_memoria()

idioma = st.session_state.idioma
config = {
    "es": {"inv": "Hola, soy Tomás. ¿En qué puedo ayudarle hoy?", "mic": "🎤 PULSE PARA HABLAR", "sys": "Eres Tomás, guía experto de Carcaixent."},
    "ca": {"inv": "Hola, sóc Tomás. En què puc ajudar-lo hui?", "mic": "🎤 PREME PER A PARLAR", "sys": "Eres Tomás, guia expert de Carcaixent."},
    "en": {"inv": "Hello, I am Tomás. How can I help you today?", "mic": "🎤 TAP TO SPEAK", "sys": "You are Tomás, expert guide of Carcaixent."}
}

# Mostrar Chat
for chat in st.session_state.historial:
    st.chat_message(chat["role"], avatar="🏛️" if chat["role"]=="assistant" else "👤").write(chat["content"])

# --- MICRO ---
st.write("---")
_, col_mic, _ = st.columns([1,2,1])
with col_mic:
    # El mic_recorder funciona perfecto en tablets desde el navegador
    audio = mic_recorder(start_prompt=config[idioma]["mic"], stop_prompt="🛑 ESCUCHANDO...", key=f'mic_{st.session_state.audio_key}')

if audio:
    with st.spinner("Pensando..."):
        # 1. Transcripción
        transcript = client.audio.transcriptions.create(model="whisper-1", file=("audio.wav", audio['bytes']), language=idioma)
        user_text = transcript.text.strip()

        if user_text:
            # 2. Cargar conocimiento (Se sube el TXT junto al código)
            contexto = ""
            if os.path.exists("info_museo.txt"):
                with open("info_museo.txt", "r", encoding="utf-8") as f: contexto = f.read()

            mensajes = [{"role": "system", "content": f"{config[idioma]['sys']} \n\n INFO: {contexto}"}]
            for m in st.session_state.historial[-5:]: mensajes.append(m)
            mensajes.append({"role": "user", "content": user_text})

            # 3. Respuesta y voz
            response = client.chat.completions.create(model="gpt-4o-mini", messages=mensajes)
            respuesta = response.choices[0].message.content
            audio_ev = client.audio.speech.create(model="tts-1", voice="onyx", input=respuesta)

            # Guardar en historial
            st.session_state.historial.append({"role": "user", "content": user_text})
            st.session_state.historial.append({"role": "assistant", "content": respuesta})
            
            # 4. Reproducción y actualización
            st.session_state.audio_key += 1
            st.rerun()

# Reproducir el último audio si existe
if st.session_state.historial and st.session_state.historial[-1]["role"] == "assistant":
    # Aquí es donde el MP3 se reproduce automáticamente en la tablet
    st.audio(audio_ev.content, format="audio/mpeg", autoplay=True)
