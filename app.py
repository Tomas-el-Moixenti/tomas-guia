import streamlit as st
from openai import OpenAI
import os
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURACIÓN DE SEGURIDAD ---
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("Por favor, configura la OPENAI_API_KEY en los Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="TOMÁS - MUSEU DE CARCAIXENT", layout="wide")

# --- DISEÑO (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #FEF9E7; }
    .stButton>button { 
        height: 4em !important; 
        font-size: 20px !important; 
        border-radius: 12px !important; 
        background-color: #1B4F72 !important; 
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN ---
if 'idioma' not in st.session_state: st.session_state.idioma = "es"
if 'historial' not in st.session_state: st.session_state.historial = []

def reset_memoria():
    st.session_state.historial = []
    st.rerun()

# --- INTERFAZ ---
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
    "es": {"mic": "🎤 PULSE PARA HABLAR", "sys": "Eres Tomás, guía experto del Museu de Carcaixent. Responde de forma amable y breve."},
    "ca": {"mic": "🎤 PREME PER A PARLAR", "sys": "Eres Tomás, guia expert del Museu de Carcaixent. Respon de forma amable i breu."},
    "en": {"mic": "🎤 TAP TO SPEAK", "sys": "You are Tomás, expert guide of the Museu de Carcaixent. Answer kindly and briefly."}
}

# Chat
for chat in st.session_state.historial:
    with st.chat_message(chat["role"], avatar="🏛️" if chat["role"]=="assistant" else "👤"):
        st.write(chat["content"])

# --- MICRO ---
st.write("---")
_, col_mic, _ = st.columns([1,2,1])
with col_mic:
    audio = mic_recorder(start_prompt=config[idioma]["mic"], stop_prompt="🛑 ESCUCHANDO...", key='recorder')

if audio:
    with st.spinner("Tomás está pensando..."):
        # 1. Transcripción
        transcript = client.audio.transcriptions.create(model="whisper-1", file=("audio.wav", audio['bytes']), language=idioma)
        user_text = transcript.text.strip()

        if user_text:
            # 2. Contexto
            contexto = ""
            if os.path.exists("info_museo.txt"):
                with open("info_museo.txt", "r", encoding="utf-8") as f: contexto = f.read()

            mensajes = [{"role": "system", "content": f"{config[idioma]['sys']} \n\n INFO: {contexto}"}]
            for m in st.session_state.historial[-5:]: mensajes.append(m)
            mensajes.append({"role": "user", "content": user_text})

            # 3. Respuesta de Texto
            response = client.chat.completions.create(model="gpt-4o-mini", messages=mensajes)
            respuesta = response.choices[0].message.content
            
            # 4. Voz
            audio_ev = client.audio.speech.create(model="tts-1", voice="onyx", input=respuesta)
            
            # Guardar y mostrar
            st.session_state.historial.append({"role": "user", "content": user_text})
            st.session_state.historial.append({"role": "assistant", "content": respuesta})
            
            # Reproducir Audio
            st.audio(audio_ev.content, format="audio/mpeg", autoplay=True)
            st.rerun()
