import cv2
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import funcoes.IA_a as IA_a
import os
import requests
import datetime
from dotenv import load_dotenv

# Carregando as variáveis de ambiente do arquivo .env.dev
load_dotenv('.env.dev')

app = Flask(__name__)
CORS(app)  # Habilitando o CORS para todas as rotas

@app.route('/predict/', methods=['POST'])
def predict():
    # ------------------------- Parte envolvendo receber o JSON do controller-INPE com a URL da imagem -------------------------
    data = request.get_json()

    # Verifica se o JSON foi enviado e se contém o campo img_original_png
    if not data or 'identificacao_ia' not in data or 'img_original_png' not in data['identificacao_ia']:
        return jsonify({'error': 'JSON inválido ou campo img_original_png ausente'}), 400

    # Obtém o campo img_original_png do JSON
    img_url = data['identificacao_ia']['img_original_png']
    print(img_url)

    image_filename = os.path.basename(img_url)
    if not image_filename.endswith('.png'):  # Verifica se já tem a extensão .png
        image_filename += '.png'
    
    # Faz o download da imagem usando a URL fornecida
    try:
        response = requests.get(img_url)
        if response.status_code != 200:
            return jsonify({'error': 'Não foi possível baixar a imagem da URL fornecida'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Define o diretório onde a imagem será salva
    image_dir = "IA/img/"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    # Define o caminho completo da imagem com o nome do arquivo extraído da URL
    image_path = os.path.join(image_dir, image_filename)

    # Salva a imagem baixada no caminho especificado
    with open(image_path, 'wb') as f:
        f.write(response.content)

    # ------------------------- Valida o formato da imagem -------------------------
    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}

    # Verifica a extensão da imagem e converte para minúsculo para evitar problemas de case-sensitive
    image_extension = image_filename.split('.')[-1].lower()

    if image_extension not in supported_formats:
        os.remove(image_path)  # Remove a imagem caso o formato não seja suportado
        return jsonify({'error': 'Formato de imagem não suportado'}), 400
    
    # ------------------------------ Parte envolvendo tratar a imagem recebida com a IA ---------------------------------
    mask_path, imagem_tratada_pela_IA, porcentagem_nuvem = IA_a.IA(image_path)
    imagem_tratada_pela_IA = cv2.imwrite(imagem_tratada_pela_IA, cv2.IMREAD_UNCHANGED)
    nome_base = os.path.splitext(imagem_tratada_pela_IA.filename)[0]

    # ------------ Parte envolvendo a montagem do JSON para salvar no firebase e devolver a resposta --------------------
    data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
    hora_atual = datetime.datetime.now().strftime("%H:%M:%S")

    # Obtendo a resolução da imagem tratada
    resolucao_da_imagem = f"{imagem_tratada_pela_IA.shape[1]}x{imagem_tratada_pela_IA.shape[0]}"  # largura x altura

    # Calcula a porcentagem de nuvem e área visível
    area_visivel_mapa = 100 - porcentagem_nuvem
    porcentagem_nuvem = round(porcentagem_nuvem, 2)
    area_visivel_mapa = round(area_visivel_mapa, 2)

    imagem_IA_path = 'IA/img_mark_e_merged/merged_output_with_color.png'
    imagem_mask_cloud_path = 'IA/img_mark_e_merged/mask_0.png'

    #rota pra salvar as 2 imagens no Bucket e receber as 2 url de volta
    with open(imagem_IA_path, 'rb') as tratada_image, open(imagem_mask_cloud_path, 'rb') as nuvem_image:
        files = {
            'tratada': tratada_image,
            'nuvem': nuvem_image
        }

        # Enviando as imagens para as respectivas rotas
        response_tratada = requests.post('http://host.docker.internal:3005/upload_image_tratada_png', files={'tratada': files['tratada']})
        response_mask = requests.post('http://1host.docker.internal:3005/upload_image_nuvem_png', files={'nuvem': files['nuvem']})
        data_tratada = response_tratada.json()
        data_mask = response_mask.json()
        
    # Obtendo as URLs das imagens
    tratada_url = data_tratada.get('tratada_url')
    nuvem_url = data_mask.get('nuvem_url')

    id_usuario = data['identificacao_ia'].get('id_usuario', None)

    # Verifica se id_usuario não é None e se não é uma string
    if id_usuario is not None and not isinstance(id_usuario, str):
        id_usuario = str(id_usuario)
    else:
        return "id_usuario inválido"

    # Salva no Firestore o JSON que o frontend precisa consumir
    json_incompleto_para_a_rota_terminar = {
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
            "id": data['identificacao_ia'].get('id', None),
            "area_visivel_mapa": area_visivel_mapa,
            "percentual_nuvem": porcentagem_nuvem,
            "percentual_sombra_nuvem": None,
            "id_usuario": id_usuario,
            "data": data_atual,
            "hora": hora_atual,
            "img_original_png": data['identificacao_ia'].get('img_original_png', None),
            "img_original_tiff": data['identificacao_ia'].get('img_original_tiff', None),
            "img_tratada": tratada_url,
            "mask_nuvem": nuvem_url,
            "mask_sombra": None,
            "tiff_tratado": None,
            "resolucao_imagem_png": resolucao_da_imagem,
            "resolucao_imagem_tiff": None,
            "bbox": data['identificacao_ia'].get('bbox', None)
        }
    }

    # Rota de Teste local
    response_json = {}

    # Faz a requisição
    response = requests.post('http://host.docker.internal:3005/post_json', json=json_incompleto_para_a_rota_terminar)

    # Verificação da resposta
    if response.status_code == 201:
        response_json = response.json()
    else:
        print("Erro ao enviar o JSON:", response.status_code, response.text)

    # Retorna o JSON de resposta ou um erro, conforme a situação
    return jsonify(response_json), response.status_code

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=3002)
