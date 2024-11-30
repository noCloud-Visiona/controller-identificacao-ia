import cv2
import numpy as np

def processar_resultado(results, image, nome_imagem_original, nuvem_tela_inteira):
    if len(image.shape) == 2:  # Se for uma imagem em tons de cinza
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    H, W, _ = image.shape

    if nuvem_tela_inteira:
        custom_mask_path = './IA/white_mask_1024x1024.png'
        custom_mask = cv2.imread(custom_mask_path, cv2.IMREAD_GRAYSCALE)
        
        if custom_mask is not None:
            custom_mask_resized = cv2.resize(custom_mask, (W, H))

            output_mask_path = f"./IA/img_mark/{nome_imagem_original}_cloud_mask.png"
            
            cv2.imwrite(output_mask_path, custom_mask_resized)  # Salva a máscara redimensionada

            custom_mask_color = cv2.cvtColor(custom_mask_resized, cv2.COLOR_GRAY2BGR)
            custom_mask_color[custom_mask_resized > 0] = [0, 0, 255]

            merged_image = cv2.addWeighted(image, 0.7, custom_mask_color, 0.3, 0)
            merged_output_path = f"./IA/img_merged/{nome_imagem_original}_merged_custom.png"
            cv2.imwrite(merged_output_path, merged_image)
            
            print(f"Merge custom completo. Imagem salva como {nome_imagem_original}_merged_custom.png .")
        else:
            raise ValueError("Máscara personalizada não fornecida ou inválida.")

    for result in results:
        if not result.masks:
            print("O resultado não contém máscaras.")
        else:
            for j, mask in enumerate(result.masks.data):
                mask = mask.numpy()
                mask = cv2.resize(mask, (W, H))
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

