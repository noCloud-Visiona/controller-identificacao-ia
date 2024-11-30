import os
import cv2
import requests
import datetime
import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer
from services import baixar_imagem, validar_formato_imagem
from services import montar_json_response, processar_imagem_com_ia, enviar_json_final


def processar_imagem(band16_url, image_dir, json_data, job_id, processing_jobs, id_usuario):
    try:
        print("[INFO] Iniciando o processo de imagem...")

        # Baixar a imagem
        print("[INFO] Baixando a imagem...")
        image_path = baixar_imagem(band16_url, image_dir=image_dir)
        validar_formato_imagem(image_path)
        print(f"[INFO] Imagem baixada com sucesso: {image_path}")

        # Priorizar user_geometry se disponível
        user_geometry = json_data.get('user_geometry')
        if user_geometry:
            print(f"[INFO] Usando user_geometry para o recorte: {user_geometry}")
            coordinates = user_geometry['coordinates'][0]
            minx, miny = coordinates[0]
            maxx, maxy = coordinates[2]
        else:
            print("[INFO] user_geometry não encontrado. Usando bbox padrão.")
            bbox = json_data.get('bbox')
            if not bbox:
                raise ValueError("A área de recorte 'bbox' não foi especificada no JSON de entrada.")
            minx, miny, maxx, maxy = bbox

        print(f"[INFO] Coordenadas de recorte: minx={minx}, miny={miny}, maxx={maxx}, maxy={maxy}")

        # Conversão de coordenadas WGS84 para UTM
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32723", always_xy=True)
        minx_utm, miny_utm = transformer.transform(minx, miny)
        maxx_utm, maxy_utm = transformer.transform(maxx, maxy)
        print(f"[INFO] Coordenadas bbox convertidas para UTM: minx_utm={minx_utm}, miny_utm={miny_utm}, maxx_utm={maxx_utm}, maxy_utm={maxy_utm}")

        # Abrir a imagem e verificar os limites
        with rasterio.open(image_path) as src:
            print(f"[INFO] Sistema de coordenadas da imagem: {src.crs}")
            print(f"[INFO] Limites da imagem: {src.bounds}")

            # Verificar se as coordenadas estão dentro dos limites da imagem
            if (minx_utm < src.bounds.left or maxx_utm > src.bounds.right or
                miny_utm < src.bounds.bottom or maxy_utm > src.bounds.top):
                raise ValueError("[ERRO] As coordenadas do bbox estão fora dos limites da imagem.")

            # Calcular a janela de corte
            print("[INFO] Calculando a janela de corte...")
            window = from_bounds(minx_utm, miny_utm, maxx_utm, maxy_utm, src.transform)
            profile = src.profile  # Copiar o perfil da imagem original
            print(f"[INFO] Dimensões da janela de corte: largura={window.width}, altura={window.height}")

            # Atualizar o perfil para o novo tamanho
            profile.update(
                width=window.width,
                height=window.height,
                transform=rasterio.windows.transform(window, src.transform)
            )

            # Criar um arquivo recortado temporário
            cropped_image_path = os.path.join(os.path.dirname(image_path), "cropped_image.tif").replace("\\", "/")
            print(f"[INFO] Salvando a imagem recortada em: {cropped_image_path}")

            with rasterio.open(cropped_image_path, "w", **profile) as dst:
                for i in range(1, src.count + 1):
                    print(f"[INFO] Processando banda {i}/{src.count}")
                    dst.write(src.read(i, window=window), i)
            print("[INFO] Imagem recortada salva com sucesso.")

        # Processar a imagem recortada
        print("[INFO] Iniciando o processamento da imagem com IA...")
        imagem_sem_nuvem, imagem_sem_sombra, imagem_nuvem, imagem_sombra, thumbnail_sem_nuvem, thumbnail_sem_sombra, thumbnail_nuvem, thumbnail_sombra, thumbnail_imagem, percent, imagem_tratada, thumbnail_imagem_tratada = processar_imagem_com_ia(cropped_image_path)
        print("[INFO] Processamento concluído.")

        # Obter informações de data e hora
        data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
        hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[INFO] Data atual: {data_atual}, Hora atual: {hora_atual}")

        # Enviar imagens para o bucket e obter URLs
        print("[INFO] Enviando imagens processadas para o bucket...")

         # Enviar imagem "sem nuvem"
        with open(thumbnail_imagem_tratada, 'rb') as thumbnail_imagem_tratada:
            files = {'thumbnail_imagem_tratada': thumbnail_imagem_tratada}
            response_thumbnail_imagem_tratada_url = requests.post('http://host.docker.internal:3004/upload_image_tratada_png', files={'thumbnail_imagem_tratada': files['thumbnail_imagem_tratada']})
            thumbnail_imagem_tratada_url = response_thumbnail_imagem_tratada_url.json().get('tratada')
            print(f"[INFO] URL da imagem sem nuvem: {thumbnail_imagem_tratada_url}")

        # Enviar imagem "sem nuvem"
        with open(imagem_sem_nuvem, 'rb') as sem_nuvem_image:
            files = {'imagem_sem_nuvem': sem_nuvem_image}
            response_sem_nuvem = requests.post('http://host.docker.internal:3004/upload_imagem_sem_nuvem', files={'imagem_sem_nuvem': files['imagem_sem_nuvem']})
            imagem_sem_nuvem_url = response_sem_nuvem.json().get('imagem_sem_nuvem_url')
            print(f"[INFO] URL da imagem sem nuvem: {imagem_sem_nuvem_url}")

        # Enviar imagem "sem sombra"
        with open(imagem_sem_sombra, 'rb') as sem_sombra_image:
            files = {'imagem_sem_sombra': sem_sombra_image}
            response_sem_sombra = requests.post('http://host.docker.internal:3004/upload_imagem_sem_sombra', files={'imagem_sem_sombra': files['imagem_sem_sombra']})
            imagem_sem_sombra_url = response_sem_sombra.json().get('imagem_sem_sombra_url')
            print(f"[INFO] URL da imagem sem sombra: {imagem_sem_sombra_url}")

        # Enviar imagem "nuvem"
        with open(imagem_nuvem, 'rb') as nuvem_image:
            files = {'imagem_nuvem': nuvem_image}
            response_nuvem = requests.post('http://host.docker.internal:3004/upload_imagem_nuvem', files={'imagem_nuvem': files['imagem_nuvem']})
            imagem_nuvem_url = response_nuvem.json().get('imagem_nuvem_url')
            print(f"[INFO] URL da imagem com nuvem: {imagem_nuvem_url}")

        # Enviar imagem "sombra"
        with open(imagem_sombra, 'rb') as sombra_image:
            files = {'imagem_sombra': sombra_image}
            response_sombra = requests.post('http://host.docker.internal:3004/upload_imagem_sombra', files={'imagem_sombra': files['imagem_sombra']})
            imagem_sombra_url = response_sombra.json().get('imagem_sombra_url')
            print(f"[INFO] URL da imagem com sombra: {imagem_sombra_url}")
            
        # Enviar thumbnail "sem nuvem"
        with open(thumbnail_sem_nuvem, 'rb') as sem_nuvem_thumbnail:
            files = {'thumbnail_sem_nuvem': sem_nuvem_thumbnail}
            response_thumbnail_sem_nuvem = requests.post('http://host.docker.internal:3004/upload_thumbnail_sem_nuvem', files={'thumbnail_sem_nuvem': files['thumbnail_sem_nuvem']})
            thumbnail_sem_nuvem_url = response_thumbnail_sem_nuvem.json().get('thumbnail_sem_nuvem_url')
            print(f"[INFO] URL do thumbnail sem nuvem: {thumbnail_sem_nuvem_url}")

        # Enviar thumbnail "sem sombra"
        with open(thumbnail_sem_sombra, 'rb') as sem_sombra_thumbnail:
            files = {'thumbnail_sem_sombra': sem_sombra_thumbnail}
            response_thumbnail_sem_sombra = requests.post('http://host.docker.internal:3004/upload_thumbnail_sem_sombra', files={'thumbnail_sem_sombra': files['thumbnail_sem_sombra']})
            thumbnail_sem_sombra_url = response_thumbnail_sem_sombra.json().get('thumbnail_sem_sombra_url')
            print(f"[INFO] URL do thumbnail sem sombra: {thumbnail_sem_sombra_url}")

        # Enviar thumbnail "nuvem"
        with open(thumbnail_nuvem, 'rb') as nuvem_thumbnail:
            files = {'thumbnail_nuvem': nuvem_thumbnail}
            response_thumbnail_nuvem = requests.post('http://host.docker.internal:3004/upload_thumbnail_nuvem', files={'thumbnail_nuvem': files['thumbnail_nuvem']})
            thumbnail_nuvem_url = response_thumbnail_nuvem.json().get('thumbnail_nuvem_url')
            print(f"[INFO] URL do thumbnail com nuvem: {thumbnail_nuvem_url}")

        # Enviar thumbnail "sombra"
        with open(thumbnail_sombra, 'rb') as sombra_thumbnail:
            files = {'thumbnail_sombra': sombra_thumbnail}
            response_thumbnail_sombra = requests.post('http://host.docker.internal:3004/upload_thumbnail_sombra', files={'thumbnail_sombra': files['thumbnail_sombra']})
            thumbnail_sombra_url = response_thumbnail_sombra.json().get('thumbnail_sombra_url')
            print(f"[INFO] URL do thumbnail com sombra: {thumbnail_sombra_url}")

        # Enviar thumbnail da imagem original
        with open(thumbnail_imagem, 'rb') as imagem_thumbnail:
            files = {'thumbnail_imagem_original': imagem_thumbnail}
            response_thumbnail_imagem = requests.post('http://host.docker.internal:3004/upload_thumbnail_imagem_original', files={'thumbnail_imagem_original': files['thumbnail_imagem_original']})
            thumbnail_imagem_url = response_thumbnail_imagem.json().get('thumbnail_imagem_original_url')
            print(f"[INFO] URL do thumbnail da imagem original: {thumbnail_imagem_url}")

        # Montar o JSON final
        json_response = montar_json_response(
            json_data,
            percent,
            data_atual,
            hora_atual,
            id_usuario,
            imagem_sem_nuvem_url,
            imagem_sem_sombra_url,
            imagem_nuvem_url,
            imagem_sombra_url,
            thumbnail_sem_nuvem_url,
            thumbnail_sem_sombra_url,
            thumbnail_nuvem_url,
            thumbnail_sombra_url,
            thumbnail_imagem_url,
            imagem_tratada,
            thumbnail_imagem_tratada
        )
        
        print(f"[INFO] JSON final montado: {json_response}")
        processing_jobs[job_id]["status"] = "Análise concluída!"
        processing_jobs[job_id]["result"] = json_response

    except Exception as e:
        print(f"[ERRO] {str(e)}")
        processing_jobs[job_id]["status"] = "Ops... Algo de errado aconteceu!"
        processing_jobs[job_id]["result"] = str(e)
