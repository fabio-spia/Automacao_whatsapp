import random
from enum import Enum
from selenium.webdriver.common.keys import Keys
import time
import requests
import re
import os
from dotenv import load_dotenv

load_dotenv("credentials/.env")

N8N_WEBHOOK_GET_DEALS = os.getenv("N8N_WEBHOOK_GET_DEALS")
N8N_WEBHOOK_GET_MSGS = os.getenv("N8N_WEBHOOK_GET_MSGS")
N8N_WEBHOOK_ADD_MSG = os.getenv("N8N_WEBHOOK_ADD_MSG")
N8N_WEBHOOK_ADD_INCONS = os.getenv("N8N_WEBHOOK_ADD_INCONS")
N8N_WEBHOOK_ADD_LOSTS = os.getenv("N8N_WEBHOOK_ADD_LOSTS")
N8N_WEBHOOK_LOST_DEALS = os.getenv("N8N_WEBHOOK_LOST_DEALS")
N8N_WEBHOOK_LOST_DEALS_FOLLOWUP = os.getenv("N8N_WEBHOOK_LOST_DEALS_FOLLOWUP")


class status(Enum):
    ABERTO = "aberto"
    GANHO = "ganho"
    PERDIDO = "perdido"

def clear_field(campo):
    campo.click()
    campo.send_keys(Keys.CONTROL + "a")
    time.sleep(2)
    campo.send_keys(Keys.DELETE)

def humanized_writing(field, text):
    for char in text:
        try:
            if char == "&":
                time.sleep(1)
                field.send_keys(Keys.ENTER)    
            else:
                field.send_keys(char)
        except:
            pass
        time.sleep(random.uniform(0.05, 0.5))

def get_deals(status: status):
    payload = {
        "status": status
    }

    try:
        resp = requests.post(
            N8N_WEBHOOK_GET_DEALS,
            json=payload,
            timeout=90
        )

        resp.raise_for_status()

        dados = resp.json()

        
        return dados

    except requests.exceptions.RequestException as e:
        print(f"Erro na chamada ao n8n: {e}")
    except ValueError:
        print("O n8n não retornou JSON válido")

def import_dataset(status):
    payload = {
        "status": status
    }

    try:
        resp = requests.post(
            N8N_WEBHOOK_GET_MSGS,
            json=payload,
            timeout=90
        )

        resp.raise_for_status()

        dados = resp.json()

        print("Resposta do n8n:")
        print(dados)
        return dados

    except requests.exceptions.RequestException as e:
        print(f"Erro na chamada ao n8n: {e}")
    except ValueError:
        print("O n8n não retornou JSON válido")

def add_mensage(mensagens):
    try:
        response = requests.post(N8N_WEBHOOK_ADD_MSG, json={"messages": mensagens},timeout=5)
        response.raise_for_status()
        print("Webhook enviado com sucesso!")
        print(response.text)
    except requests.exceptions.RequestException as e:
        print("Erro ao enviar webhook:", e)

def add_inconsistencia(id, title, tipo):
    payload = {
        "id" : int(id), 
        "title" : title,
        "tipo" : tipo
    }
    try:
        response = requests.post(N8N_WEBHOOK_ADD_INCONS, json=payload, timeout=5)
        response.raise_for_status()
        print("Webhook enviado com sucesso!")
        print(response.text)
    except requests.exceptions.RequestException as e:
        print("Erro ao enviar webhook:", e)

def add_perdidos(id, mensage):
    payload = {
        "id" : int(id), 
        "mensage" : mensage
    }
    try:
        response = requests.post(N8N_WEBHOOK_ADD_LOSTS, json=payload, timeout=5)
        response.raise_for_status()
        print("Webhook enviado com sucesso!")
        print(response.text)
    except requests.exceptions.RequestException as e:
        print("Erro ao enviar webhook:", e)


def lost_deals():
    try:
        resp = requests.post(
            N8N_WEBHOOK_LOST_DEALS,
            timeout=90
        )
        resp.raise_for_status()
        dados = resp.json()
        return dados
    except requests.exceptions.RequestException as e:
        print(f"Erro na chamada ao n8n: {e}")
    except ValueError:
        print("O n8n não retornou JSON válido")

def lost_deals_followup():
    try:
        resp = requests.post(
            N8N_WEBHOOK_LOST_DEALS_FOLLOWUP,
            timeout=120
        )
        resp.raise_for_status()
        dados = resp.json()
        return dados
    except requests.exceptions.RequestException as e:
        print(f"Erro na chamada ao n8n: {e}")
    except ValueError:
        print("O n8n não retornou JSON válido")

def normalizar_adicionando_9(numero):
    # remove tudo que não for número
    n = re.sub(r'\D', '', str(numero))

    # remove código do país se já existir
    if n.startswith("55"):
        n = n[len("55"):]

    # precisa ter pelo menos DDD + telefone
    if len(n) < 10:
        return None

    ddd = n[:2]
    telefone = n[2:]

    # se tiver 8 dígitos, adiciona 9
    if len(telefone) == 8:
        telefone = "9" + telefone

    return f"+55{ddd}{telefone}"



def normalizar_removendo_9(numero):
    # remove caracteres
    n = re.sub(r'\D', '', str(numero))

    # remove código do país
    if n.startswith("55"):
        n = n[len("55"):]

    if len(n) < 10:
        return None

    ddd = n[:2]
    telefone = n[2:]

    # remove o 9 inicial se existir
    if len(telefone) == 9 and telefone.startswith("9"):
        telefone = telefone[1:]

    return f"+55{ddd}{telefone}"

def get_stage_name(stage_id) -> str:
    stage_map = {
        "1": "Qualificação",
        "2": "Qualificado",
        "17": "Alinhamento",
        "6": "Preparando Proposta",
        "12": "Proposta Pronta",
        "3": "Proposta Enviada",
        "16": "Quente"
    }
    
    return stage_map.get(stage_id, "Etapa desconhecida")
