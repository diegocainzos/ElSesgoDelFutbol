#!/bin/bash
set -e

PEM_FILE="$HOME/Downloads/elsesgodelfutbol.pem"
IP="16.170.218.146"

if [ -z "$PEM_FILE" ]; then
    echo "¡Eeeh, pibe! Me tenés que pasar la ruta a la llave .pem."
    exit 1
fi

echo "Tirando la pelota larga (Copiando archivos al servidor)..."
# Excluimos las cosas pesadas y .git
rsync -avz --exclude='.venv' --exclude='.git' --exclude='__pycache__' --exclude='data/articles.db' -e "ssh -i $PEM_FILE -o StrictHostKeyChecking=no" ./ ubuntu@$IP:~/elsesgodelfutbol/

echo "¡Archivos en la cancha! Levantando el equipo con Docker Compose..."
ssh -i "$PEM_FILE" -o StrictHostKeyChecking=no ubuntu@$IP "cd elsesgodelfutbol && sudo docker compose up -d --build"

echo ""
echo "================================================================"
echo "¡LISTO, MAESTRO! El equipo está en la cancha jugando con Docker."
echo "Para ver si los pibes están corriendo bien, entrá a:"
echo "ssh -i $PEM_FILE ubuntu@$IP"
echo "Y tirá un: sudo docker compose ps"
echo "================================================================"
