import streamlit as st
from openai import OpenAI
import os
from streamlit_mic_recorder import mic_recorder
from difflib import SequenceMatcher

# --- CONFIGURACIÓN SEGURA ---
st.set_page_config(page_title="TOMÁS - CARCAIXENT", layout="wide", initial_sidebar_state="collapsed")

# Aquí usamos el secreto que configuraremos en el siguiente paso
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- DISEÑO ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #FEF9E7; }
    h1 { color: #1B4F72 !important; font-family: 'Helvetica', sans-serif; font-weight: bold; text-align: center; margin-top: -30px; }
    [data-testid="stHorizontalBlock"] { max-width: 800px; margin: 0 auto; }
    .stButton>button { height: 3.5em !important; border-radius: 5px !important; color: white !important; background-color: #1B4F72 !important; border: 1px solid #154360 !important; width: 100%; }
    .stButton>button:hover { background-color: #2E86C1 !important; }
    .stChatMessage { background-color: white !important; border: 1px solid #D4AC0D !important; border-radius: 10px; max-width: 850px; margin: 0 auto 10px auto; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN ---
if 'idioma' not in st.session_state: st.session_state.idioma = "es"
if 'historial' not in st.session_state: st.session_state.historial = []
if 'audio_key' not in st.session_state: st.session_state.audio_key = 0

def reset_memoria():
    st.session_state.historial = []
    st.rerun()

st.markdown("<h1>🏛️ Museu de Carcaixent</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #1B4F72; margin-bottom: 25px;'>Seleccione su idioma / Seleccione el seu idioma / Select language</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("CASTELLANO"): st.session_state.idioma = "es"; reset_memoria()
with col2:
    if st.button("VALENCIÀ"): st.session_state.idioma = "ca"; reset_memoria()
with col3:
    if st.button("ENGLISH"): st.session_state.idioma = "en"; reset_memoria()

idioma = st.session_state.idioma
config = {
    "es": {"inv": "Hola, soy Tomás. ¿En qué puedo ayudarle hoy?", "mic": "🎤 MANTENER PARA HABLAR", "sys": "Eres Tomás, guía experto de Carcaixent. Eres culto y cercano."},
    "ca": {"inv": "Hola, sóc Tomás. En què puc ajudar-lo hui?", "mic": "🎤 MANTINDRE PER A PARLAR", "sys": "Eres Tomás, guia expert de Carcaixent. Eres culte i proper."},
    "en": {"inv": "Hello, I am Tomás. How can I help you today?", "mic": "🎤 HOLD TO SPEAK", "sys": "You are Tomás, expert guide of Carcaixent. Cultured and friendly."}
}

if not st.session_state.historial:
    st.chat_message("assistant", avatar="🏛️").write(config[idioma]["inv"])
else:
    for chat in st.session_state.historial:
        st.chat_message(chat["role"], avatar="🏛️" if chat["role"]=="assistant" else "👤").write(chat["content"])

st.write("###")
_, col_mic, _ = st.columns([1,1,1])
with col_mic:
    # Este es el botón de pulsar para hablar
    audio = mic_recorder(start_prompt=config[idioma]["mic"], stop_prompt="🛑 SOLTAR PARA ENVIAR", key=f'mic_{st.session_state.audio_key}')

if audio:
    with st.spinner("Pensando..."):
        transcript = client.audio.transcriptions.create(model="whisper-1", file=("audio.wav", audio['bytes']), language=idioma)
        user_text = transcript.text.strip()

        es_repetido = False
        if st.session_state.historial:
            ultima_p = next((m["content"] for m in reversed(st.session_state.historial) if m["role"] == "user"), "")
            if SequenceMatcher(None, user_text.lower(), ultima_p.lower()).ratio() > 0.8:
                es_repetido = True

        if user_text and not es_repetido:
            contexto = ""
            if os.path.exists("info_museo.txt"):
                with open("info_museo.txt", "r", encoding="utf-8") as f: contexto = f.read()

            instrucciones = f"{config[idioma]['sys']} \n\n INFO: {contexto}"
            mensajes = [{"role": "system", "content": instrucciones}]
            for m in st.session_state.historial[-3:]: mensajes.append(m)
            mensajes.append({"role": "user", "content": user_text})

            response = client.chat.completions.create(model="gpt-4o-mini", messages=mensajes)
            respuesta = response.choices[0].message.content
            
            # Generamos la voz
            audio_ev = client.audio.speech.create(model="tts-1", voice="onyx", input=respuesta)

            st.session_state.historial.append({"role": "user", "content": user_text})
            st.session_state.historial.append({"role": "assistant", "content": respuesta})
            
            st.rerun()

# Reproducción automática del último audio
if st.session_state.historial and st.session_state.historial[-1]["role"] == "assistant":
    # Generamos el audio para la última respuesta si acaba de ocurrir
    respuesta_final = st.session_state.historial[-1]["content"]
    audio_play = client.audio.speech.create(model="tts-1", voice="onyx", input=respuesta_final)
    st.audio(audio_play.content, format="audio/mpeg", autoplay=True)
    st.session_state.audio_key += 1
