from datetime import datetime
import csv
from config import get_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from extract_mensages import extract_last_mensage
from util import add_mensage, lost_deals_followup, humanized_writing, lost_deals, add_perdidos, add_inconsistencia, get_stage_name, get_deals
from training import open_conversation
import time
import random

#Funçao enviar mensagem
def send_menssage(driver, Menssagem):
    campo_mensagem = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,'(//div[@role="textbox"])[last()]')))
    humanized_writing(campo_mensagem, Menssagem)
    time.sleep(random.randint(1,5))
    campo_mensagem.send_keys(Keys.ENTER)
    print("Mensagem enviada!")
    return





if __name__ == "__main__":
    
    choise = input("Oque voce deseja que o SALES faça agora ?\n1- Mandar menssagem para negocios perdidos\n2- Fazer follow-up de todos os negocios perdidos\n3- Fazer follow-up de negocios abertos\n4- Mandar menssagem para uma lista")
    driver = get_driver()
    driver.get("https://web.whatsapp.com/")
    time.sleep(random.randint(1,5))
    if choise =="1":
        deals = lost_deals()#Pegar os negocios perdidos no pipedrive
        for deal in deals:
            print("Enviando mensagem para "+deal['title'])
            if open_conversation(driver, deal['phone']) == False:#Caso não encontre o contato, registra como inconsistencia
                add_inconsistencia(deal['id_negocio'],deal['title'],"Contato não encontrado")
                continue       
            time.sleep(random.randint(1,5))
            send_menssage(driver, deal['mensage'])
            msg = extract_last_mensage(driver)
            remetente = "SALES"
            msg = {
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
            }            
            add_mensage(msg)
            add_perdidos(deal['id_negocio'], deal['mensage'])#Registra a tentativa de reativação
            time.sleep(random.randint(1,5)) 




    if choise=="2":
        deals = lost_deals_followup()
        if not deals:
            print("Nenhum deal encontrado")
            deals = []
        for deal in deals:
            open_conversation(driver, deal['phone'])
            print("\n"+deal['title']+"\n")
            print(deal['sugestao']+"\n\n")
            choise2 = input("Você enviou mensagem ?\n1- SIM\n2- NÃO")
            if choise2=='1':
                msg = extract_last_mensage(driver)
                remetente = "SALES"
                msg = {
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
                }            
                add_mensage(msg)

    if choise == "3":
        deals = get_deals("aberto")
        while True:
            for deal in deals:
                print(str(deal['id_negocio'])+" : "+deal['title'])
            id_deal = input("Digite o ID do negocio que quer fazer folowup")
            deal = next((d for d in deals if str(d["id_negocio"]) == id_deal), None)
            open_conversation(driver, deal['phone'])
            choise2 = input("Você enviou mensagem ?\n1- SIM\n2- NÃO")
            while choise2=='1':
                    msg = extract_last_mensage(driver)
                    print("Conteúdo:", msg['text'])
                    remetente = "SALES"
                    msg = {
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
                    }            
                    add_mensage(msg)
                    print("Mensagens salvas")
                    choise2 = input("Você enviou outra mensagem ?\n1- SIM\n2- NÃO")
            choise = input("Deseja fazer folowup de outro negocio ?\n1- SIM\n2- NÃO")
            if choise != "1":
                break

    if choise == "4":
        arquivo_csv = "src/leads.csv"
        with open(arquivo_csv, mode="r", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            for linha in leitor:
                print("\n\nEnviando mensagem para ")
                mensagem = ""
                print(mensagem)
                if open_conversation(driver, "Telefone")== False:
                    with open("src/erro.csv", "a", newline="", encoding="utf-8") as arquivo:
                        escritor = csv.writer(arquivo)
                        escritor.writerow([linha])
                send_menssage(driver,mensagem)
                time.sleep(random.randint(15,60))

