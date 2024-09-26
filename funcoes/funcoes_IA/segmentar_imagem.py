from ultralytics import YOLO
from funcoes.enums import Caminho

def segmentar_imagem(image):
    model = YOLO('funcoes/funcoes_IA/best-miguel.pt')
    results = model(image)
    return results