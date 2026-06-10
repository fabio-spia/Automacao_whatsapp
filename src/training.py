import random
import time
from config import get_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from extract_mensages import extract_recent_messages 
from util import get_stage_name, get_deals, humanized_writing, clear_field, add_mensage, normalizar_adicionando_9, normalizar_removendo_9, add_inconsistencia







def open_conversation(driver, Number):
    
    try:    
        WebDriverWait(driver,60).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Nova conversa"]'))).click()
    except TimeoutException:
        print("Botão não apareceu. Seguindo sem clicar.")
    campo_pesquisa = WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="Pesquisar nome ou número"]')))
    Number = normalizar_adicionando_9(Number)
    time.sleep(random.randint(1,5))
    humanized_writing(campo_pesquisa, Number)
    time.sleep(random.randint(1,5))
    try:
        el = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-tab="4"][role="button"]'))
        )
        driver.execute_script("arguments[0].click();", el)
    except TimeoutException:
        clear_field(campo_pesquisa)
        Number = normalizar_removendo_9(Number)
        humanized_writing(campo_pesquisa, Number)
        try:
            el = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-tab="4"][role="button"]'))
            )
            driver.execute_script("arguments[0].click();", el)
        except TimeoutException:
            print("Nenhum contato encontrado!")
            clear_field(campo_pesquisa)
            return False
    print("Contato encontrado")
    






if __name__ == "__main__":
    
    deals = get_deals("aberto")
    driver = get_driver()
    driver.get("https://web.whatsapp.com/")
    for deal in deals:
        print(f"Extraindo conversas de {deal['name']}")
        if deal['phone'] == '':
            print("Sem telefone")
            add_inconsistencia(deal['id_negocio'],deal['title'],"Sem telefone")
            continue
        if open_conversation(driver, deal['phone']) == False:
            print("Contato não encontrado")
            add_inconsistencia(deal['id_negocio'],deal['title'],"Contato não encontrado")
            continue
        ids = deal.get('ids_msg') or []
        conversa = extract_recent_messages(driver, ids)
        print(conversa)
        if conversa == False:
            print("Sem mensagens")
            if not deal.get('ids_msg'):
                add_inconsistencia(deal['id_negocio'],deal['title'],"Sem mensagens")
            continue
        mensagens = []
        for msg in conversa:
            remetente="Pedro"
            if msg['direction']=="recebida":
                remetente = deal['name']
            mensagens.append({
            "id": msg['id'],
            "mensagem": msg['text'],
            "timestamp_datahora_msg": str(msg['timestamp']),
            "timestamp_datahora_lido": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "numero_vendedor": "5511934072566",
            "numero_cliente": deal['phone'],
            "mensagem_enviada_por": remetente,
            "crm_negocio_etapa": get_stage_name(deal['stage_id']),
            "crm_negocio_status": deal['status'],
            "crm_negocio_id": int(deal['id_negocio']),
            "crm_pessoa_id": int(deal['id_pessoa'])
        })
        add_mensage(mensagens)
    driver.quit()



