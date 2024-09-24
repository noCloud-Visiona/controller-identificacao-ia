from ultralytics import YOLO
from enums import Caminho

def segmentar_imagem(imagem_tratada):
    model = YOLO(Caminho.PESO.value)
    results = model(imagem_tratada)
    return results