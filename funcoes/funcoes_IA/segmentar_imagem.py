from ultralytics import YOLO
from funcoes.enums import Caminho

def segmentar_imagem(image):
    model = YOLO('IA/weights/best-miguel.pt')
    results = model(image)
    return results