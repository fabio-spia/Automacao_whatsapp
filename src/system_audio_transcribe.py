import os
import re
import time
import wave

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

import pyaudiowpatch as pyaudio
from faster_whisper import WhisperModel


def _parse_duration_seconds(bubble) -> float:
    """
    Tenta ler a duração exibida na bolha, tipo 0:04 ou 1:12.
    Se falhar, usa um fallback de 8s.
    """
    try:
        candidates = bubble.find_elements(By.XPATH, './/*[contains(text(),":")]')
        for el in candidates:
            t = (el.text or "").strip()
            if re.fullmatch(r"\d{1,2}:\d{2}", t):
                mm, ss = t.split(":")
                return int(mm) * 60 + int(ss)
    except Exception:
        pass
    return 8.0


def _click_play(bubble, driver=None):
    """
    Clica no botao de play do audio.
    """
    xps = [
        './/button[contains(@aria-label,"Reproduzir mensagem de voz")]',
        './/button[contains(@aria-label,"Reproduzir")]',
        './/button[contains(@aria-label,"Play")]',
        './/*[@data-icon="audio-play"]/ancestor::button[1]',
    ]
    last_err = None
    for xp in xps:
        try:
            btn = bubble.find_element(By.XPATH, xp)
            if driver is not None:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.05)
                driver.execute_script("arguments[0].click();", btn)
            else:
                ActionChains(driver).move_to_element(btn).click().perform()
            return True
        except Exception as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    return False


def _record_wasapi_loopback_wav(wav_path: str, seconds: float, sample_rate: int = 48000, channels: int = 2):
    """
    Grava o audio de saida do Windows via WASAPI loopback e salva em WAV PCM16.
    """
    seconds = max(1.0, float(seconds))

    pa = pyaudio.PyAudio()

    wasapi_info = pa.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = pa.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    if not default_speakers.get("isLoopbackDevice", False):
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            name = (dev.get("name") or "").lower()
            if dev.get("hostApi") == wasapi_info["index"] and dev.get("isLoopbackDevice", False):
                if (default_speakers.get("name") or "").lower() in name:
                    default_speakers = dev
                    break

    frames_per_buffer = 1024

    stream = pa.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        input=True,
        input_device_index=default_speakers["index"],
        frames_per_buffer=frames_per_buffer,
    )

    chunks = []
    t0 = time.time()
    while time.time() - t0 < seconds:
        data = stream.read(frames_per_buffer, exception_on_overflow=False)
        chunks.append(data)

    stream.stop_stream()
    stream.close()
    pa.terminate()

    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(chunks))


def transcribe_whatsapp_audio_by_playback(
    driver,
    bubble,
    download_dir: str,
    model: WhisperModel,
    extra_record_seconds: float = 0.8,
) -> str:
    """
    Dá play no audio no WhatsApp, grava o som do sistema, transcreve e retorna texto.
    """
    if not os.path.isdir(download_dir):
        os.makedirs(download_dir, exist_ok=True)

    duration = _parse_duration_seconds(bubble)
    record_seconds = duration + float(extra_record_seconds)

    wav_path = os.path.join(download_dir, f"ptt_loopback_{int(time.time() * 1000)}.wav")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", bubble)
    time.sleep(0.1)

    _click_play(bubble, driver=driver)
    time.sleep(0.1)

    try:
        _record_wasapi_loopback_wav(wav_path, record_seconds)

        segments, _info = model.transcribe(wav_path, vad_filter=True)
        parts = []
        for seg in segments:
            txt = (seg.text or "").strip()
            if txt:
                parts.append(txt)

        return " ".join(parts).strip()

    finally:
        if os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass