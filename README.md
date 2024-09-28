# controller-identificacao-ia

## Criar o ambiente virtual:
```sh
python -m venv venv
```
## Ativar o ambiente virtual:
```sh
.\venv\Scripts\activate
```
## Instale as dependências:
```sh
pip install -r requirements.txt
```
## Execute o comando

```sh
python app.py
```

## Rotas:

## /predict/<id_usuario>
- Enviar uma imagem a ser processada pela IA e um id de usuario na rota, retornando um json e salvando no firebase

## /historico/<id_usuario>
- retorna uma lista com todos os jsons que aquele usuario já fez até agora