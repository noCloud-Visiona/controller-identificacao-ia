import base64
import json    

# Serializa a imagem para um JSON
def transforma_imagem_em_json(resultado_da_imagem):
    with open(resultado_da_imagem, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    image_json = json.dumps({"image_data": encoded_string})
    return image_json

#if (path da imagem):
#    image_json = transforma_imagem_em_json(path da imagem)
#    print("Imagem serializada em JSON:")
#    print(image_json)

############################################################################

# Desserializa o JSON de volta para a imagem
def transforma_json_em_imagem(image_json, output_path):
    try:
        image_data = json.loads(image_json).get("image_data", "")
        if not image_data:
            raise ValueError("Imagem não encontrada no JSON")
        
        with open(output_path, "wb") as output_file:
            output_file.write(base64.b64decode(image_data))
        return True, "Imagem decodificada com sucesso"
    except Exception as e:
        return False, f"Erro ao decodificar a imagem: {str(e)}"

#output_image_path = "(path onde a imagem vai ser salva)"
#output_image_path = "IA/img/output_image.png"

#if (path da imagem):
#    transforma_json_em_imagem(image_json, output_image_path)
#    print(f"Imagem desserializada e salva em: {output_image_path}")

#Obs: No lugar da variavel "imagem_json" passar uma variavel com uma imagem em formato json