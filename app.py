import os
import datetime
import requests
from threading import Thread
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import uuid
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import base64
import json

# Importar funções de módulos
from processar_imagem import processar_imagem

# Carregando as variáveis de ambiente do arquivo .env.dev
load_dotenv('.env.dev')

app = Flask(__name__)
CORS(app)  # Habilitando o CORS para todas as rotas

# Configuração do Flask-Limiter
limiter = Limiter(
    key_func=get_remote_address,  # Limita por endereço IP
    app=app,
    default_limits=["20 per minute"]  # Limite padrão de 10 requisições por minuto
)

processing_jobs = {}

@app.route('/predict/<id_usuario>', methods=['POST', 'OPTIONS'])
@limiter.limit("20 per minute")  # Limite específico para esse endpoint
def novopredict(id_usuario):
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    print(f"[INFO] JSON recebido na rota /predict/{id_usuario}: {data}")
    
    if not data:
        return jsonify({"error": "Nenhum dado fornecido"}), 400
    
    band16_url = data.get('assets', {}).get('tci', {}).get('href')
    if not band16_url:
        return jsonify({"error": "tci não encontrada!"}), 404

    # Gerar um ID único para o trabalho
    job_id = str(uuid.uuid4())
    processing_jobs[job_id] = {"status": "Análise em andamento, por favor aguarde uns instantes!", "result": None}

    # Inicializa o trabalho
    response = requests.post('http://host.docker.internal:3004/post_job_id/id_usuario/job_id', id_usuario=id_usuario, job_id=job_id)

    # Verificação da resposta
    if response.status_code == 201:
        response_json = response.json()
    else:
        print("Erro ao salvar o job_id:", response.status_code, response.text)

    image_filename = os.path.basename(band16_url) + '.tif'
    image_dir = "IA/img/"
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, image_filename)

    # Inicia o processamento em segundo plano
    thread = Thread(target=processar_imagem, args=(band16_url,image_dir,data, job_id, processing_jobs, id_usuario))  # Remove callback_url
    thread.start()

    return jsonify({"message": "A análise está em andamento!", "job_id": job_id}), 202

@app.route('/status/<id_usuario>/<job_id>', methods=['GET'])
def status(id_usuario, job_id):
    job = requests.get('http://host.docker.internal:3004/get_job_id/id_usuario/job_id', id_usuario=id_usuario, job_id=job_id)
    job_processing = processing_jobs.get(job.get('job_id'))
    if job_processing:
        return jsonify(job_processing), 200
    else:
        return jsonify({"error": "Job ID não encontrado"}), 404
    
@app.route('/imagem-predict/<id_usuario>', methods=['POST', 'OPTIONS'])
def imagem_predict(id_usuario):
    if not request.files:
        return jsonify({'error': 'Nenhuma imagem provida'}), 400
    
    data = request.get_json()
    
    imagem = next(iter(request.files.values()))

    image_dir = "IA/img/"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    #salva o path de onde ficou a imagem
    image_path = os.path.join(image_dir, imagem.filename)
    imagem.save(image_path)

    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}

    if image_path.split('.')[-1].lower() not in supported_formats:
        os.remove(image_path)
        return jsonify({'error': 'Formato de imagem não suportado'}), 400
    
    # ------------------------------ Parte envolvendo tratar a imagem recebida com a IA ---------------------------------
    mask_path, caminho_imagem_tratada, porcentagem_nuvem = IA_a.IA(image_path)
    imagem_tratada_pela_IA = cv2.imread(caminho_imagem_tratada, cv2.IMREAD_UNCHANGED)
    print(imagem_tratada_pela_IA)

    # ------------ Parte envolvendo a montagem do JSON para salvar no firebase e devolver a resposta --------------------
    data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
    hora_atual = datetime.datetime.now().strftime("%H:%M:%S")

    # Obtendo a resolução da imagem tratada
    resolucao_da_imagem = f"{imagem_tratada_pela_IA.shape[1]}x{imagem_tratada_pela_IA.shape[0]}"  # largura x altura

    # Calcula a porcentagem de nuvem e área visível
    area_visivel_mapa = 100 - porcentagem_nuvem
    porcentagem_nuvem = round(porcentagem_nuvem, 2)
    area_visivel_mapa = round(area_visivel_mapa, 2)

    #rota pra salvar as 2 imagens no Bucket e receber as 2 url de volta
    with open(caminho_imagem_tratada, 'rb') as tratada_image, open(mask_path, 'rb') as nuvem_image:
        files = {
            'tratada': tratada_image,
            'nuvem': nuvem_image
        }

        # Enviando as imagens para as respectivas rotas
        response_tratada = requests.post('http://host.docker.internal:3004/upload_image_tratada_png', files={'tratada': files['tratada']})
        response_mask = requests.post('http://host.docker.internal:3004/upload_image_nuvem_png', files={'nuvem': files['nuvem']})
        data_tratada = response_tratada.json()
        data_mask = response_mask.json()
        
    # Obtendo as URLs das imagens
    tratada_url = data_tratada.get('tratada_url')
    nuvem_url = data_mask.get('nuvem_url')

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

    # Rota de Teste local
    response_json = {}

    # Faz a requisição
    response = requests.post('http://host.docker.internal:3004/post_json', json=json_incompleto_para_a_rota_terminar)

    # Verificação da resposta
    if response.status_code == 201:
        response_json = response.json()
    else:
        print("Erro ao enviar o JSON:", response.status_code, response.text)

    print(f"Imagem encontrada: {image_path}")

    job_id = str(uuid.uuid4())
    processing_jobs[job_id] = {"status": "Análise em andamento, por favor aguarde uns instantes!", "result": None}  # Inicializa o trabalho
    thread = Thread(target=processar_imagem, args=(image_path, data, job_id, processing_jobs, id_usuario))  # Remove callback_url
    thread.start()

    return jsonify({"message": "A análise está em andamento!", "job_id": job_id}), 202

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=3002)