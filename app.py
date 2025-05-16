import requests
import argparse
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar configuración del .env
load_dotenv()

# Argumentos
parser = argparse.ArgumentParser(description="Crear un ticket en Jira desde una tarea fallida.")
parser.add_argument("--empresa", required=True, help="Nombre de la empresa")
parser.add_argument("--servicio", required=True, help="Nombre del servicio")
parser.add_argument("--servidor", required=True, help="Nombre del servidor")
parser.add_argument("--tarea", required=True, help="Nombre de la tarea fallida")
args = parser.parse_args()

# Configuración desde .env
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USER = os.getenv("JIRA_USER")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
WEBSERVICE_TOKEN_URL = os.getenv("WEBSERVICE_TOKEN_URL")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
LOG_PATH = os.getenv("LOG_PATH")

def registrar_evento(resultado):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] Empresa: {args.empresa} | Servicio: {args.servicio} | Servidor: {args.servidor} | Tarea: {args.tarea} | Resultado: {resultado}\n"
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registro_tickets.log")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(linea)

# Validar .env
if not all([JIRA_URL, JIRA_USER, JIRA_PROJECT_KEY, WEBSERVICE_TOKEN_URL, BEARER_TOKEN, LOG_PATH]):
    error_msg = "❌ Faltan variables en el archivo .env"
    print(error_msg)
    registrar_evento(error_msg)
    exit(1)

# Obtener token de Jira desde el webservice
try:
    response = requests.get(
        WEBSERVICE_TOKEN_URL,
        headers={"Authorization": f"Bearer {BEARER_TOKEN}"}
    )
    response.raise_for_status()
    JIRA_API_TOKEN = response.text.strip()
except Exception as e:
    error_msg = f"❌ Error al obtener token: {e}"
    print(error_msg)
    registrar_evento(error_msg)
    exit(1)

# Leer log de la tarea fallida
try:
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        log_content = f.read()
except Exception as e:
    error_msg = f"❌ Error al leer el archivo log: {e}"
    print(error_msg)
    registrar_evento(error_msg)
    exit(1)

# Armar contenido del ticket
summary = f"Tarea fallida - {args.servidor} - {args.empresa}"
description = (
    f"*Empresa:* {args.empresa}\n"
    f"*Servicio:* {args.servicio}\n"
    f"*Servidor:* {args.servidor}\n"
    f"*Tarea fallida:* {args.tarea}\n\n"
    f"*Log:*\n{log_content}"
)

payload = {
    "fields": {
        "project": {"key": JIRA_PROJECT_KEY},
        "summary": summary,
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}]
                }
            ]
        },
        "issuetype": {"name": "Task"},
    }
}

# Crear ticket en Jira
try:
    r = requests.post(
        f"{JIRA_URL}/rest/api/3/issue",
        auth=(JIRA_USER, JIRA_API_TOKEN),
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    r.raise_for_status()
    issue_key = r.json().get("key")
    resultado = f"✅ Ticket creado: {issue_key}"
    print(resultado)
    registrar_evento(resultado)
except Exception as e:
    error_msg = f"❌ Error al crear el ticket: {e} | Respuesta: {r.text}"
    print(error_msg)
    registrar_evento(error_msg)
