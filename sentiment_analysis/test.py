from transformers import pipeline


# Modelo de sentimiento español entrenado en BERT
MODEL_NAME = "pysentimiento/robertuito-sentiment-analysis"

classifier = pipeline('sentiment-analysis', model=MODEL_NAME)  #
test_phrases = [
    # --- Positivas ---
    "La película fue absolutamente increíble, la volvería a ver mil veces.",
    "El servicio al cliente fue excepcionalmente rápido y amable.",
    "Me encanta cómo este producto resuelve todos mis problemas diarios.",
    "Es la mejor experiencia que he tenido en un restaurante este año.",
    
    # --- Negativas ---
    "El pedido llegó tarde y la comida estaba completamente fría.",
    "Es una pérdida de tiempo y dinero, no lo recomiendo para nada.",
    "La interfaz es confusa y la aplicación se cierra sola constantemente.",
    "Sinceramente, esperaba mucho más después de leer las reseñas.",
    
    # --- Neutras / Informativas ---
    "El paquete fue entregado el martes por la tarde.",
    "La duración del evento es de aproximadamente tres horas.",
    "El dispositivo tiene una pantalla de seis pulgadas y es de color gris.",
    
    # --- Desafíos (Sarcasmo, Negación, Ambigüedad) ---
    "No es que sea malo, pero definitivamente no es para mí.", # Negación suave
    "¡Genial! Otra actualización que rompe todo lo que funcionaba bien.", # Sarcasmo
    "No puedo decir que no me haya gustado el final.", # Doble negación (Positivo)
    "El diseño es bonito, pero la funcionalidad es un desastre total.", # Sentimiento mixto
    "Al principio tenía mis dudas, pero ahora estoy gratamente sorprendido." # Cambio de opinión
]
print(classifier(test_phrases))
