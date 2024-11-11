import os
import requests
import cv2
import time
from funcoes import IA_a  # Importando o módulo IA para processamento
from PIL import Image
import numpy as np 

def baixar_imagem(img_url, image_dir="IA/img/"):
    image_filename = os.path.basename(img_url)
    if not image_filename.endswith('.tif'):
         image_filename += '.tif'
    image_path = os.path.join(image_dir, image_filename)
    

    headers = {'Range': 'bytes=0-'}
    max_retries = 3
    retry_delay = 10  # segundos

    for attempt in range(max_retries):
         try:
             with open(image_path, 'wb') as f:
                 pos = 0
                 chunk_size = 500 * 1024 * 1024
                 while True:
                     headers['Range'] = f'bytes={pos}-{pos + chunk_size - 1}'
                     response = requests.get(img_url, headers=headers, stream=True, timeout=60)
                     if response.status_code in [206, 200]:
                         f.write(response.content)
                         pos += len(response.content)
                         if len(response.content) < chunk_size:
                             break
                     else:
                         raise ValueError(f"Erro no download da imagem com código de resposta: {response.status_code}")
             return image_path

         except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
             print(f"[ERRO] Timeout na tentativa {attempt + 1}/{max_retries}. Retentando em {retry_delay} segundos...")
             time.sleep(retry_delay)
         except requests.exceptions.RequestException as e:
             print(f"[ERRO] Erro ao tentar baixar a imagem: {e}")
             raise e
    raise ValueError("Erro ao baixar a imagem após várias tentativas")


def validar_formato_imagem(image_path):
    """Valida o formato da imagem e remove se não for suportado."""
    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}
    image_extension = os.path.splitext(image_path)[-1][1:].lower()
    if image_extension not in supported_formats:
        os.remove(image_path)
        raise ValueError("Formato de imagem não suportado")

def processar_imagem_com_ia(image_path):
    """Processa a imagem utilizando o módulo IA e retorna dados da imagem processada."""
    # Processa a imagem usando IA, que gera os caminhos das imagens tratadas
    mask_path, caminho_imagem_tratada, porcentagem_nuvem = IA_a.IA(image_path)
    print(f"[INFO] Imagem retornou com sucesso após processamento com IA: {caminho_imagem_tratada}")
    
    # Configura o limite máximo de pixels no Pillow
    Image.MAX_IMAGE_PIXELS = None  # Define como 'None' para desativar a verificação de limite de pixels
    
    # Abra a imagem tratada usando Pillow
    with Image.open(caminho_imagem_tratada) as pil_img:
        # Converte a imagem Pillow para um array numpy que o OpenCV pode processar
        imagem_tratada = np.array(pil_img)
        print(f"[INFO] Imagem tratada carregada com sucesso: {imagem_tratada.shape}")
    print('Acabou With')
    # Verifique se a imagem foi carregada corretamente
    if imagem_tratada is None or imagem_tratada.size == 0:
        raise ValueError("Falha ao carregar a imagem tratada. Verifique o caminho e formato da imagem.")
    print(f"[INFO] Imagem tratada carregada com sucesso: {imagem_tratada.shape}")
    # Converta para BGR se a imagem estiver em RGB (se necessário para compatibilidade com OpenCV)
    if len(imagem_tratada.shape) == 3 and imagem_tratada.shape[2] == 3:
        imagem_tratada = imagem_tratada[:, :, ::-1]
        print(f"[INFO] Imagem tratada convertida para BGR: {imagem_tratada.shape}")
    print(f"[INFO] Imagem tratada convertida para BGR: {imagem_tratada.shape}")
    return mask_path, caminho_imagem_tratada, porcentagem_nuvem, imagem_tratada

def montar_json_response(data, mask_path, caminho_imagem_tratada, porcentagem_nuvem, imagem_tratada, tratada_url, nuvem_url, data_atual, hora_atual, id_usuario):
    """Monta o JSON final para enviar ao front."""
    print(f"[INFO] Montando JSON final para envio ao frontend...")
    resolucao_da_imagem = f"{imagem_tratada.shape[1]}x{imagem_tratada.shape[0]}"
    print(f"[INFO] Resolução da imagem tratada: {resolucao_da_imagem}")
    area_visivel_mapa = round(100 - porcentagem_nuvem, 2)
    print(f"[INFO] Área visível no mapa: {area_visivel_mapa}%")
    porcentagem_nuvem = round(porcentagem_nuvem, 2)
    print(f"[INFO] Porcentagem de nuvem: {porcentagem_nuvem}%")

    # JSON response estruturado
    return {
        "type": data.get('type', None),
        "id": data.get('id', None),
        "collection": data.get('collection', None),
        "stac_version": data.get('stac_version', None),
        "stac_extensions": data.get('stac_extensions', []),
        "geometry": {
            "type": data['geometry'].get('type', None),
            "coordinates": data['geometry'].get('coordinates', None)
        },
        "links": [
            {
                "href": link.get('href'),
                "rel": link.get('rel')
            } for link in data.get('links', [])
        ],
        "bbox": data.get('bbox', None),
        "assets": {
            "tci": {
                "href": data['assets']['tci'].get('href', None),
                "type": data['assets']['tci'].get('type', None),
                "roles": data['assets']['tci'].get('roles', None),
                "created": data['assets']['tci'].get('created', None),
                "updated": data['assets']['tci'].get('updated', None),
                "bdc:size": data['assets']['tci'].get('bdc:size', None),
                "bdc:chunk_size": data['assets']['tci'].get('bdc:chunk_size', None),
                "bdc:raster_size": data['assets']['tci'].get('bdc:raster_size', None),
                "checksum:multihash": data['assets']['tci'].get('checksum:multihash', None)
            },
            "thumbnail": {
                "href": data['assets']['thumbnail'].get('href', None),
                "type": data['assets']['thumbnail'].get('type', None),
                "roles": data['assets']['thumbnail'].get('roles', None),
                "created": data['assets']['thumbnail'].get('created', None),
                "updated": data['assets']['thumbnail'].get('updated', None),
                "bdc:size": data['assets']['thumbnail'].get('bdc:size', None),
                "checksum:multihash": data['assets']['thumbnail'].get('checksum:multihash', None)
            }
        },
        "properties": {
            "datetime": data['properties'].get('datetime', None),
            "start_datetime": data['properties'].get('start_datetime', None),
            "end_datetime": data['properties'].get('end_datetime', None),
            "created": data['properties'].get('created', None),
            "updated": data['properties'].get('updated', None),
            "eo:cloud_cover": data['properties'].get('eo:cloud_cover', None)
        },
        "user_geometry": {
            "type": data['user_geometry'].get('type', None),
            "coordinates": data['user_geometry'].get('coordinates', None)
        },
        "identificacao_ia":{
            "id": data['id'],
            "area_visivel_mapa": area_visivel_mapa,
            "percentual_nuvem": porcentagem_nuvem,
            "percentual_sombra_nuvem": None,
            "id_usuario": id_usuario,
            "data": data_atual,
            "hora": hora_atual,
            "img_original_png": data['id'],
            "img_original_tiff": data['id'],
            "img_tratada": tratada_url,
            "mask_nuvem": nuvem_url,
            "mask_sombra": None,
            "tiff_tratado": caminho_imagem_tratada,
            "resolucao_imagem_png": resolucao_da_imagem,
            "resolucao_imagem_tiff": None,
            "bbox": data['bbox']
        }
    }

def enviar_json_final(json_response):
    print(f"[INFO] Enviando JSON final para a rota especificada...")
    """Envia o JSON final para a rota especificada."""
    response = requests.post('http://host.docker.internal:3004/post_json', json=json_response)
    print(f"[INFO] Resposta da requisição: {response.text}")
    return response