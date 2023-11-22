from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import os

#token取得---------------------------------------------------
line_bot_api = LineBotApi('caJal+9vjkxrQnDCoNvdIUJp+6RbN0CV8SevJdhx7VPmFcLWzI7xjsRhQ7RYmjm5LGhkUU9Co8gCp2hvOfarpHUmQpPqpsiMb6m8en7nzrF2w8PJJRGbcs0x6NhTEUfgUBZTa0vaodq9ZeBD8znLFAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('e18551997846615098b69cef7933efb2')
#---------------------------------------------------------------


#確認------------------------------
app = Flask(__name__)
app.debug = False

@app.route("/")
def say_hello():
    return "Hello!!!!!"
#----------------------------------


#LINEbotを呼び出す---------------------------------
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'
#----------------------------------------------------------


#ダジャレ開始--------------------------------------------------------
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    df_list=[['ふとん', 'ふとんがふっとんだ'],
            ['みかん', 'アルミ缶のうえにあるみかん'],
            ['ねこ', 'ねこが寝ころんだ'],
            ['いす', 'いすに居座る'],
            ['委員会', '委員会に入っていいんかい'],
            ['いくら', 'このいくら、いくらですか？'],
            ['飲酒', '飲酒していいんしゅか？'],
            ['お金', 'お金はおっかねえ'],
            ['カンニング', 'カンニングはいかんにんぐ']]

    for i in range(len(df_list)):
        joke=None
        if event.message.text==df_list[i][0]:
            joke=df_list[i][1]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=joke))
        else:continue

    if joke==None:
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='すまん、思いつかんかった!!'))

#------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)

