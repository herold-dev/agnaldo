import telebot
from telebot import types
import requests
from datetime import datetime
import os
from flask import Flask, request

# ===== variaveis =====
TRELLO_KEY = os.environ.get('TRELLO_KEY')
TRELLO_TOKEN = os.environ.get('TRELLO_TOKEN')
TRELLO_LIST_ID = os.environ.get('TRELLO_LIST_ID')
TELEGRAM_BOT = os.environ.get('TELEGRAM_BOT')
SENHA_BOT = os.environ.get('SENHA_BOT')

# ===== Configurações do bot Telegram =====
bot = telebot.TeleBot(TELEGRAM_BOT)

# ===== Configuração do Flask =====
app = Flask(__name__)

usuario_data = {}

# ===== Lista de riscos =====
riscos = [
    'Risco Estratégico',
    'Risco Operacional',
    'Risco de Imagem / Reputação',
    'Risco Legal / Conformidade',
    'Risco de Integridade',
    'Risco Financeiro / Orçamentário',
    'Risco Patrimonial',
    'Risco Externo'
]

# Dados temporários por usuário
usuario_data = {}

# ===== Rota de Health Check para UptimeRobot =====
@app.route('/')
def health_check():
    return 'Bot está online! 🤖', 200

# ===== Rota do Webhook do Telegram =====
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Erro', 400

# ===== Comando personalizado: /registrar_risco =====
@bot.message_handler(commands=['registrar_risco'])
def solicitar_senha(msg: types.Message):
    bot.send_message(msg.chat.id, "Digite a senha para iniciar o registro do risco:")
    usuario_data[msg.chat.id] = {"etapa": "aguardando_senha"}

# ===== Processa mensagens em todas as etapas =====
@bot.message_handler(func=lambda message: True)
def processar_mensagem(message: types.Message):
    chat_id = message.chat.id

    if chat_id not in usuario_data:
        return

    etapa = usuario_data[chat_id].get("etapa")

    # Etapa 1: Validar senha
    if etapa == "aguardando_senha":
        if message.text == SENHA_BOT:
            usuario_data[chat_id]["etapa"] = "aguardando_risco"
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            for risco in riscos:
                markup.add(types.KeyboardButton(risco))
            bot.send_message(chat_id, "✅ Senha correta! Agora, selecione o tipo de risco:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "❌ Senha incorreta. Tente novamente.")

    # Etapa 2: Captura do risco
    elif etapa == "aguardando_risco":
        if message.text in riscos:
            usuario_data[chat_id]["risco"] = message.text
            usuario_data[chat_id]["etapa"] = "aguardando_observacao"
            bot.send_message(chat_id, "📝 Agora, digite a observação sobre este risco:")
        else:
            bot.send_message(chat_id, "Por favor, selecione um risco válido usando o menu.")

    # Etapa 3: Captura da observação
    elif etapa == "aguardando_observacao":
        risco = usuario_data[chat_id]["risco"]
        observacao = message.text
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        titulo = f"{risco} - {data_hora}"
        descricao = f"Risco: {risco}\nObservação: {observacao}\nData/Hora: {data_hora}"

        # Enviar para o Trello
        url = "https://api.trello.com/1/cards"
        query = {
            'key': TRELLO_KEY,
            'token': TRELLO_TOKEN,
            'idList': TRELLO_LIST_ID,
            'name': titulo,
            'desc': descricao
        }

        response = requests.post(url, params=query)

        if response.status_code == 200:
            bot.send_message(chat_id, "✅ Risco registrado com sucesso no Trello!")
        elif response.status_code == 401:
            bot.send_message(chat_id, "❌ Erro 401: Key ou Token inválidos no Trello.")
        elif response.status_code == 404:
            bot.send_message(chat_id, "❌ Erro 404: Lista ou Quadro do Trello não encontrado.")
        else:
            bot.send_message(chat_id, f"❌ Erro {response.status_code}: {response.text}")

        # Limpa dados
        usuario_data.pop(chat_id, None)

# ===== Inicialização para Render =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

