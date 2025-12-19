import os
import time
from flask import Flask, request, jsonify
from iqoptionapi.stable_api import IQ_Option

app = Flask(__name__)

# Configurações via Variáveis de Ambiente (Railway)
IQ_EMAIL = os.environ.get("IQ_EMAIL")
IQ_PASSWORD = os.environ.get("IQ_PASSWORD")
API_TOKEN = os.environ.get("API_TOKEN", "minha_senha_secreta") # Proteção

print("🔄 Iniciando serviço...")
API = IQ_Option(IQ_EMAIL, IQ_PASSWORD)

def connect_iq():
    check, reason = API.connect()
    if check:
        print("✅ Conectado na IQ Option")
    else:
        print(f"❌ Erro ao conectar: {reason}")
    return check

# Tenta conectar ao iniciar
connect_iq()

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "online", "message": "Trader Bot is Running"}), 200

@app.route('/trade', methods=['POST'])
def trade():
    # 1. Segurança Básica
    token_recebido = request.headers.get('x-api-key')
    if token_recebido != API_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Garante conexão
    if not API.check_connect():
        print("⚠️ Conexão perdida. Reconectando...")
        connect_iq()

    data = request.json
    par = data.get('pair').upper()
    acao = data.get('action').lower() # call ou put
    valor = float(data.get('amount'))
    tempo = int(data.get('exp'))

    # 3. Executa
    print(f"🚀 Ordem Recebida: {acao} | {par} | ${valor}")
    status, id_ordem = API.buy(valor, par, acao, tempo)

    if status:
        # Verifica resultado (bloqueante)
        resultado = API.check_win_v3(id_ordem)
        lucro = resultado if resultado > 0 else -valor
        return jsonify({
            "status": "success",
            "win": lucro > 0,
            "lucro": lucro
        })
    else:
        return jsonify({"status": "error", "message": "IQ recusou a ordem"}), 400

if __name__ == '__main__':
    app.run()