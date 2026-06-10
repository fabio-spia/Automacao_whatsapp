from datetime import datetime, timedelta
import re
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from faster_whisper import WhisperModel
from system_audio_transcribe import transcribe_whatsapp_audio_by_playback

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
WHISPER_MODEL = None

def get_whisper_model():
    global WHISPER_MODEL

    if WHISPER_MODEL is None:
        model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

        WHISPER_MODEL = WhisperModel(
            model_size,
            device="cpu",
            compute_type=compute_type,
            cpu_threads=max(1, (os.cpu_count() or 4) - 1),
            num_workers=1
        )

    return WHISPER_MODEL


# ========================= ROOT DA MENSAGEM =========================
def get_message_root(el):
    xps = [
        './ancestor::div[@data-id][1]',
        './ancestor::div[@role="row"][1]',
        './ancestor::div[contains(@class,"message-in") or contains(@class,"message-out")][1]',
    ]

    for xp in xps:
        try:
            root = el.find_element(By.XPATH, xp)
            if root:
                return root
        except Exception:
            pass

    return el


# ========================= TIMESTAMP =========================
def get_pre_plain_text(root) -> str:
    try:
        v = root.get_attribute("data-pre-plain-text")
        if v:
            return v
    except Exception:
        pass

    xps = [
        './/div[@data-pre-plain-text]',
        './/*[@data-pre-plain-text]',
    ]

    for xp in xps:
        try:
            els = root.find_elements(By.XPATH, xp)
            for el in els:
                v = (el.get_attribute("data-pre-plain-text") or "").strip()
                if v:
                    return v
        except Exception:
            pass

    return ""


def parse_pre_plain_text(pre_plain_text):
    if not pre_plain_text:
        return {"timestamp": None, "author": None}

    m = re.match(r"^\[(.*?)\]\s*(.*?):\s*$", pre_plain_text.strip())
    if not m:
        return {"timestamp": None, "author": None}

    dt = datetime.strptime(m.group(1).strip(), "%H:%M, %d/%m/%Y")
    return {"timestamp": dt, "author": m.group(2).strip()}


# ========================= TIPOS =========================
def _is_pdf_bubble(root):
    markers = [
        './/*[@data-icon="document-PDF-icon"]',
        './/*[contains(@title, ".pdf") or contains(@title, ".PDF")]',
        './/span[contains(text(), ".pdf") or contains(text(), ".PDF")]',
    ]
    for xp in markers:
        try:
            root.find_element(By.XPATH, xp)
            return True
        except Exception:
            pass
    return False


def extract_pdf_title_from_bubble(root) -> str:
    candidates = [
        './/span[contains(text(), ".pdf") or contains(text(), ".PDF")]',
        './/*[@title[contains(., ".pdf") or contains(., ".PDF")]]',
    ]

    for xp in candidates:
        try:
            elements = root.find_elements(By.XPATH, xp)
            for el in elements:
                text = (el.text or el.get_attribute("title") or "").strip()
                if text and ".pdf" in text.lower():
                    return text
        except Exception:
            pass

    return "[PDF]"


def _is_audio_bubble(root):
    markers = [
        './/*[@data-testid="audio-play"]',
        './/*[@data-testid="audio-message"]',
        './/*[contains(@aria-label,"Reproduzir") or contains(@aria-label,"Play")]',
    ]
    for xp in markers:
        try:
            root.find_element(By.XPATH, xp)
            return True
        except Exception:
            pass
    return False


# ========================= UTIL =========================
def conversation_to_string(messages):
    linhas = []
    linhas.append("\n================ CONVERSA =================\n")

    for m in messages:
        ts = m["timestamp"] or "sem data"
        linha = f"{m['id']} - [{ts}] ({m['direction']}) {m['text']}"
        linhas.append(linha)
        linhas.append("")

    linhas.append("==========================================\n")
    return "\n".join(linhas)


def rolar_conversa_ate_topo(driver):
    chat = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div[data-scrolltracepolicy="wa.web.conversation.messages"]')
        )
    )

    ultimo = None
    for _ in range(50):
        atual = driver.execute_script("return arguments[0].scrollTop;", chat)
        driver.execute_script("arguments[0].scrollTop = 0;", chat)
        time.sleep(1)
        novo = driver.execute_script("return arguments[0].scrollTop;", chat)
        if novo == 0 or novo == ultimo:
            break
        ultimo = novo


# ========================= MAIN =========================
def extract_recent_messages(driver, id_msg=None):
    time.sleep(10)
    rolar_conversa_ate_topo(driver)
    time.sleep(5)

    messages_xpath = '//div[@data-id]'
    last_exception = None

    for _ in range(3):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, messages_xpath))
            )

            msg_roots = driver.find_elements(By.XPATH, messages_xpath)
            tail = msg_roots[-100:] if len(msg_roots) > 100 else msg_roots
            items = []

            for msg_root in tail:
                try:

                    message_id = msg_root.get_attribute("data-id")

                    if not message_id:
                        print("ID NÃO ENCONTRADO")
                        return
                    if id_msg:
                        if message_id in id_msg:
                            continue

                    root = get_message_root(msg_root)

                    html = root.get_attribute("innerHTML") or ""
                    if "message-in" in html:
                        direction = "recebida"
                    elif "message-out" in html:
                        direction = "enviada"
                    else:
                        direction = "desconhecida"

                    pre_plain = get_pre_plain_text(root)
                    meta = parse_pre_plain_text(pre_plain)

                    
                    # ÁUDIO
                    if _is_audio_bubble(root):
                        if items:
                            timestamp = items[-1]["timestamp"] + timedelta(minutes=1)
                        else:
                            timestamp = meta["timestamp"]
                        try:
                            transcricao = transcribe_whatsapp_audio_by_playback(
                                driver=driver,
                                bubble=root,
                                download_dir=DOWNLOAD_DIR,
                                model=get_whisper_model(),
                            )
                            items.append({
                                "id": message_id,
                                "direction": direction,
                                "timestamp": timestamp,
                                "author": meta["author"],
                                "text": transcricao.strip() if transcricao else "[AUDIO]",
                            })
                        except Exception as e:
                            items.append({
                                "id": message_id,
                                "direction": direction,
                                "timestamp": timestamp,
                                "author": meta["author"],
                                "text": f"[AUDIO] erro: {e}",
                            })
                        
                        continue

                    # PDF
                    if _is_pdf_bubble(root):
                        if items:
                            timestamp = items[-1]["timestamp"] + timedelta(minutes=1)
                        else:
                            timestamp = meta["timestamp"]

                        pdf_title = extract_pdf_title_from_bubble(root)
                        items.append({
                            "id": message_id,
                            "direction": direction,
                            "timestamp": timestamp,
                            "author": meta["author"],
                            "text": pdf_title,
                        })
                        continue

                    # TEXTO
                    text = ""
                    try:
                        text_els = root.find_elements(By.XPATH, './/*[@data-testid="selectable-text"]')
                        parts = []
                        for el in text_els:
                            t = (el.text or "").strip()
                            if t:
                                parts.append(t)
                        text = "\n".join(parts).strip()
                    except Exception:
                        pass

                    if not text:
                        continue

                    items.append({
                        "id": message_id,
                        "direction": direction,
                        "timestamp": meta["timestamp"],
                        "author": meta["author"],
                        "text": text,
                    })

                except StaleElementReferenceException:
                    continue

            if not items:
                return False

            #return conversation_to_string(items) #TESTE
            return items

        except (StaleElementReferenceException, TimeoutException) as e:
            last_exception = e
            continue

    if last_exception:
        raise last_exception

    return ""
#Pega a ultima mensagem enviada
def extract_last_mensage(driver):
    time.sleep(10)
    messages_xpath = '//div[@data-id]'
    last_exception = None

    for _ in range(3):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, messages_xpath))
            )

            msg_roots = driver.find_elements(By.XPATH, messages_xpath)
            
            for msg_root in reversed(msg_roots):
                try:
                    message_id = msg_root.get_attribute("data-id")

                    if not message_id:
                        print("ID NÃO ENCONTRADO")
                        return

                    root = get_message_root(msg_root)

                    html = root.get_attribute("innerHTML") or ""
                    if 'data-testid="tail-in"' in html:
                        continue
                    elif 'data-testid="tail-out"' in html or 'aria-label="Você:"' in html:
                        direction = "enviada"
                    else:
                        continue

                    pre_plain = get_pre_plain_text(root)
                    meta = parse_pre_plain_text(pre_plain)

                    # TEXTO
                    text = ""
                    try:
                        text_els = root.find_elements(By.XPATH, './/*[@data-testid="selectable-text"]')
                        parts = []
                        for el in text_els:
                            t = (el.text or "").strip()
                            if t:
                                parts.append(t)
                        text = "\n".join(parts).strip()
                    except Exception:
                        pass

                    if not text:
                        continue

                    msg = {
                        "id": message_id,
                        "direction": direction,
                        "timestamp": meta["timestamp"],
                        "author": meta["author"],
                        "text": text
                    }
                    return msg
                except StaleElementReferenceException:
                    continue
            

        except (StaleElementReferenceException, TimeoutException) as e:
            last_exception = e
            continue

    if last_exception:
        raise last_exception

    return ""