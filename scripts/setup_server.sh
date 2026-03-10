#!/bin/bash
set -e

echo "¡Arrancando el precalentamiento del servidor, papá!"

# 1. Actualizar el sistema
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git tmux sqlite3 libpq-dev python3-dev

# 2. Armar la memoria Swap (2GB) para que el modelo de IA no se ahogue
if [ ! -f /swapfile ]; then
    echo "Armando la memoria de emergencia (Swap)..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "¡Memoria Swap lista!"
else
    echo "¡Ya teníamos Swap, seguimos viaje!"
fi

# 3. Instalar uv (el gestor de paquetes mágico)
if ! command -v uv &> /dev/null; then
    echo "Instalando uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi

echo "¡Servidor listo para salir a jugar!"
