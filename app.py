import os
import datetime
import requests
from threading import Thread
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import uuid

# Importar funções de módulos
from services import baixar_imagem, validar_formato_imagem
from processar_imagem import processar_imagem

# Carregando as variáveis de ambiente do arquivo .env.dev
load_dotenv('.env.dev')

app = Flask(__name__)
CORS(app)  # Habilitando o CORS para todas as rotas

processing_jobs = {}

@app.route('/novopredict', methods=['POST', 'OPTIONS'])
def novopredict():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Nenhum dado fornecido"}), 400
    
    band16_url = data.get('assets', {}).get('BAND16', {}).get('href')
    if not band16_url:
        return jsonify({"error": "BAND16 not found"}), 404

    # Gerar um ID único para o trabalho
    job_id = str(uuid.uuid4())
    processing_jobs[job_id] = {"status": "em andamento", "result": None}  # Inicializa o trabalho

    image_filename = os.path.basename(band16_url) + '.tif'
    image_dir = "IA/img/"
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, image_filename)

    try:
        # Baixar a imagem
        image_path = baixar_imagem(band16_url, image_dir=image_dir)
        validar_formato_imagem(image_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Inicia o processamento em segundo plano
    thread = Thread(target=processar_imagem, args=(image_path, data, job_id))  # Remove callback_url
    thread.start()

    return jsonify({"message": "A análise está em andamento!", "job_id": job_id}), 202

@app.route('/status/<job_id>', methods=['GET'])
def status(job_id):
    job = processing_jobs.get(job_id)
    if job:
        return jsonify(job), 200
    else:
        return jsonify({"error": "Job not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=3002)