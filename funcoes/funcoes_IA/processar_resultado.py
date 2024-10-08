import cv2
import numpy as np

def mascara_binaria(image, nome_imagem_original, H, W):
    print("Nenhuma detecção encontrada, criando uma máscara completamente preta.")
        
    # Cria uma máscara preta (todos os pixels com valor 0)
    mask = np.zeros((H, W), dtype=np.uint8)
    
    # Salva a máscara preta
    output_mask_path = f"IA/img_mark_e_merged/{nome_imagem_original}_masked_output_0.png"
    cv2.imwrite(output_mask_path, mask)

    mask_color = np.zeros((H, W, 3), dtype=np.uint8) 
    merged_image = cv2.addWeighted(image, 0.7, mask_color, 0.3, 0)
    merged_output_path = f"IA/img_mark_e_merged/{nome_imagem_original}_merged_0.png"
    cv2.imwrite(merged_output_path, merged_image)
    print(f"Mascara preta salva como {output_mask_path}")
    print(f"Imagem mesclada salva como {merged_output_path}")
    return output_mask_path, merged_image

def processar_resultado(results, image, nome_imagem_original):

    W, H, _ = image.shape  # Tamanho da imagem original

    # Se não houver resultados ou as máscaras estiverem vazias
    if not results or len(results[0].masks) == 0:
        output_mask_path, merged_image = mascara_binaria(image, nome_imagem_original, H, W)
        return output_mask_path, merged_image
    
    # Processar os resultados
    for result in results:
        for j, mask in enumerate(result.masks.data):
            mask = mask.numpy()
            W, H, _ = image.shape
            mask = cv2.resize(mask, (W, H)) 

            output_mask_path = f"IA/img_mark_e_merged/{nome_imagem_original}_masked_output_{j}.png.png"  # Nome do arquivo para a máscara
            cv2.imwrite(output_mask_path, mask * 255)  

            mask_img = cv2.imread(output_mask_path, cv2.IMREAD_GRAYSCALE)

            mask_color = np.zeros((*mask_img.shape, 3), dtype=np.uint8)  # Imagem colorida em 3 canais
            mask_color[mask_img > 0] = [0, 0, 255]  # Cor vermelha onde a máscara é aplicada
    
            merged_image = cv2.addWeighted(image, 0.7, mask_color, 0.3, 0) 
            merged_output_path = f"IA/img_mark_e_merged/{nome_imagem_original}_merged_{j}.png"
            cv2.imwrite(merged_output_path, merged_image)

            print(f"Merge completo. Imagem salva como {nome_imagem_original}_merged_{j}.png .")

            return output_mask_path, merged_image

