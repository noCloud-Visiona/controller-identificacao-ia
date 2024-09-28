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

## /predict
- Enviar uma imagem e um json contendo:
{"id": valor numerico que será o id do usuario}

## /historico/<id_usuario>
- retorna uma lista com todos os jsons que aquele usuario já fez até agora, exceto a imagem original por enquanto (o tamanho em base64 fica maior que 1MB que é o quanto o Firebase aceita em 1 campo só)