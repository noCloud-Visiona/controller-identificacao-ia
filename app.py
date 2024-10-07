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

@app.route('/predict/<id_usuario>', methods=['POST'])
def predict(id_usuario):
    # ------------------------- Parte envolvendo receber a imagem e id do usuario da requisição -------------------------
    if not request.files:
        return jsonify({'error': 'Nenhuma imagem provida'}), 400

    imagem = next(iter(request.files.values()))

    image_dir = "IA/img/"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    # Salva o caminho onde ficou a imagem
    image_path = os.path.join(image_dir, imagem.filename)
    imagem.save(image_path)

    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}

    if image_path.split('.')[-1].lower() not in supported_formats:
        os.remove(image_path)
        return jsonify({'error': 'Formato de imagem não suportado'}), 400

    print(f"Imagem encontrada: {image_path}")

    # ------------------------------ Parte envolvendo tratar a imagem recebida com a IA ---------------------------------
    mask_path, imagem_tratada_pela_IA, porcentagem_nuvem = IA_a.IA(image_path)
    nome_base = os.path.splitext(imagem.filename)[0]

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

    #rota pra salvar as 2 imagens no Bucket e receber as 2 url de volta
    with open(image_path, 'rb') as original_image, open(imagem_IA_path, 'rb') as tratada_image:
        files = {
            'original': original_image,
            'tratada': tratada_image
        }
        # Rota de Teste local
        response = requests.post('http://localhost:5000/upload_images', files=files)
        data = response.json()
        
    # Obtendo as URLs das imagens
    original_url = data['original_url']
    tratada_url = data['tratada_url']

    # Salva no Firestore o JSON que o frontend precisa consumir
    json_incompleto_para_a_rota_terminar = {
        "id_usuario": id_usuario,
        "id_imagem": nome_base,
        "data": data_atual,
        "hora": hora_atual,
        "geometry": {
            "type": "Polygon",
            "coordinates": None
        },
        "resolucao_imagem": resolucao_da_imagem,
        "satelite": "CBERS4A",
        "sensor": "WPM",
        "percentual_nuvem": porcentagem_nuvem,
        "area_visivel_mapa": area_visivel_mapa,
        "imagem": None,
        "thumbnail": original_url,
        "img_tratada": tratada_url,
    }

    # Rota de Teste local
    response = requests.post('http://localhost:5000/post_json', json=json_incompleto_para_a_rota_terminar)

    # Verificação da resposta
    if response.status_code == 201:
        response_json = response.json()
        print("JSON recebido da resposta")
    else:
        print("Erro ao enviar o JSON:", response.status_code, response.text)

    return jsonify(response_json)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=3002)
