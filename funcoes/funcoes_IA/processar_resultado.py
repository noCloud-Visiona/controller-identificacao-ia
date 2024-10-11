import cv2
import numpy as np

def mascara_binaria(image, nome_imagem_original, H, W):
    print("Nenhuma detecção encontrada, criando uma máscara completamente preta.")
    # Cria uma máscara preta (todos os pixels com valor 0)
    mask = np.zeros((H, W), dtype=np.uint8)  # Corrigido para (altura, largura)

    # Salva a máscara preta
    output_mask_path = f"./../IA/img_mark/{nome_imagem_original}_masked_output_0.png"
    cv2.imwrite(output_mask_path, mask)

    if not isinstance(image, np.ndarray):
        raise ValueError("A imagem fornecida não é um array NumPy válido.")

    # Garante que a imagem seja colorida (3 canais)
    if len(image.shape) == 2:  # Se for uma imagem em tons de cinza
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Cria uma imagem colorida da máscara (todas as cores pretas)
    mask_color = np.zeros((H, W, 3), dtype=np.uint8) 
    merged_image = cv2.addWeighted(image, 0.7, mask_color, 0.3, 0)
    merged_output_path = f"./../IA/img_merged/{nome_imagem_original}_merged_0.png"
    cv2.imwrite(merged_output_path, merged_image)
    
    print(f"Mascara preta salva como {output_mask_path}")
    print(f"Imagem mesclada salva como {merged_output_path}")
    return output_mask_path, merged_image

def processar_resultado(results, image, nome_imagem_original):
    # Garante que a imagem seja colorida (3 canais)
    if len(image.shape) == 2:  # Se for uma imagem em tons de cinza
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    H, W, _ = image.shape

    # Processar os resultados
    for result in results:
        if not result.masks:
            print("O resultado não contém máscaras.")
            output_mask_path, merged_image = mascara_binaria(image, nome_imagem_original, H, W)
            return output_mask_path, merged_image
        else: 
            for j, mask in enumerate(result.masks.data):
                mask = mask.numpy()
                mask = cv2.resize(mask, (W, H))  # Certifica-se de que as dimensões estão corretas

                output_mask_path = f"./../IA/img_mark/{nome_imagem_original}_masked_output_{j}.png"  # Nome do arquivo para a máscara
                cv2.imwrite(output_mask_path, mask * 255)  # Salva a máscara como uma imagem

                mask_img = cv2.imread(output_mask_path, cv2.IMREAD_GRAYSCALE)
                
                # Verifica se a máscara tem apenas 1 canal e expande para 3 canais
                mask_color = cv2.cvtColor(mask_img, cv2.COLOR_GRAY2BGR)
                mask_color[mask_img > 0] = [0, 0, 255]  # Cor vermelha onde a máscara é aplicada

                merged_image = cv2.addWeighted(image, 0.7, mask_color, 0.3, 0) 
                merged_output_path = f"./../IA/img_merged/{nome_imagem_original}_merged_{j}.png"
                cv2.imwrite(merged_output_path, merged_image)

                print(f"Merge completo. Imagem salva como {nome_imagem_original}_merged_{j}.png .")

                return output_mask_path, merged_image
