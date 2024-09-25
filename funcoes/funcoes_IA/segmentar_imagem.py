from ultralytics import YOLO
from enums import Caminho

def segmentar_imagem(image):
    model = YOLO(Caminho.PESO.value)
    results = model(image)
    return results