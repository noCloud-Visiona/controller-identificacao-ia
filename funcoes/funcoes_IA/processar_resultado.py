import cv2
import numpy as np

def mascara_binaria(image, nome_imagem_original, H, W):
    print("Nenhuma detecção encontrada, criando uma máscara completamente preta.")
    # Cria uma máscara preta (todos os pixels com valor 0)
    mask = np.zeros((H, W), dtype=np.uint8)  # Corrigido para (altura, largura)

    # Salva a máscara preta
    output_mask_path = f"./IA/img_mark/{nome_imagem_original}_masked_output_0.png"
    cv2.imwrite(output_mask_path, mask)

    if not isinstance(image, np.ndarray):
        raise ValueError("A imagem fornecida não é um array NumPy válido.")

    # Garante que a imagem seja colorida (3 canais)
    if len(image.shape) == 2:  # Se for uma imagem em tons de cinza
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Cria uma imagem colorida da máscara (todas as cores pretas)
    mask_color = np.zeros((H, W, 3), dtype=np.uint8) 
    merged_image = cv2.addWeighted(image, 0.7, mask_color, 0.3, 0)
    merged_output_path = f"./IA/img_merged/{nome_imagem_original}_merged_0.png"
    cv2.imwrite(merged_output_path, merged_image)
    
    print(f"Mascara preta salva como {output_mask_path}")
    print(f"Imagem mesclada salva como {merged_output_path}")
    return output_mask_path, merged_image

def processar_resultado(results, image, nome_imagem_original):
    # Garante que a imagem seja colorida (3 canais)
    if len(image.shape) == 2:  # Se for uma imagem em tons de cinza
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    H, W, _ = image.shape

    # Inicializa os caminhos de saída para as máscaras separadas
    output_cloud_mask_path = None
    output_shadow_mask_path = None

    # Processar os resultados
    for result in results:
        if not result.masks:
            print("O resultado não contém máscaras.")
            output_mask_path, merged_image = mascara_binaria(image, nome_imagem_original, H, W)
            return output_mask_path, merged_image
        else:
            # Obter as classes associadas às boxes
            classes = result.boxes.cls.cpu().numpy().astype(int)  # Classes das detecções
            masks = result.masks.data.cpu().numpy()  # Máscaras como arrays numpy

            cloud_mask = None
            shadow_mask = None

            for mask, cls in zip(masks, classes):
                mask = cv2.resize(mask, (W, H)) 

                if cls == 0:  
                    if cloud_mask is None:
                        cloud_mask = mask
                    else:
                        cloud_mask = cv2.bitwise_or(cloud_mask, mask)
                elif cls == 1:  
                    if shadow_mask is None:
                        shadow_mask = mask
                    else:
                        shadow_mask = cv2.bitwise_or(shadow_mask, mask)

            if cloud_mask is not None:
                output_cloud_mask_path = f"./IA/img_mark/{nome_imagem_original}_cloud_mask.png"
                cv2.imwrite(output_cloud_mask_path, (cloud_mask * 255).astype('uint8'))

            if shadow_mask is not None:
                output_shadow_mask_path = f"./IA/img_mark/{nome_imagem_original}_shadow_mask.png"
                cv2.imwrite(output_shadow_mask_path, (shadow_mask * 255).astype('uint8'))

            if cloud_mask is not None:
                cloud_color = cv2.cvtColor((cloud_mask * 255).astype('uint8'), cv2.COLOR_GRAY2BGR)
                cloud_color[cloud_mask > 0] = [255, 0, 0]  # Azul para nuvens
                merged_cloud_image = cv2.addWeighted(image, 0.7, cloud_color, 0.3, 0)
                merged_cloud_output_path = f"./IA/img_merged/{nome_imagem_original}_merged_cloud.png"
                cv2.imwrite(merged_cloud_output_path, merged_cloud_image)

            if shadow_mask is not None:
                shadow_color = cv2.cvtColor((shadow_mask * 255).astype('uint8'), cv2.COLOR_GRAY2BGR)
                shadow_color[shadow_mask > 0] = [0, 0, 255]  # Vermelho para sombras
                merged_shadow_image = cv2.addWeighted(image, 0.7, shadow_color, 0.3, 0)
                merged_shadow_output_path = f"./IA/img_merged/{nome_imagem_original}_merged_shadow.png"
                cv2.imwrite(merged_shadow_output_path, merged_shadow_image)

            return output_cloud_mask_path, output_shadow_mask_path
