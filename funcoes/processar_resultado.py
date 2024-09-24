import cv2

def processar_resultados(results, imagem_tratada):
    # Processar os resultados
    for result in results:
        for j, mask in enumerate(result.masks.data):
            mask = mask.numpy()
            mask = cv2.resize(mask, (640, 640))  # Redimensionar a máscara para o tamanho original

            # Salvar a máscara como uma imagem em escala de cinza
            output_mask_path = f"mask_{j}.png"  # Nome do arquivo para a máscara
            cv2.imwrite(output_mask_path, mask * 255)  # Multiplica por 255 para converter para escala de cinza

            # Carregar a máscara salva
            mask_img = cv2.imread(output_mask_path, cv2.IMREAD_GRAYSCALE)

            # Criar uma imagem colorida para a máscara (vermelha com transparência)
            mask_color = np.zeros((*mask_img.shape, 3), dtype=np.uint8)  # Imagem colorida em 3 canais
            mask_color[mask_img > 0] = [0, 0, 255]  # Cor vermelha onde a máscara é aplicada

            # Sobrepor a máscara colorida na imagem original
            merged_image = cv2.addWeighted(imagem_tratada, 0.7, mask_color, 0.3, 0)  # Ajuste os pesos conforme necessário

            # Salvar a imagem final mesclada
            merged_output_path = "merged_output_with_color.png"
            cv2.imwrite(merged_output_path, merged_image)
            print("Merge completo. Imagem salva como 'merged_output_with_color.png'.")