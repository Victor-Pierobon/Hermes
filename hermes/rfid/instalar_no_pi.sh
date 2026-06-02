#!/usr/bin/env bash
#
# HERMES — instalador do autostart do leitor RFID (rode ESTE script NO Raspberry Pi).
#
# O que faz:
#   1. confere que o leitor (rfid_reader.py) e o venv existem em ~/hermes
#   2. confere que o usuário tem acesso ao SPI/GPIO (grupos spi e gpio)
#   3. gera o serviço systemd (com SEU usuário, caminhos e o endereço do servidor)
#   4. habilita o serviço para iniciar no boot e o inicia agora
#
# Uso (no Pi):
#   cd ~/hermes
#   bash instalar_no_pi.sh http://10.116.31.40:5000/api/rfid
#
# (se omitir o endereço, usa http://10.116.31.40:5000/api/rfid por padrão)
#
set -euo pipefail

PROJECT_DIR="$HOME/hermes"
SCRIPT="$PROJECT_DIR/rfid_reader.py"
VENV_PY="$PROJECT_DIR/venv/bin/python"
SERVICE_NAME="hermes-rfid"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

# Endereço do servidor no PC. Passe como 1º argumento ou edite o padrão abaixo.
SERVER_URL="${1:-http://10.116.31.40:5000/api/rfid}"
STOP_ID="${STOP_ID:-parada_w3_sul_502}"

echo "==> Usuário: $USER   Home: $HOME"
echo "==> Servidor: $SERVER_URL"
echo "==> Parada:   $STOP_ID"

# 1. arquivos esperados
if [[ ! -f "$SCRIPT" ]]; then
    echo "ERRO: não achei $SCRIPT — copie o rfid_reader.py para ~/hermes/ antes."
    exit 1
fi
if [[ ! -x "$VENV_PY" ]]; then
    echo "ERRO: não achei o venv em $VENV_PY"
    echo "      crie:  cd ~/hermes && python3 -m venv venv && source venv/bin/activate && pip install mfrc522 RPi.GPIO requests"
    exit 1
fi

# 2. acesso a SPI/GPIO (sob systemd o usuário precisa estar nos grupos)
for grp in spi gpio; do
    if ! id -nG "$USER" | tr ' ' '\n' | grep -qx "$grp"; then
        echo "AVISO: usuário '$USER' não está no grupo '$grp'. Adicionando…"
        sudo usermod -aG "$grp" "$USER"
        echo "       -> reinicie o Pi depois, para o grupo valer."
    fi
done

# 3. gerar o serviço systemd
echo "==> Gerando $SERVICE_PATH"
sudo tee "$SERVICE_PATH" >/dev/null <<EOF
[Unit]
Description=HERMES — leitor RFID (RC522) no boot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=SERVER_URL=$SERVER_URL
Environment=STOP_ID=$STOP_ID
ExecStart=$VENV_PY $SCRIPT
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 4. habilitar e iniciar
echo "==> Habilitando e iniciando o serviço"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo
echo "==> Status:"
sudo systemctl --no-pager status "$SERVICE_NAME" || true
echo
echo "Acompanhe as leituras em tempo real com:"
echo "    journalctl -u $SERVICE_NAME -f"
echo
echo "Pronto. A partir de agora basta LIGAR o Pi — o leitor sobe sozinho no boot."
