import telebot
from telebot import types
import requests
from datetime import datetime

# ===== Configurações do bot Telegram =====
bot = telebot.TeleBot('8280281003:AAFF3DeiUcXiKpf4UPiuMI9dAXGWWyxuLEU')  # Token do seu bot

# ===== Configurações do Trello =====
TRELLO_KEY = '3178db52eaba1e53042c73bba4647f20'
TRELLO_TOKEN = 'ATTA8d5696c9eba1e6081b930f22676f19566f0e5ea44567ae35ea0af77fe834e9b38EFE4EE6'
TRELLO_LIST_ID = '68a4918423f12e2180552bef'

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
        if message.text == "teleaco123":
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

# ===== Executa o bot =====
bot.infinity_polling()
