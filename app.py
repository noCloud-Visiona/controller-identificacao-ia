from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import funcoes.IA_a as IA_a
import os
import datetime
import json
import base64
from funcoes.serializador_de_imagem import transforma_imagem_em_json
from firebase import db, bucket
from datetime import timedelta

app = Flask(__name__)
CORS(app)  # Habilitando o CORS para todas as rotas

@app.route('/predict/<id_usuario>', methods=['POST'])
def predict(id_usuario):

    # ------------------------- Parte envolvendo receber a imagem e id do usuario da requisição -------------------------

    #espera uma imagem a ser tratada pela IA e um id de usuario na rota
    if not request.files:
        return jsonify({'error': 'Nenhuma imagem provida'}), 400

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

    # -------------------------------------------------------------------------------------------------------------------

    # ------------------------------ Parte envolvendo tratar a imagem recebida com a IA ---------------------------------

    # Aqui estamos garantindo que a função IA retorna três valores
    mask_path, imagem_tratada_pela_IA, porcentagem_nuvem = IA_a.IA(image_path)
    nome_base = os.path.splitext(imagem.filename)[0]

    # -------------------------------------------------------------------------------------------------------------------

    # ------------ Parte envolvendo a montagem do JSON para salvar no firebase e devolver a resposta --------------------

    #cria as informações data e horario
    data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
    hora_atual = datetime.datetime.now().strftime("%H:%M:%S")

    # Como `imagem_tratada` é um `numpy.ndarray`, você pode obter a resolução diretamente
    resolucao_da_imagem = f"{imagem_tratada_pela_IA.shape[1]}x{imagem_tratada_pela_IA.shape[0]}"  # largura x altura

    #faz os calculos para ter a porcentagem de nuvem e area visivel
    area_visivel_mapa = 100 - porcentagem_nuvem
    porcentagem_nuvem = round(porcentagem_nuvem, 2)
    area_visivel_mapa = round(area_visivel_mapa, 2)

    imagem_IA_path = 'IA/img_mark_e_merged/merged_output_with_color.png'

    #acessa a coleção no firebase "historico_imagens_ia"
    collection_ref = db.collection("historico_imagens_ia")

    #abre e faz um count de quantos documentos tem para adicionar no doc_count apenas do id usuario
    docs = collection_ref.where("id_usuario", "==", id_usuario).stream()
    doc_count = sum(1 for _ in docs)

    #cria o campo id unico para o frontend consumir e trazer todas as requisições de um usuario especifico
    id_unico = f"{nome_base}_{doc_count + 1}"

    #salva a imagem original e a imagem tratada pela IA no bucket do firebase, referenciando caminhos no bucket
    blob = bucket.blob(f"imagens/original/{nome_base}_{doc_count}")
    blob.upload_from_filename(image_path)
    blob.make_public()
    imagem_original_url = blob.public_url

    blob = bucket.blob(f"imagens/tratada/{nome_base}_{doc_count}")
    blob.upload_from_filename(imagem_IA_path)
    blob.make_public()
    imagem_tratada_pela_IA_url = blob.public_url

    #salva no firestorm o json que o frontend precisa consumir
    collection_ref = db.collection("historico_imagens_ia")
    collection_ref.add({
        "id_usuario": id_usuario,
        "id": id_unico,
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
        "thumbnail": imagem_original_url,
        "img_tratada": imagem_tratada_pela_IA_url
    })

    # Apaga a imagem da pasta local após termino da utilidade dela, para que não encha a pasta IA/img
    for file in os.listdir(image_dir):
        if file.split('.')[-1].lower() in supported_formats:
            file_path = os.path.join(image_dir, file)
            os.remove(file_path)

    resposta = {
        "id_usuario": id_usuario,
        "id": id_unico,
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
        "thumbnail": imagem_original_url,
        "img_tratada": imagem_tratada_pela_IA_url
    }

    return jsonify(resposta)

@app.route('/historico/<id_usuario>', methods=['GET'])
def get_historico(id_usuario):
    collection_ref = db.collection("historico_imagens_ia")
    
    # Recuperando os documentos que têm o campo "id_usuario" igual ao valor passado
    documentos = collection_ref.where("id_usuario", "==", id_usuario).stream()
    
    # Criando uma lista para armazenar os dados
    historico = []
    
    for doc in documentos:
        # Adicionando os dados de cada documento à lista
        historico.append(doc.to_dict())
    
    # Retornando os dados em formato JSON
    return jsonify(historico)

# Rota do Briscese 
@app.route('/show_image', methods=['POST'])
def show_image():
    # Recebe o JSON com a imagem codificada
    json_data = request.get_json()

    # Chama a função para transformar a imagem codificada em um arquivo PNG
    success, mensagem = transforma_json_em_imagem(json_data, "IA/img/output_image.png")

    if success:
        # Retorna a imagem decodificada
        try:
            return send_file("IA/img/output_image.png", mimetype='image/png'), 200
        except FileNotFoundError:
            return jsonify({"message": "Erro: Imagem não encontrada"}), 404
    else:
        # Em caso de erro, retorna a mensagem de erro
        return jsonify({"message": mensagem}), 400

def transforma_json_em_imagem(image_json, output_path):
    try:
        # Aqui, pegamos a imagem da chave "img_tratada"
        image_data = image_json.get("img_tratada", "")
        
        if not image_data:
            raise ValueError("Imagem não encontrada na chave 'img_tratada' do JSON")

        # Decodificando a imagem Base64
        missing_padding = len(image_data) % 4
        if missing_padding:
            image_data += '=' * (4 - missing_padding)

        with open(output_path, "wb") as output_file:
            output_file.write(base64.b64decode(image_data))

        return True, "Imagem decodificada com sucesso"
    except json.JSONDecodeError as json_err:
        return False, f"Erro ao decodificar JSON: {str(json_err)}"
    except ValueError as val_err:
        return False, str(val_err)
    except Exception as e:
        return False, f"Erro ao decodificar a imagem: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=3002)
