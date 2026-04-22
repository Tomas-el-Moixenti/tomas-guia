import streamlit as st
from openai import OpenAI
import os

st.set_page_config(page_title="TOMÁS - GUÍA MUSEO", layout="centered")

# Configuración de la llave
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("🤖 Tomás, tu guía del Museo")

# Leer la información del museo
with open("info_museo.txt", "r", encoding="utf-8") as f:
    contexto_museo = f.read()

# Chat por teclado (Esto no fallará)
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Eres Tomás, un guía amable del museo de Carcaixent. Responde breve y en español basándote en esto: {contexto_museo}"},
                {"role": "user", "content": prompt}
            ]
        )
        msg = response.choices[0].message.content
        st.write(msg)
        
        # Voz de respuesta rápida
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=msg
        )
        st.audio(audio_response.content, format="audio/mp3", autoplay=True)
