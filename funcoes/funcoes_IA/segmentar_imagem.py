import os
import cv2
from PIL import Image
import numpy as np
from ultralytics import YOLO
from funcoes.enums import Caminho
from funcoes.funcoes_IA.tratar_imagem import tratar_imagem_rgb
from funcoes.funcoes_IA.processar_resultado import processar_resultado

def criar_mascara_binaria(imagem, path):
    print("Criando máscara binária...")
    mask = Image.new("L", imagem.size, 0)  # Cria uma imagem preta com o mesmo tamanho da imagem original
    nome_imagem = os.path.splitext(os.path.basename(path))[0]  # Obtém o nome da imagem original
    mask_path = os.path.join(os.path.dirname(path), f"{nome_imagem}_mask.png")
    mask.save(mask_path)
    return mask_path

def redimensionar_imagem(imagem, tamanho=(640, 640)):
    print("Redimensionando a imagem...")
    if imagem.shape != tamanho:
        imagem = cv2.resize(imagem, tamanho)
    return imagem

def segmentar_imagem(image, model):
    print("Segmentando a imagem...")
    results = model(image)
    return results

#esse novo filtro verifica se a nuvem cobre quase a tela inteira, manualmente dando true caso tenha 
#mais de 60% ou 30% de cor branca e cinza predominante na imagem dentro do range, se for 
#ele muda a variavel custom para True, usando uma mask pre definida no processar_resultado
def filtro_nuvem_grande(file_path):
    dark_threshold = 0.3
    light_threshold = 0.6
    tolerance_range = (100, 255)

    try:
        # Abre a imagem e converte para RGB
        img = Image.open(file_path).convert("RGB")
        pixels = list(img.getdata())
        total_pixels = len(pixels)

        # Conta pixels dentro do intervalo de tons de cinza
        gray_pixels = sum(
            1
            for pixel in pixels
            if tolerance_range[0] <= pixel[0] <= tolerance_range[1]
            and tolerance_range[0] <= pixel[1] <= tolerance_range[1]
            and tolerance_range[0] <= pixel[2] <= tolerance_range[1]
        )
        gray_ratio = gray_pixels / total_pixels

        # Classifica como 'nuvem grande' se o critério for atendido
        return gray_ratio >= dark_threshold or gray_ratio >= light_threshold
    except Exception as e:
        print(f"Erro ao processar o filtro em {file_path}: {e}")
        return False

def segmentar_imagens(images_path=Caminho.IMG_TILE.value):
    print("Segmentando imagens...")
    model = YOLO(Caminho.PESO.value)  
    for root, dirs, files in os.walk(images_path):
        for file in files:
            if file.lower().endswith(('.png')):
                image_path = os.path.join(root, file)
                print(image_path)
                imagem = cv2.imread(image_path)
                nome_imagem_original = os.path.splitext(file)[0]
                usar_modelo_nuvem_tela_inteira = filtro_nuvem_grande(image_path)
                
                if usar_modelo_nuvem_tela_inteira:
                    results = segmentar_imagem(imagem, model)
                    print("Nuvem tela inteira")

                    nuvem_tela_inteira = True
                    processar_resultado(results, imagem, nome_imagem_original, nuvem_tela_inteira)
                else:
                    results = segmentar_imagem(imagem, model)
                    print("Nuvem e sombra")
                    
                    nuvem_tela_inteira = False
                    processar_resultado(results, imagem, nome_imagem_original, nuvem_tela_inteira)
