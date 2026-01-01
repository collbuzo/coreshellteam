import streamlit as st
import google.generativeai as genai
from streamlit_javascript import st_javascript
import json
import time

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO (CYBER-DARK THEME)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CoreShell Team", page_icon="💠", layout="wide")

st.markdown("""
    <style>
    /* Fondo y Tipografía General */
    .stApp { background-color: #0E1117; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    
    /* Títulos Neon */
    h1, h2, h3 { color: #00FFCC !important; font-family: 'Consolas', monospace; letter-spacing: -1px; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    
    /* Cajas de Código y Resultados */
    .stCodeBlock { border: 1px solid #30363D; border-radius: 8px; background-color: #0d1117 !important; }
    
    /* Botones de Acción (Cyan) */
    div.stButton > button:first-child {
        background-color: #00FFCC; color: #0E1117; border-radius: 6px;
        border: none; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #00E6B8; box-shadow: 0 0 10px rgba(0, 255, 204, 0.4); color: #000;
    }
    
    /* Botones de eliminar favoritos (Pequeños y rojos) */
    .delete-btn { color: #ff4b4b; border: 1px solid #ff4b4b; background: transparent; }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: #161B22; color: white; border: 1px solid #30363D; border-radius: 6px;
    }
    .stTextInput > div > div > input:focus { border-color: #00FFCC; box-shadow: 0 0 5px rgba(0,255,204,0.2); }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. LÓGICA DE PERSISTENCIA (LOCAL STORAGE)
# -----------------------------------------------------------------------------
def get_local_storage():
    return st_javascript("JSON.parse(localStorage.getItem('coreshell_favs') || '[]')")

def save_local_storage(favs):
    json_str = json.dumps(favs).replace("'", "\\'")
    st_javascript(f"localStorage.setItem('coreshell_favs', '{json_str}')")

# Cargar favoritos al inicio (evita parpadeos recargando solo si es necesario)
if 'favoritos' not in st.session_state:
    st.session_state.favoritos = []
    
# Intentar sincronizar con el navegador (solo si la lista está vacía al inicio)
vals = get_local_storage()
if vals and not st.session_state.favoritos:
    st.session_state.favoritos = vals

# -----------------------------------------------------------------------------
# 3. BASE DE DATOS LOCAL (COMMAND KNOWLEDGE BASE)
# -----------------------------------------------------------------------------
comandos_locales = {
    # ARCHIVOS
    "listar archivos": {"mac": "ls -la", "win": "dir /a", "desc": "Lista todos los archivos, incluyendo los ocultos."},
    "crear carpeta": {"mac": "mkdir [nombre]", "win": "mkdir [nombre]", "desc": "Crea un nuevo directorio."},
    "borrar carpeta": {"mac": "rm -rf [carpeta]", "win": "rmdir /s /q [carpeta]", "desc": "⚠️ Elimina una carpeta y todo su contenido."},
    "mover archivo": {"mac": "mv [origen] [destino]", "win": "move [origen] [destino]", "desc": "Mueve o renombra archivos."},
    "copiar archivo": {"mac": "cp [origen] [destino]", "win": "copy [origen] [destino]", "desc": "Copia un archivo."},
    "buscar texto": {"mac": "grep -r '[texto]' .", "win": "findstr /s /i '[texto]' *.*", "desc": "Busca texto dentro de archivos en la carpeta actual."},
    
    # RED
    "mi ip": {"mac": "ifconfig | grep inet", "win": "ipconfig", "desc": "Muestra tu configuración de red y dirección IP."},
    "ping": {"mac": "ping -c 4 [url]", "win": "ping [url]", "desc": "Comprueba la conexión con un servidor."},
    "puertos abiertos": {"mac": "lsof -i -P | grep LISTEN", "win": "netstat -an | findstr LISTENING", "desc": "Muestra qué puertos están escuchando conexiones."},
    "dns lookup": {"mac": "nslookup [dominio]", "win": "nslookup [dominio]", "desc": "Consulta la IP asociada a un dominio."},
    "descargar archivo": {"mac": "curl -O [url]", "win": "curl.exe -O [url]", "desc": "Descarga un archivo desde internet."},
    
    # SISTEMA
    "uso disco": {"mac": "df -h", "win": "wmic logicaldisk get size,freespace,caption", "desc": "Muestra el espacio libre en disco."},
    "uso memoria": {"mac": "top -l 1 | grep PhysMem", "win": "systeminfo | findstr Memory", "desc": "Estado de la memoria RAM."},
    "matar proceso": {"mac": "kill -9 [PID]", "win": "taskkill /F /PID [PID]", "desc": "Fuerza el cierre de un programa bloqueado."},
    "historial": {"mac": "history", "win": "doskey /history", "desc": "Muestra los últimos comandos ejecutados."},
    "limpiar pantalla": {"mac": "clear", "win": "cls", "desc": "Limpia la terminal."},
    "permisos": {"mac": "chmod 755 [archivo]", "win": "icacls [archivo] /grant [usuario]:F", "desc": "Cambia los permisos de lectura/escritura."},
    
    # GIT (EXTRA PARA DEVS)
    "git status": {"mac": "git status", "win": "git status", "desc": "Estado actual del repositorio."},
    "git commit": {"mac": "git commit -m 'mensaje'", "win": "git commit -m 'mensaje'", "desc": "Guarda cambios con un mensaje."},
    "git push": {"mac": "git push origin main", "win": "git push origin main", "desc": "Sube cambios al servidor remoto."}
}

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL (SIDEBAR)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 💠 CoreShell Team")
    st.caption("The Collective Memory for Engineering Teams")
    
    # --- SECCIÓN FAVORITOS (TOOLBOX) ---
    st.markdown("---")
    st.markdown("### ⭐ My Toolbox")
    if not st.session_state.favoritos:
        st.info("Tu caja de herramientas está vacía. Guarda comandos para verlos aquí.")
    else:
        for i, fav in enumerate(st.session_state.favoritos):
            with st.expander(f"📌 {fav['nombre'].capitalize()}", expanded=False):
                st.code(fav['mac'], language='bash')
                st.code(fav['win'], language='powershell')
                if st.button("Eliminar", key=f"del_{i}"):
                    st.session_state.favoritos.pop(i)
                    save_local_storage(st.session_state.favoritos)
                    st.rerun()

    # --- SECCIÓN MONETIZACIÓN & CONTACTO ---
    st.markdown("---")
    st.markdown("### 🤝 Support & Team Plan")
    
    # Botón Buy Me A Coffee (Enlace directo a tu cuenta)
    st.markdown(
        """
        <a href="https://buymeacoffee.com/coreshellteam" target="_blank">
            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 45px !important;width: 160px !important;" >
        </a>
        """,
        unsafe_allow_html=True
    )
    
    st.caption("Cada café ayuda a mantener los servidores y el desarrollo gratuito.")
    
    st.markdown("---")
    st.info("🏢 **¿Eres una empresa?** Contáctanos para la versión **Team Edition** con repositorio privado de comandos.")

    # --- SECCIÓN CONFIGURACIÓN (API KEY) ---
    with st.expander("⚙️ Configuración IA"):
        api_key = st.text_input("Gemini API Key:", type="password", help="Trae tu propia clave para desbloquear la IA.")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            st.success("✅ IA Conectada")
        else:
            st.warning("⚠️ IA Desconectada (Solo modo local)")

# -----------------------------------------------------------------------------
# 5. CUERPO PRINCIPAL (MAIN UI)
# -----------------------------------------------------------------------------

# Encabezado (Hero)
col_logo, col_txt = st.columns([1, 5])
with col_logo:
    st.markdown("# 💠") # Aquí iría tu logo imagen si lo subes
with col_txt:
    st.title("CoreShell Team")
    st.markdown("##### *Instant Knowledge. Secure Collaboration.*")

# Buscador Principal
query = st.text_input("", placeholder="¿Qué quieres hacer hoy? (Ej: ver puertos abiertos, desplegar docker...)", help="Escribe en lenguaje natural")

if query:
    q = query.lower().strip()
    resultado = None
    origen = "local"

    # 1. Búsqueda en Base de Datos Local
    for key, val in comandos_locales.items():
        if q in key:
            resultado = {"nombre": key, "mac": val['mac'], "win": val['win'], "desc": val['desc']}
            break

    # 2. Búsqueda en IA (Si no está en local y hay API Key)
    if not resultado and api_key:
        with st.spinner("🤖 CoreShell AI está analizando tu petición..."):
            try:
                # Prompt de ingeniería para asegurar formato JSON-like
                prompt = f"""
                Actúa como experto DevOps. Usuario quiere: '{query}'.
                Responde EXCLUSIVAMENTE con este formato exacto:
                MAC: [comando zsh]
                WIN: [comando powershell]
                DESC: [explicación muy breve]
                WARN: [Si es peligroso pon 'SI', si no 'NO']
                """
                response = model.generate_content(prompt).text
                
                # Parseo manual robusto
                lines = response.split('\n')
                mac_cmd = next((l.split('MAC:')[1].strip() for l in lines if 'MAC:' in l), "No encontrado")
                win_cmd = next((l.split('WIN:')[1].strip() for l in lines if 'WIN:' in l), "No encontrado")
                desc = next((l.split('DESC:')[1].strip() for l in lines if 'DESC:' in l), "Comando generado por IA")
                
                resultado = {"nombre": query, "mac": mac_cmd, "win": win_cmd, "desc": desc}
                origen = "ia"
            except Exception as e:
                st.error(f"Error de conexión con la IA: {e}")

    # 3. Mostrar Resultados
    if resultado:
        if origen == "ia":
            st.caption("✨ Generado por Gemini AI")
        
        st.success(f"💡 {resultado['desc']}")

        col_mac, col_win = st.columns(2)
        
        with col_mac:
            st.markdown("### 🍎 macOS / Linux (Zsh)")
            st.code(resultado['mac'], language='bash')
            
        with col_win:
            st.markdown("### 🪟 Windows (PowerShell)")
            st.code(resultado['win'], language='powershell')

        # Botón de Guardar
        col_btn, _ = st.columns([1, 3])
        with col_btn:
            if st.button("⭐ Añadir a mi Toolbox"):
                # Verificar duplicados
                if not any(d['nombre'] == resultado['nombre'] for d in st.session_state.favoritos):
                    st.session_state.favoritos.append(resultado)
                    save_local_storage(st.session_state.favoritos)
                    st.toast("¡Comando guardado en la barra lateral!", icon="✅")
                    time.sleep(1) # Pequeña pausa para que se actualice la UI
                    st.rerun()
                else:
                    st.toast("Este comando ya está en tus favoritos.", icon="⚠️")

    elif not resultado and not api_key:
        st.warning("No encontrado en la base local. **Conecta tu API Key** en la barra lateral para preguntar a la IA.")

# Pie de página
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>© 2024 CoreShell Team | The Last CLI Reference You'll Ever Need</div>", unsafe_allow_html=True)