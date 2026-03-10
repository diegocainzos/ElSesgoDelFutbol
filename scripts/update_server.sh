#!/bin/bash
set -e

echo "¡Bajando la pelota de Git (Actualizando código)...!"
git pull origin main

echo "Re-armando la burbuja (Reconstruyendo Docker)..."
sudo docker compose up -d --build

echo "¡Listo, pibe! El equipo está en la cancha con los cambios nuevos."

