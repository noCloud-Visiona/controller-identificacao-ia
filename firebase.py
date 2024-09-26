import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use uma conta de serviço.
cred = credentials.Certificate('firebase/serviceAccount.json')

# Inicialize o app do Firebase Admin SDK.
firebase_admin.initialize_app(cred)

# Crie um cliente do Firestore.
db = firestore.client()
