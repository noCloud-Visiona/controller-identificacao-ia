from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import funcoes.IA_a as IA_a
import os
import datetime
import json
import base64
from funcoes.serializador_de_imagem import transforma_imagem_em_json
from firebase import db, bucket
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

    # Acessa a coleção no Firestore "historico_imagens_ia"
    collection_ref = db.collection("historico_imagens_ia")

    # Conta quantos documentos já existem para o usuário, para criar um id único
    docs = collection_ref.where("id_usuario", "==", id_usuario).stream()
    doc_count = sum(1 for _ in docs)

    id_imagem = f"{nome_base}_{doc_count + 1}"

    # Salva a imagem original e a tratada no Firebase Storage
    blob = bucket.blob(f"imagens/original_final/{id_imagem}")
    blob.upload_from_filename(image_path)
    blob.make_public()
    imagem_original_url = blob.public_url

    blob = bucket.blob(f"imagens/tratada_final/{id_imagem}")
    blob.upload_from_filename(imagem_IA_path)
    blob.make_public()
    imagem_tratada_pela_IA_url = blob.public_url

    # Salva no Firestore o JSON que o frontend precisa consumir
    collection_ref.add({
        "id_usuario": id_usuario,
        "id_imagem": id_imagem,
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

    resposta = {
        "id_usuario": id_usuario,
        "id_imagem": id_imagem,
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
    historico = [doc.to_dict() for doc in documentos]

    return jsonify(historico)

@app.route('/delete_image/<id_imagem>/<id_usuario>', methods=['DELETE'])
def delete_image(id_imagem, id_usuario):
    collection_ref = db.collection("historico_imagens_ia")

    # Recupera o documento que tem o campo "id_imagem" e "id_usuario" igual ao fornecido
    documentos = collection_ref.where("id_imagem", "==", id_imagem).where("id_usuario", "==", id_usuario).stream()

    doc_to_delete = None
    for doc in documentos:
        doc_to_delete = doc
        break

    if not doc_to_delete:
        return jsonify({"message": "Imagem não encontrada ou não pertence ao usuário"}), 404

    # Pegando os dados do documento
    doc_data = doc_to_delete.to_dict()
    original_url = doc_data.get("thumbnail")
    treated_url = doc_data.get("img_tratada")

    try:
        # Extrair o caminho do bucket a partir das URLs
        if original_url:
            original_blob_name = "/".join(original_url.split("/")[-3:])  # Obtém o caminho relativo do blob
            bucket.delete_blob(original_blob_name)

        if treated_url:
            treated_blob_name = "/".join(treated_url.split("/")[-3:])  # Obtém o caminho relativo do blob
            bucket.delete_blob(treated_blob_name)

        # Deletando o documento do Firestore
        doc_to_delete.reference.delete()

        return jsonify({"message": "Imagem deletada com sucesso"}), 200

    except Exception as e:
        return jsonify({"message": f"Erro ao deletar imagem: {str(e)}"}), 500


@app.route('/get_image/<id_imagem>/<id_usuario>', methods=['GET'])
def get_image(id_imagem, id_usuario):
    collection_ref = db.collection("historico_imagens_ia")

    # Recupera o documento que tem o campo "id_imagem" igual ao valor passado e "id_usuario" igual ao fornecido
    documentos = collection_ref.where("id_imagem", "==", id_imagem).where("id_usuario", "==", id_usuario).stream()

    doc_to_get = None
    for doc in documentos:
        doc_to_get = doc
        break

    if not doc_to_get:
        return jsonify({"message": "Imagem não encontrada ou não pertence ao usuário"}), 404

    # Pegando os dados do documento
    doc_data = doc_to_get.to_dict()

    resposta = {
        "id_usuario": doc_data.get("id_usuario"),
        "id_imagem": doc_data.get("id_imagem"),
        "data": doc_data.get("data"),
        "hora": doc_data.get("hora"),
        "geometry": doc_data.get("geometry"),
        "resolucao_imagem": doc_data.get("resolucao_imagem"),
        "satelite": doc_data.get("satelite"),
        "sensor": doc_data.get("sensor"),
        "percentual_nuvem": doc_data.get("percentual_nuvem"),
        "area_visivel_mapa": doc_data.get("area_visivel_mapa"),
        "thumbnail": doc_data.get("thumbnail"),
        "img_tratada": doc_data.get("img_tratada")
    }

    return jsonify(resposta), 200

@app.route('/show_image', methods=['POST'])
def show_image():
    json_data = request.get_json()

    # Chama a função para transformar a imagem codificada em um arquivo PNG
    success, mensagem = transforma_json_em_imagem(json_data, "IA/img/output_image.png")

    if success:
        try:
            return send_file("IA/img/output_image.png", mimetype='image/png'), 200
        except FileNotFoundError:
            return jsonify({"message": "Erro: Imagem não encontrada"}), 404
    else:
        return jsonify({"message": mensagem}), 400

def transforma_json_em_imagem(image_json, output_path):
    try:
        image_data = image_json.get("img_tratada", "")
        
        if not image_data:
            raise ValueError("Imagem não encontrada na chave 'img_tratada' do JSON")

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
