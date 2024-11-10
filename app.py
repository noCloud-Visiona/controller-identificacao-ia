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
    
    if not data:
        return jsonify({"error": "Nenhum dado fornecido"}), 400
    
    band16_url = data.get('assets', {}).get('tci', {}).get('href')
    if not band16_url:
        return jsonify({"error": "tci não encontrada!"}), 404

    # Gerar um ID único para o trabalho
    job_id = str(uuid.uuid4())
    processing_jobs[job_id] = {"status": "Análise em andamento, por favor aguarde uns instantes!", "result": None}  # Inicializa o trabalho

    image_filename = os.path.basename(band16_url) + '.tif'
    image_dir = "IA/img/"
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, image_filename)

    # Inicia o processamento em segundo plano
    thread = Thread(target=processar_imagem, args=(band16_url,image_dir,data, job_id, processing_jobs, id_usuario))  # Remove callback_url
    thread.start()

    return jsonify({"message": "A análise está em andamento!", "job_id": job_id}), 202

@app.route('/status/<job_id>', methods=['GET'])
def status(job_id):
    job = processing_jobs.get(job_id)
    if job:
        return jsonify(job), 200
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

    print(f"Imagem encontrada: {image_path}")

    job_id = str(uuid.uuid4())
    processing_jobs[job_id] = {"status": "Análise em andamento, por favor aguarde uns instantes!", "result": None}  # Inicializa o trabalho
    thread = Thread(target=processar_imagem, args=(image_path, data, job_id, processing_jobs, id_usuario))  # Remove callback_url
    thread.start()

    return jsonify({"message": "A análise está em andamento!", "job_id": job_id}), 202

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=3002)