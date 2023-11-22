from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from flask_sqlalchemy import SQLAlchemy




app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedule.db'
db = SQLAlchemy(app)

line_bot_api = LineBotApi('caJal+9vjkxrQnDCoNvdIUJp+6RbN0CV8SevJdhx7VPmFcLWzI7xjsRhQ7RYmjm5LGhkUU9Co8gCp2hvOfarpHUmQpPqpsiMb6m8en7nzrF2w8PJJRGbcs0x6NhTEUfgUBZTa0vaodq9ZeBD8znLFAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('e18551997846615098b69cef7933efb2')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.split(',')
    if len(user_message) == 3:
        schedule_name, start_time, end_time = user_message
        new_schedule = Schedule(name=schedule_name, start_time=start_time, end_time=end_time)
        db.session.add(new_schedule)
        try:
            db.session.commit()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="予定が追加されました。")
            )
        except:
            db.session.rollback()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="予定が重複しています。")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="正しい形式で予定を入力してください。")
        )



class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)


if __name__ == "__main__":
    app.run(debug=True)
