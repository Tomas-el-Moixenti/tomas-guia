import streamlit as st
from openai import OpenAI
import os
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="TOMÁS - MUSEU", layout="wide", initial_sidebar_state="collapsed")

# CLAVE DIRECTA (Limpiada de saltos de línea para que funcione sí o sí)
MI_LLAVE = "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"

client = OpenAI(api_key=MI_LLAVE)

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background-color: #FEF9E7; }
    .stButton>button { height: 3em !important; font-size: 20px !important; background-color: #1B4F72 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE ESTADO ---
if 'idioma' not in st.session_state: st.session_state.idioma = "es"
if 'historial' not in st.session_state: st.session_state.historial = []
if 'audio_key' not in st.session_state: st.session_state.audio_key = 0

# --- TRADUCCIONES ---
config = {
    "es": {"titulo": "🏛️ Museu de Carcaixent", "mic": "🎤 PULSE PARA HABLAR", "sys": "Eres Tomás, guía del museo."},
    "ca": {"titulo": "🏛️ Museu de Carcaixent", "mic": "🎤 PREME PER A PARLAR", "sys": "Eres Tomás, guia del museu."},
    "en": {"titulo": "🏛️ Carcaixent Museum", "mic": "🎤 TAP TO SPEAK", "sys": "You are Tomás, museum guide."}
}

st.markdown(f"<h1 style='text-align: center; color: #1B4F72;'>{config[st.session_state.idioma]['titulo']}</h1>", unsafe_allow_html=True)

# Botones de idioma
c1, c2, c3 = st.columns(3)
with c1: 
    if st.button("CASTELLANO"): st.session_state.idioma = "es"; st.session_state.historial = []; st.rerun()
with c2: 
    if st.button("VALENCIÀ"): st.session_state.idioma = "ca"; st.session_state.historial = []; st.rerun()
with c3: 
    if st.button("ENGLISH"): st.session_state.idioma = "en"; st.session_state.historial = []; st.rerun()

# Mostrar historial
for m in st.session_state.historial:
    st.chat_message(m["role"]).write(m["content"])

# --- GRABADOR ---
st.write("---")
audio = mic_recorder(start_prompt=config[st.session_state.idioma]["mic"], stop_prompt="🛑 ESCUCHANDO...", key=f"mic_{st.session_state.audio_key}")

if audio:
    with st.spinner("Tomás está pensando..."):
        # 1. Transcribir
        trans = client.audio.transcriptions.create(model="whisper-1", file=("audio.wav", audio['bytes']), language=st.session_state.idioma)
        pregunta = trans.text
        
        # 2. Responder
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": config[st.session_state.idioma]["sys"]}] + st.session_state.historial + [{"role": "user", "content": pregunta}]
        )
        respuesta = res.choices[0].message.content
        
        # 3. Audio de respuesta
        speech = client.audio.speech.create(model="tts-1", voice="onyx", input=respuesta)
        
        # Guardar y refrescar
        st.session_state.historial.append({"role": "user", "content": pregunta})
        st.session_state.historial.append({"role": "assistant", "content": respuesta})
        st.session_state.audio_key += 1
        st.rerun()

# Reproducción automática si el último es del asistente
if st.session_state.historial and st.session_state.historial[-1]["role"] == "assistant":
    last_text = st.session_state.historial[-1]["content"]
    audio_res = client.audio.speech.create(model="tts-1", voice="onyx", input=last_text)
    st.audio(audio_res.content, format="audio/mpeg", autoplay=True)
