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

    response = requests.get(img_url, timeout=1000)
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

def montar_json_response(data, mask_path, caminho_imagem_tratada, porcentagem_nuvem, imagem_tratada, tratada_url, nuvem_url, data_atual, hora_atual, id_usuario):
    """Monta o JSON final para enviar ao front."""
    resolucao_da_imagem = f"{imagem_tratada.shape[1]}x{imagem_tratada.shape[0]}"
    area_visivel_mapa = round(100 - porcentagem_nuvem, 2)
    porcentagem_nuvem = round(porcentagem_nuvem, 2)

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
            "EVI": {
                "href": data['assets']['EVI'].get('href', None),
                "type": data['assets']['EVI'].get('type', None),
                "roles": data['assets']['EVI'].get('roles', None),
                "created": data['assets']['EVI'].get('created', None),
                "updated": data['assets']['EVI'].get('updated', None),
                "bdc:size": data['assets']['EVI'].get('bdc:size', None),
                "bdc:chunk_size": data['assets']['EVI'].get('bdc:chunk_size', None),
                "bdc:raster_size": data['assets']['EVI'].get('bdc:raster_size', None),
                "checksum:multihash": data['assets']['EVI'].get('checksum:multihash', None)
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
            "tiff_tratado": None,
            "resolucao_imagem_png": resolucao_da_imagem,
            "resolucao_imagem_tiff": None,
            "bbox": data['bbox']
        }
    }

def enviar_json_final(json_response):
    """Envia o JSON final para a rota especificada."""
    response = requests.post('http://host.docker.internal:3004/post_json', json=json_response)
    return response