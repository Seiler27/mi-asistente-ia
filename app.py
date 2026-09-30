# ============================================================
#  Semana 6 - Mi Asistente Inteligente (Chatbot + Transcriptor)
# ============================================================

# ---------- Bloque 1: Importar herramientas ----------
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

# ---------- Bloque 2: Conectar con OpenAI ----------
# Cargar tu clave desde el archivo .env (NUNCA la escribas aquí)
load_dotenv(override=True)  # override: siempre lee la clave actual del .env

# Configurar cómo se ve tu página (debe ir antes de cualquier otro st.*)
st.set_page_config(
    page_title="Mi Asistente Inteligente",
    page_icon="🤖",
    layout="wide",
)

# Versión GRATIS: usamos Groq, que es compatible con la librería openai.
# Consigue tu clave gratis en https://console.groq.com/keys
clave = (os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
if not clave.startswith("gsk_"):
    st.error("❌ No encontré tu clave de Groq. El archivo .env debe tener una sola línea así: GROQ_API_KEY=gsk_...")
    st.stop()

# Crear la conexión (misma librería openai, pero apuntando a los servidores de Groq)
client = OpenAI(api_key=clave, base_url="https://api.groq.com/openai/v1")

# Modelos gratuitos de Groq: elegimos automáticamente uno que tu cuenta tenga disponible
PREFERIDOS_CHAT = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b",
                   "openai/gpt-oss-20b", "llama-3.1-8b-instant"]
PREFERIDOS_AUDIO = ["whisper-large-v3-turbo", "whisper-large-v3"]

@st.cache_data(ttl=3600)
def modelos_disponibles(clave_actual):
    try:
        return [m.id for m in client.models.list().data]
    except Exception:
        return []

disponibles = modelos_disponibles(clave)

def elegir(preferidos):
    for m in preferidos:
        if m in disponibles:
            return m
    return preferidos[0]

MODELO_CHAT = elegir(PREFERIDOS_CHAT)     # reemplaza a gpt-3.5-turbo
MODELO_AUDIO = elegir(PREFERIDOS_AUDIO)   # reemplaza a whisper-1

# Título que verá el usuario
st.title("🤖 Mi Asistente + Transcriptor")
st.markdown("---")
st.caption(f"Modelo de chat: {MODELO_CHAT} · Modelo de audio: {MODELO_AUDIO}")

# ---------- Bloque 3: Crear las dos pestañas ----------
tab_chat, tab_audio = st.tabs([
    "💬 Chatbot Personalizado",
    "🎙️ Transcriptor de Voz a Texto",
])

# ---------- Bloque 4: Chatbot ----------
with tab_chat:
    st.header("Tu Asistente con Personalidad")

    # Crear la memoria (session_state guarda datos entre interacciones)
    if "historial" not in st.session_state:
        st.session_state.historial = [
            {
                "role": "system",
                "content": (
                    "Eres AsistenteTIC, ayudante del curso. "
                    "Respondes claro, amable y breve. "
                    "Solo hablas sobre herramientas TIC y desarrollo profesional. "
                    "Si te preguntan de otro tema responde: "
                    "'Me especializo en tecnología aplicada. ¿Te ayudo con algo de eso?'"
                ),
            }
        ]

    # Botón para empezar de nuevo
    if st.button("🔄 Reiniciar Conversación"):
        del st.session_state.historial
        st.rerun()

    # Mostrar mensajes anteriores (sin el mensaje "system")
    for mensaje in st.session_state.historial[1:]:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    # Recibir pregunta del usuario
    pregunta = st.chat_input("Escribe tu pregunta aquí...")

    if pregunta:
        with st.chat_message("user"):
            st.markdown(pregunta)

        # Guardar en la memoria
        st.session_state.historial.append({"role": "user", "content": pregunta})

        # Enviar TODO el historial a GPT
        with st.chat_message("assistant"):
            with st.spinner("Pensando... ⏳"):
                try:
                    respuesta = client.chat.completions.create(
                        model=MODELO_CHAT,
                        messages=st.session_state.historial,
                        temperature=0.7,
                        max_tokens=800,
                    )
                    texto_respuesta = respuesta.choices[0].message.content
                    st.markdown(texto_respuesta)

                    # Guardar respuesta para recordar después
                    st.session_state.historial.append(
                        {"role": "assistant", "content": texto_respuesta}
                    )
                except Exception as error:
                    st.session_state.historial.pop()  # quitar la pregunta que falló
                    st.error(f"❌ Error: {error}")

# ---------- Bloque 5: Transcriptor ----------
with tab_audio:
    st.header("Convierte tu Voz en Texto")
    st.write("Sube una grabación y obtén el texto automáticamente.")

    archivo_audio = st.file_uploader(
        "Selecciona tu grabación",
        type=["mp3", "wav", "m4a", "ogg"],
        help="Formatos soportados: MP3, WAV, M4A, OGG. Máximo 25 MB.",
    )

    if archivo_audio:
        st.success(f"✅ Recibido: {archivo_audio.name}")
        tamaño_kb = round(archivo_audio.size / 1024, 1)
        st.info(f"Tamaño: {tamaño_kb} KB")

        if st.button("📝 Transcribir Ahora"):
            with st.spinner("Procesando audio... ⏳"):
                try:
                    # Enviar a Whisper (nombre + bytes del archivo)
                    texto = client.audio.transcriptions.create(
                        model=MODELO_AUDIO,
                        file=(archivo_audio.name, archivo_audio.getvalue()),
                        response_format="text",
                    )

                    st.success("✅ ¡Transcripción Completada!")
                    st.subheader("Texto Obtenido:")
                    st.text_area("Transcripción", texto, height=300,
                                 label_visibility="collapsed")

                    st.download_button(
                        label="💾 Descargar (.txt)",
                        data=texto,
                        file_name="transcripcion.txt",
                        mime="text/plain",
                    )
                except Exception as error:
                    st.error(f"❌ Error: {error}")
                    st.info("💡 Solución: Verifica que el archivo no supere 25 MB y que sea MP3, WAV, M4A u OGG.")
