import cv2

def tratar_imagem(image_path):
    original_img = cv2.imread(image_path)

    resized_img = cv2.resize(original_img, (640, 640))

    # Converter a imagem para tons de cinza
    gray_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)

    # Converter de volta para 3 canais
    gray_img_3ch = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
    return gray_img_3ch