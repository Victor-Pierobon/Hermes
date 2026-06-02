#!/usr/bin/env python3
"""
HERMES — Leitor RFID do Raspberry Pi (RC522).

Roda NO Raspberry Pi, não no PC do servidor.

Função única: ler o UID do cartão e fazer um POST HTTP ao servidor, disparando
o MESMO evento que o botão da parada dispara ("origem única, gatilhos múltiplos").
Se o Pi falhar no palco, o botão da tela continua como plano B infalível.

Uso (no Pi, com o venv ativo):
    source ~/sapid/venv/bin/activate
    python3 rfid_reader.py

Configuração via variáveis de ambiente (opcional):
    SERVER_URL=http://192.168.1.11:5000/api/rfid python3 rfid_reader.py
    STOP_ID=parada_w3_sul_506 python3 rfid_reader.py
"""

import os
import sys
import time

import requests

# ── configuração ──────────────────────────────────────────────────────────────
# Endereço do servidor Flask (roda no PC). Usamos o nome mDNS "nitrov.local" em
# vez de um IP fixo: assim, mesmo em hotspot de celular (onde o IP do PC muda a
# cada conexão), o Pi sempre encontra o PC pelo nome. Pi e PC na MESMA rede.
# Se precisar, sobreponha com IP direto: SERVER_URL=http://192.168.x.x:5000/api/rfid
SERVER_URL = os.environ.get("SERVER_URL", "http://nitrov.local:5000/api/rfid")

# Parada que este leitor representa (deve existir em data/transit_data.json).
STOP_ID = os.environ.get("STOP_ID", "parada_w3_sul_502")

# Tempo (s) ignorando releituras após um envio — evita spam ao segurar o cartão.
COOLDOWN_S = float(os.environ.get("COOLDOWN_S", "3"))

# Timeout (s) do POST — curto para a demo não travar se a rede cair.
HTTP_TIMEOUT_S = float(os.environ.get("HTTP_TIMEOUT_S", "4"))


def enviar_solicitacao(uid: str) -> None:
    """Faz o POST ao servidor. Nunca derruba o loop: erro de rede só avisa."""
    payload = {"uid": str(uid), "stop_id": STOP_ID}
    try:
        resp = requests.post(SERVER_URL, json=payload, timeout=HTTP_TIMEOUT_S)
        resp.raise_for_status()
        req_id = resp.json().get("request_id", "?")
        print(f"  ✔ solicitação enviada (request_id={req_id})")
    except requests.exceptions.ConnectionError:
        print(f"  ✖ servidor inacessível em {SERVER_URL}")
        print("    confira: servidor rodando? Pi e PC na mesma rede? IP correto?")
    except requests.exceptions.Timeout:
        print(f"  ✖ timeout ({HTTP_TIMEOUT_S}s) — rede lenta ou servidor ocupado")
    except requests.exceptions.RequestException as exc:
        print(f"  ✖ falha no envio: {exc}")


def main() -> None:
    # Importado aqui (e não no topo) para a mensagem de erro ser clara se as
    # libs de hardware não estiverem instaladas — elas só existem no Pi.
    try:
        from mfrc522 import SimpleMFRC522
        import RPi.GPIO as GPIO
    except ImportError:
        print("ERRO: este script roda NO Raspberry Pi.")
        print("Instale as libs de hardware no venv do Pi:")
        print("    pip install mfrc522 RPi.GPIO requests")
        sys.exit(1)

    reader = SimpleMFRC522()

    print("HERMES — leitor RFID ativo")
    print(f"  servidor : {SERVER_URL}")
    print(f"  parada   : {STOP_ID}")
    print("  aproxime um cartão do leitor (Ctrl+C para sair)\n")

    ultimo_uid = None
    ultimo_envio = 0.0

    try:
        while True:
            # read_id() bloqueia até um cartão encostar e devolve o UID. Só lê,
            # nunca grava — o cartão permanece intacto e reutilizável.
            uid = reader.read_id()
            agora = time.time()

            # Debounce: ignora o mesmo cartão repetido dentro do cooldown.
            if uid == ultimo_uid and (agora - ultimo_envio) < COOLDOWN_S:
                continue

            print(f"Cartão lido — UID: {uid}")
            enviar_solicitacao(uid)
            ultimo_uid = uid
            ultimo_envio = agora

            # Pausa breve para o cartão sair do campo antes de reler.
            time.sleep(COOLDOWN_S)
    except KeyboardInterrupt:
        print("\nencerrando…")
    finally:
        # Libera os pinos GPIO; sem isso a próxima execução reclama que estão ocupados.
        GPIO.cleanup()


if __name__ == "__main__":
    main()
