import os
import cv2
from PIL import Image
import numpy as np
from ultralytics import YOLO
from funcoes.enums import Caminho
from funcoes.funcoes_IA.tratar_imagem import tratar_imagem_cinza
from funcoes.funcoes_IA.porcentagem_nuvem import porcentagem_nuvem
from funcoes.funcoes_IA.processar_resultado import processar_resultado

def criar_mascara_binaria(imagem, path):
    mask = Image.new("L", imagem.size, 0)  # Cria uma imagem preta com o mesmo tamanho da imagem original
    nome_imagem = os.path.splitext(os.path.basename(path))[0]  # Obtém o nome da imagem original
    mask_path = os.path.join(os.path.dirname(path), f"{nome_imagem}_mask.png")
    mask.save(mask_path)
    return mask_path

def redimensionar_imagem(imagem, tamanho=(640, 640)):
    if imagem.shape != tamanho:
        imagem = cv2.resize(imagem, tamanho)
    return imagem

def segmentar_imagem(image, model):
    results = model(image)
    return results

def segmentar_imagens(images_path=Caminho.IMG_TILE.value):
    model = YOLO(Caminho.PESO.value)
    for root, dirs, files in os.walk(images_path):
        for file in files:
            if file.endswith('.png'):
                image_path = os.path.join(root, file)
                print(image_path)
                imagem = cv2.imread(image_path)
                imagem = tratar_imagem_cinza(imagem)
                nome_imagem_original = os.path.splitext(file)[0]
                results = segmentar_imagem(imagem, model)
                output_mask_path, merged_image = processar_resultado(results, imagem, nome_imagem_original)
