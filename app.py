import streamlit as st
import static_ffmpeg
import io
import zipfile

# --- SOLUCIÓN DEFINITIVA AL ERROR DE FFPROBE EN WINDOWS ---
# Esto descarga e inyecta ffmpeg y ffprobe automáticamente
static_ffmpeg.add_paths()

from pydub import AudioSegment

st.set_page_config(page_title="Editor de Cornetas", layout="centered")
st.title("🎺 Editor de Cornetas Múltiple")
st.markdown("Sube tu corneta, selecciona varias canciones, y descarga todas editadas en un solo ZIP.")

# --- 1. SUBIR CORNETA ---
st.header("1. Audio de la Corneta")
corneta_file = st.file_uploader("Sube el audio de la corneta (MP3)", type=["mp3"])

# --- 2. SUBIR CANCIONES ---
st.header("2. Canciones Principales")
canciones_files = st.file_uploader(
    "Sube una o varias canciones (MP3). Mantén presionado Ctrl para seleccionar varias.", 
    type=["mp3"], 
    accept_multiple_files=True
)

# --- 3. CONFIGURACIÓN ---
st.header("3. Configuración de Tiempos")
col1, col2 = st.columns(2)
with col1:
    intervalo = st.number_input("Insertar cada (segundos)", min_value=1, value=20, step=1)
with col2:
    duracion = st.number_input("Duración del sonido (segundos)", min_value=1, value=3, step=1)

# --- 4. PROCESAR Y DESCARGAR ---
if st.button("🎛️ Generar Canciones Editadas"):
    if not corneta_file:
        st.error("⚠️ Primero sube el audio de la corneta.")
    elif not canciones_files:
        st.error("⚠️ Sube al menos una canción principal.")
    else:
        progreso = st.progress(0)
        estado = st.empty()
        estado.text("Iniciando procesamiento...")
        
        # Cargar la corneta en memoria
        try:
            corneta = AudioSegment.from_file(corneta_file, format="mp3")
            corneta = corneta[:int(duracion * 1000)] # Cortar a la duración deseada
        except Exception as e:
            st.error(f"Error al leer la corneta: {e}")
            st.stop()
        
        # Crear archivo ZIP en memoria
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            total = len(canciones_files)
            for idx, cancion_file in enumerate(canciones_files):
                estado.text(f"Procesando: {cancion_file.name} ({idx+1}/{total})")
                try:
                    # Cargar canción en memoria
                    cancion = AudioSegment.from_file(cancion_file, format="mp3")
                    
                    # Insertar corneta
                    intervalo_ms = int(intervalo * 1000)
                    resultado = cancion
                    for i in range(0, len(cancion), intervalo_ms):
                        resultado = resultado.overlay(corneta, position=i)
                    
                    # Exportar a buffer
                    output_buffer = io.BytesIO()
                    resultado.export(output_buffer, format="mp3")
                    output_buffer.seek(0)
                    
                    # Añadir al ZIP
                    zip_file.writestr(f"editada_{cancion_file.name}", output_buffer.read())
                except Exception as e:
                    st.warning(f"No se pudo procesar {cancion_file.name}: {e}")
                
                progreso.progress((idx + 1) / total)
            
        zip_buffer.seek(0)
        estado.text("¡Proceso completado!")
        st.success(f"¡Listo! Se editaron {total} canción(es).")
        
        st.download_button(
            label="⬇️ Descargar Todas las Canciones (ZIP)",
            data=zip_buffer,
            file_name="canciones_editadas.zip",
            mime="application/zip"
        )