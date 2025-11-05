#!/usr/bin/env bash
set -euo pipefail

# caminho base (onde este script está)
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

# echo "Autentique-se para sudo (será pedido apenas uma vez)..."
# sudo -v

# # manter sudo ativo
# _keep_sudo_alive() {
#   while true; do
#     sleep 30
#     sudo -v || break
#   done
# }
# _keep_sudo_alive & keep_sudo_pid=$!

# 2) Conexão SSH (VM)
xfce4-terminal --title="Vm" --hold -e "bash -lc 'sshpass -p \"ppgcc@ufjf\" ssh -o StrictHostKeyChecking=no -p 11270 \
  -L 3307:localhost:3307 -L 3308:localhost:3308 \
  -L 8088:localhost:8088 -L 5433:localhost:5432 -L 8036:localhost:8036 \
  usuario@200.17.70.211; exec bash'" &
  
# 1) Sobe containers
docker compose up -d
# sleep 5


# 3) pre_api
# xfce4-terminal --title="Pre API" --hold -e "bash -lc 'cd \"$BASE_DIR/pre_api\" && poetry run python app.py; exec bash'" &

# 4) worker
# xfce4-terminal --title="Worker" --hold -e "bash -lc 'cd \"$BASE_DIR/worker\" && poetry run python app.py; exec bash'" &

sleep 1

# encerra o keepalive do sudo
# kill "$keep_sudo_pid" 2>/dev/null || true

clear
echo "Tudo iniciado. Janelas abertas: Vm, Pre API, Worker."
