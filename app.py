import streamlit as st
from openai import OpenAI
import os
from streamlit_mic_recorder import mic_recorder
from difflib import SequenceMatcher

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="TOMÁS - CARCAIXENT", layout="wide", initial_sidebar_state="collapsed")
client = OpenAI(api_key="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")

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

# --- FRONT PANEL ---
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
    "es": {"inv": "Hola, soy Tomás. ¿En qué puedo ayudarle hoy?", "mic": "🎤 HABLAR", "sys": "Eres Tomás, guía experto de Carcaixent. Eres culto y cercano."},
    "ca": {"inv": "Hola, sóc Tomás. En què puc ajudar-lo hui?", "mic": "🎤 PARLAR", "sys": "Eres Tomás, guia expert de Carcaixent. Eres culte i proper."},
    "en": {"inv": "Hello, I am Tomás. How can I help you today?", "mic": "🎤 SPEAK", "sys": "You are Tomás, expert guide of Carcaixent. Cultured and friendly."}
}

# Chat
if not st.session_state.historial:
    st.chat_message("assistant", avatar="🏛️").write(config[idioma]["inv"])
else:
    for chat in st.session_state.historial:
        st.chat_message(chat["role"], avatar="🏛️" if chat["role"]=="assistant" else "👤").write(chat["content"])

# --- MICRO (Cuidado con los espacios aquí abajo) ---
st.write("###")
_, col_mic, _ = st.columns([1,1,1])
with col_mic:
    audio = mic_recorder(start_prompt=config[idioma]["mic"], stop_prompt="🛑 ESCUCHANDO...", key=f'mic_{st.session_state.audio_key}')

if audio:
    with st.spinner("..."):
        transcript = client.audio.transcriptions.create(model="whisper-1", file=("audio.wav", audio['bytes']), language=idioma)
        user_text = transcript.text.strip()

        # Filtro de eco
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
            audio_ev = client.audio.speech.create(model="tts-1", voice="onyx", input=respuesta)

            st.session_state.historial.append({"role": "user", "content": user_text})
            st.session_state.historial.append({"role": "assistant", "content": respuesta})
            
            with st.chat_message("assistant", avatar="🏛️"):
                st.write(respuesta)
                st.audio(audio_ev.content, format="audio/mpeg", autoplay=True)
                
                # Canción (si pides música)
                if any(x in user_text.lower() for x in ["música", "canción", "botifarra"]):
                    if os.path.exists("jota_botifarra.mp3"):
                        st.audio("jota_botifarra.mp3", format="audio/mpeg")
            
            st.session_state.audio_key += 1
