import cv2
import numpy as np



def porcentagem_nuvem(mask, img):
    image = cv2.imread(img, cv2.IMREAD_UNCHANGED)
    H, W = image.shape
    mask_path = mask  # Substitua pelo caminho da sua máscara
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE) 
    mask = cv2.resize(mask, (W, H))

    # Se a imagem tiver 4 canais (RGBA), você pode desconsiderar os pixels transparentes
    if image.shape[1] == 4:
        # O canal alfa (transparência) está no índice 3
        alpha_channel = image[:, :, 3]
        # Criar uma máscara binária que identifica os pixels que não são transparentes (alfa != 0)
        non_transparent_mask = alpha_channel != 0
    else:
        # Se a imagem for RGB ou escala de cinza, basta considerar todos os pixels
        non_transparent_mask = np.ones(image.shape[:2], dtype=bool)
    total_non_transparent_pixels = np.sum(non_transparent_mask)

    masked_pixels = np.sum((mask > 0) & non_transparent_mask)
    if total_non_transparent_pixels > 0:
        coverage_percentage = (masked_pixels / total_non_transparent_pixels) * 100
        print(f"Porcentagem da imagem coberta pela máscara: {coverage_percentage:.2f}%")
        return coverage_percentage
    else:
        print("Não há pixels válidos para calcular a cobertura.")
        return 0





