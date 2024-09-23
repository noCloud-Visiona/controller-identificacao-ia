from flask import Flask, request, send_file, jsonify
from funcoes.identificador_de_nuvem import identificador_nuvem
import os

app = Flask(__name__)

#OBS: para testar o codigo, pode se usar o aplicativo Insominia criando uma nova requisição POST, selecionando "multipart" e escolhendo no value o tipo file, assim enviando uma imagem na requisição.

@app.route('/predict', methods=['POST'])
def predict():
    if not request.files:
        return jsonify({'error': 'Nenhuma imagem provida'}), 400

    imagem = next(iter(request.files.values()))
    
    image_dir = "IA/img/"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    # Salva a imagem com o nome original
    image_path = os.path.join(image_dir, imagem.filename)
    imagem.save(image_path)

    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}

    # Verifica se há uma imagem com uma das extensões suportadas
    if image_path.split('.')[-1].lower() not in supported_formats:
        os.remove(image_path)
        return jsonify({'error': 'Formato de imagem não suportado'}), 400

    print(f"Imagem encontrada: {image_path}")

    resultado_da_imagem = identificador_nuvem(image_path)

    #codigo pra remover qualquer imagem suportada da pasta apos tratar a imagem
    for file in os.listdir(image_dir):
        if file.split('.')[-1].lower() in supported_formats:
            file_path = os.path.join(image_dir, file)
            os.remove(file_path)

    # devolve a imagem serializada como Json
    #return resultado_da_imagem

    # devolve a imagem normal pós identificação da IA
    return send_file(resultado_da_imagem, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)


