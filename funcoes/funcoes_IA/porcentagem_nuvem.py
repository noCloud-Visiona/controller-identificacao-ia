import os
import cv2
import numpy as np
from PIL import Image


def porcentagem_nuvem(mask, img, target_size=(1000, 1000)): 
    if not os.path.exists(img):
        print(f"Imagem não encontrada: {img}")
        return 0
    if not os.path.exists(mask):
        print(f"Mascara não encontrada: {mask}")
        return 0

    try:
        image_pil = Image.open(img)
        image_resized_pil = image_pil.resize(target_size, Image.Resampling.LANCZOS) 
        image_resized = np.array(image_resized_pil)  
    except Exception as e:
        print(f"Erro ao abrir ou redimensionar a imagem: {e}")
        return 0

    print(f"Imagem original tamanho: {image_pil.size}")
    print(f"Tamanho da imagem redimensionada: {image_resized.shape}")

    if image_resized.shape[2] == 4:
        alpha_channel = image_resized[:, :, 3]
        non_transparent_mask = alpha_channel != 0
    else:
        non_transparent_mask = np.ones(image_resized.shape[:2], dtype=bool)
    
    H, W = image_resized.shape[:2]


    try:
        mask_pil = Image.open(mask)
        mask_resized_pil = mask_pil.resize((W, H), Image.Resampling.LANCZOS)
        mask_resized = np.array(mask_resized_pil)  
    except Exception as e:
        print(f"Erro ao abrir ou redimensionar a máscara: {e}")
        return 0
    total_non_transparent_pixels = np.sum(non_transparent_mask)
    masked_pixels = np.sum((mask_resized > 0) & non_transparent_mask)

    print(f"Total de pixels não transparentes: {total_non_transparent_pixels}")
    print(f"Total de pixels com máscara: {masked_pixels}")

    if total_non_transparent_pixels > 0:
        coverage_percentage = (masked_pixels / total_non_transparent_pixels) * 100
        print(f"Porcentagem da imagem coberta pela máscara: {coverage_percentage:.2f}%")
        return coverage_percentage
    else:
        print("Não há pixels válidos para calcular a cobertura.")
        return 0




