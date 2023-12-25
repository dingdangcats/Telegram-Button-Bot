import requests
import json

TOKEN = "替换这里"  # 请替换为您的机器人Token
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

last_messages = {}  # 用于存储用户的最后一条消息
last_photos = {}    # 用于存储用户发送的最后一张图片的文件ID

def get_updates(last_update_id=None):
    url = URL + "getUpdates"
    if last_update_id:
        url += "?offset=" + str(last_update_id + 1)
    r = requests.get(url)
    response = json.loads(r.content)
    return response.get('result', [])

def handle_callback_query(update):
    query = update["callback_query"]
    chat_id = query["message"]["chat"]["id"]
    message_id = query["message"]["message_id"]

    # 检查回调查询的数据
    if query["data"] == "/close":
        if chat_id in last_messages:
            del last_messages[chat_id]
            send_message(chat_id, "进程已关闭。")
            delete_message(chat_id, message_id)  # 删除包含关闭按钮的消息
        else:
            send_message(chat_id, "没有进行中的进程。")

def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    url = URL + "sendMessage"
    requests.post(url, data=payload)

def send_photo(chat_id, photo_id, caption=None):
    payload = {
        "chat_id": chat_id,
        "photo": photo_id,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    url = URL + "sendPhoto"
    requests.post(url, data=payload)

def handle_start(update):
    chat_id = update["message"]["chat"]["id"]
    first_name = update["message"]["from"]["first_name"]
    welcome_message = (
        f"👋 *你好, {first_name}。欢迎使用个性化按钮机器人！*\n\n"
        "您需要先发送您的文本内容。随后,您需要再根据提示发送一个按钮信息:\n\n"
        "*格式: * `按钮显示文字 - 按钮链接`\n\n"
        "*您现在可以发送消息了!*"
    )
    send_message(chat_id, welcome_message)

def handle_text_message(chat_id, message_text):
    if '-' in message_text and chat_id in last_messages:
        parts = message_text.split('-')
        if len(parts) == 2:
            button_text = parts[0].strip()
            button_url = parts[1].strip()
            keyboard = {"inline_keyboard": [[{"text": button_text, "url": button_url}]]}
            send_message(chat_id, last_messages[chat_id], reply_markup=keyboard)
            del last_messages[chat_id]
        else:
            send_message(chat_id, "按钮信息格式错误，请按照 '按钮显示文字 - 按钮链接' 格式发送。")
    else:
        last_messages[chat_id] = message_text
        close_keyboard = {"inline_keyboard": [[{"text": "重新发送", "callback_data": "/close"}]]}
        send_message(chat_id, "消息已接收，请发送按钮信息。", reply_markup=close_keyboard)

def handle_photo_message(chat_id, message_caption, photo_id):
    last_photos[chat_id] = photo_id
    last_messages[chat_id] = message_caption
    close_keyboard = {"inline_keyboard": [[{"text": "重新发送", "callback_data": "/close"}]]}
    send_photo(chat_id, photo_id, message_caption)
    send_message(chat_id, "文字描述型图片已接收，请发送按钮信息。", reply_markup=close_keyboard)

def delete_message(chat_id, message_id):
    url = URL + "deleteMessage"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id
    }
    requests.post(url, data=payload)

def handle_message(update):
    if "callback_query" in update:
        handle_callback_query(update)
    elif "message" in update:
        chat_id = update["message"]["chat"]["id"]
        if "text" in update["message"]:
            message_text = update["message"]["text"]
            if message_text == "/start":
                handle_start(update)
            elif message_text == "/close":
                if chat_id in last_messages:
                    del last_messages[chat_id]
                    send_message(chat_id, "进程已关闭")
                else:
                    send_message(chat_id, "没有进行中的进程")
            else:
                handle_text_message(chat_id, message_text)
        elif "photo" in update["message"]:
            photos = update["message"]["photo"]
            photo_id = photos[-1]["file_id"]  # 选择最高质量的图片
            message_caption = update["message"].get("caption", "")
            handle_photo_message(chat_id, message_caption, photo_id)
        else:
            send_message(chat_id, "请发送文本消息或带说明的图片消息。")

def main():
    last_update_id = 0
    while True:
        updates = get_updates(last_update_id)
        for update in updates:
            update_id = update["update_id"]
            if last_update_id < update_id:
                last_update_id = update_id
                handle_message(update)

if __name__ == "__main__":
    main()
