import os
import requests
import cv2
from funcoes import IA_a  # Importando o módulo IA para processamento

def baixar_imagem(img_url, image_dir="IA/img/"):
    """Baixa a imagem da URL fornecida e salva no diretório especificado."""
    image_filename = os.path.basename(img_url)
    if not image_filename.endswith('.tif'):
        image_filename += '.tif'
    image_path = os.path.join(image_dir, image_filename)

    os.makedirs(image_dir, exist_ok=True)

    response = requests.get(img_url)
    if response.status_code == 200:
        with open(image_path, 'wb') as f:
            f.write(response.content)
        return image_path
    else:
        raise ValueError("Erro ao baixar a imagem")

def validar_formato_imagem(image_path):
    """Valida o formato da imagem e remove se não for suportado."""
    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}
    image_extension = os.path.splitext(image_path)[-1][1:].lower()
    if image_extension not in supported_formats:
        os.remove(image_path)
        raise ValueError("Formato de imagem não suportado")

def processar_imagem_com_ia(image_path):
    """Processa a imagem utilizando o módulo IA e retorna dados da imagem processada."""
    mask_path, caminho_imagem_tratada, porcentagem_nuvem = IA_a.IA(image_path)
    imagem_tratada = cv2.imread(caminho_imagem_tratada, cv2.IMREAD_UNCHANGED)
    return mask_path, caminho_imagem_tratada, porcentagem_nuvem, imagem_tratada

def montar_json_response(data, mask_path, caminho_imagem_tratada, porcentagem_nuvem, imagem_tratada, tratada_url, nuvem_url, data_atual, hora_atual):
    """Monta o JSON final para enviar ao front."""
    resolucao_da_imagem = f"{imagem_tratada.shape[1]}x{imagem_tratada.shape[0]}"
    area_visivel_mapa = round(100 - porcentagem_nuvem, 2)
    porcentagem_nuvem = round(porcentagem_nuvem, 2)

    # JSON response estruturado
    return {
        # Estrutura completa de `json_incompleto_para_a_rota_terminar`
    }

def enviar_json_final(json_response):
    """Envia o JSON final para a rota especificada."""
    response = requests.post('http://host.docker.internal:3004/post_json', json=json_response)
    return response