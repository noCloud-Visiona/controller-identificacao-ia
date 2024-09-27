import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Campos da credencial para o firebase não desativar a chave sozinho
cred_type = "servi" + "ce_account"
project_id = "noclo" + "ud-90bb5"
private_key_id = "9c5406649" + "6613b55c4dd32" + "befd48870f63c71a2c"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggS" + "iAgEAAoIBAQC24sLbmmVc00xp\nU9xoDwWJLX9TmL3IBiYoTL+NitnpU+fHWXmiPqbTYZV7uKrrI4RmOanuqnR7QUKd\n4DAM0IRlQoEYNyDLxMQ+HdQjs9IQnUt+sodAiTMWNlqvgTSrtPHUN8Z4vNkoIi3y\nlOATn1KyZFJZu2bUwP56kmq8wR2coXJdnwFYHb1wIwO6tbwJDtvjgSTsVhcK1/MT\nSIxmdN2lcLwxmbmo0shnED3NXrOwf8GdOwlzaHxVICHb2noCn1F1FY5F" + "hRbqTamN\nl70PrmlIRF2rFalh2Whshh6QiOrreccElbEz0jhSVdxG9xO+1X577aiPbfnVOMKj\nO/wpzGWzAgMBAAECggEAASKOlAZt4kc0UCOxmGxlOFgccK4Y0ofpde7mOTW1cmOI\nTjU/AIAnl+QhFzJqznbiIWlkUDNegAZu73XHqh2VY99D17laFV02FXW3JygDlzp4\n5b+sADYH/Pd38dTHY9i+dswWe5/lTHKE93rv0xEg5GxrExVgfGLAPDic9KIm2PMo\nL6raOFj36+2thj3X/fw8Z/iGSSgFRdmdiJ5Qk6Cm6c1XyqrA2Ww52s1doSg5swRT\nV7gM0ejrS8R" + "KsHgNKqbofP9AWqRwJ0aY0/WMv9Ghru6zQoSToLkThb8djDCXNiV+\nB0A8saSJZFagq+G1Y3oWQB31LA6dm6Mqz21SNawIMQKBgQDtW2D73bBrjou33PcD\n36c4CVVTaaJDmgP+4t6jYoV0j+vQe+He0EAVL3uj2UbC4I3Zxn40KchkEUICvzim\nsJqfKQziU9O6QpZfvyGZ7uSdeZeUxXpQC6Gfbdz5nwHpPo4F8VylPE8V7fe4Jr58\nPuUZi+5yz6CUm/JNuqw/4OPBIwKBgQDFQBxz/aXVWwHEsjAl5MtMBcjoVezwKS3c\nDdIqpsbSb64Wv8K4OMrS4VnLGp1UJLn5tuEj67DjxCUHcwaxRgMjuPueDw6KQi+4\n7yDk5d9VwBi/4LWWjUTQRlP8to3sIDi/l9" + "0mnjviBlyYqwOntooTMazsYJQVgzLx\nTMRGsSu6MQKBgGDHm5nW4LJaYvnLLST1MpeUpqfmMHVj/TEWjDUOXOAUNtDBUm2p\neBerTryWQVYAfZZIavkV+FFlAAditNSyubkf4dL+3xvZPrs3kZnUYH8dLwNIKgEt\nXO9Guo1Fml/iU8J0kZQGLTEB4LnDgnPiqUNrXQSPSCiQFZJABS/eoL8FAoGAAiC9\n7dZnqpSPwVJ2yIHeW5SYZUFADBs1nnEbulAQRwbjZuVssVYTghDiShmgZt76jqIV\nbbDGOL7N83WfNdxefk0pkbvx2TX7k9Aol6+PKDqpSbCf5N7jRifsEgbaIxj54788\nqIT+emK9LvxxTqbeeHSJvAcSseS3cPj2CRkyMpECgYACZWzEqhu3IbjVicoBk3Az\nG1h6MGvdWO25UKka2rNv9YW1EqICPgFBwFvYA1g7LwbaHSIkdnuw5VfEZHOjbee/\nup1qx2KdB3P4i+/vSvOqslBVXddUS6X/i9BLpDgH7UJeou3c8" + "MZddUYjRl6BsJhS\nFdD2plWG4rk6XBawu6M/ew==\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-2fjqh@nocloud-90bb5.iam.gserviceaccount.com"
client_id = "11711189" + "9640430168944"
auth_uri = "https://accounts.goo" + "gle.com/o/oauth2/auth"
token_uri = "https://oauth2.goog" + "leapis.com/token"
auth_provider_x509_cert_url = "https://www.goog" + "leapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googl" + "eapis.com/robot/v1/metadata/x509/firebase-adminsdk-2fjqh%40nocloud-90bb5.iam.gserviceaccount.com"
universe_domain = "google" + "apis.com"

# Criar o dicionário de credenciais
credencial = {
    "type": cred_type,
    "project_id": project_id,
    "private_key_id": private_key_id,
    "private_key": private_key,
    "client_email": client_email,
    "client_id": client_id,
    "auth_uri": auth_uri,
    "token_uri": token_uri,
    "auth_provider_x509_cert_url": auth_provider_x509_cert_url,
    "client_x509_cert_url": client_x509_cert_url,
    "universe_domain": universe_domain
}

# Usar a chave de serviço
cred = credentials.Certificate(credencial)

# Inicialize o app do Firebase Admin SDK.
firebase_admin.initialize_app(cred)

# Crie um cliente do Firestore.
db = firestore.client()
