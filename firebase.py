import json
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém a chave do serviço do ambiente
service_account_info = os.getenv("FIREBASE_SERVICE_ACCOUNT")

# Converte a string JSON para um dicionário
cred = credentials.Certificate(json.loads(service_account_info))

# Inicialize o app do Firebase Admin SDK.
firebase_admin.initialize_app(cred)

# Crie um cliente do Firestore.
db = firestore.client()
