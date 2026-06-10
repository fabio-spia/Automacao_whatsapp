# ANTES DE EXECUTAR, SIGA ESSES PASSOS
# 1- Crie uma pasta para ficar um browser exclusivo para a automação
# 2- Na primeira vez que executar esse codigo scanei o qrcode 
import subprocess
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe" #Caminho do chrome
USER_DATA_DIR = r"C:\ChromeBot" #Pasta para o chrome da automação
DEBUG_PORT = 9222

def chrome_ja_esta_aberto():
    try:
        requests.get(f"http://127.0.0.1:{DEBUG_PORT}/json", timeout=1)
        return True
    except:
        return False

def abrir_chrome_debug():
    if chrome_ja_esta_aberto():
        print("Chrome já está rodando em modo debug.")
        return

    comando = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA_DIR}"
    ]

    subprocess.Popen(comando)
    print("Abrindo Chrome...")

    time.sleep(5)

def conectar_no_chrome():
    options = Options()
    options.debugger_address = f"127.0.0.1:{DEBUG_PORT}"

    driver = webdriver.Chrome(options=options)
    return driver

def get_driver():
    abrir_chrome_debug()
    driver = conectar_no_chrome()

    print("Conectado com sucesso!")
    print("Título:", driver.title)

    return driver



