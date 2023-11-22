from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import sqlite3
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)

# LINE Botの設定
YOUR_CHANNEL_ACCESS_TOKEN = 'caJal+9vjkxrQnDCoNvdIUJp+6RbN0CV8SevJdhx7VPmFcLWzI7xjsRhQ7RYmjm5LGhkUU9Co8gCp2hvOfarpHUmQpPqpsiMb6m8en7nzrF2w8PJJRGbcs0x6NhTEUfgUBZTa0vaodq9ZeBD8znLFAdB04t89/1O/w1cDnyilFU='
YOUR_CHANNEL_SECRET = 'e18551997846615098b69cef7933efb2'
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# SQLiteデータベースの設定
DATABASE = 'schedule.db'

# APSchedulerの初期化
scheduler = BackgroundScheduler()
scheduler.start()


# データベースから終了時刻が過ぎた予定を削除するタスク
def remove_expired_schedules():
    current_time = datetime.now()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM schedules
        WHERE end_time < ?
    ''', (current_time,))
    conn.commit()
    conn.close()

# 定期的に予定を削除するタスクをスケジューラに登録
scheduler.add_job(remove_expired_schedules, 'interval', hours=1)  # 1時間ごとに実行


def create_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time DATETIME,
            end_time DATETIME,
            event_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_table()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # 「今後の予定」が送信された場合
    if user_message == "今後の予定":
        schedules = get_upcoming_schedules()
        if schedules:
            response_message = "今後の予定:\n"
            for schedule in schedules:
                response_message += f"{schedule[2]}\n開始日時: {schedule[0]}\n終了日時: {schedule[1]}\n\n"
        else:
            response_message = "今後の予定はありません。"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_message)
        )
        return    

    # メッセージが正しい形式か確認
    try:
        event_name, start_time_str, end_time_str = user_message.split(',')
        start_time = datetime.strptime(start_time_str.strip(), '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_time_str.strip(), '%Y-%m-%d %H:%M')
    except ValueError:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="メッセージの形式が正しくありません。正しい形式で入力してください。")
        )
        return

    # 既存の予定との重複を確認
    existing_schedule = get_overlap_schedule(start_time, end_time)

    if existing_schedule:
        existing_event_name = existing_schedule[2]
        existing_start_time = existing_schedule[0]
        existing_end_time = existing_schedule[1]

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"指定された期間には既に予定が入っています。\n"
                                  f"既存の予定: {existing_event_name}\n"
                                  f"開始日時: {existing_start_time}\n"
                                  f"終了日時: {existing_end_time}")
        )
        return

    # データベースに予定を追加
    add_schedule(start_time, end_time, event_name)

    # 追加完了のメッセージを送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="予定が追加されました。")
    )

def get_overlap_schedule(start_time, end_time):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM schedules
        WHERE start_time < ? AND end_time > ?
    ''', (end_time, start_time))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_schedule(start_time, end_time, event_name):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO schedules (start_time, end_time, event_name)
        VALUES (?, ?, ?)
    ''', (start_time, end_time, event_name))
    conn.commit()
    conn.close()

def get_upcoming_schedules():
    current_time = datetime.now()
    two_weeks_later = current_time + timedelta(weeks=2)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM schedules
        WHERE start_time >= ? AND start_time <= ?
        ORDER BY start_time
    ''', (current_time, two_weeks_later))
    schedules = cursor.fetchall()
    conn.close()
    return schedules

if __name__ == "__main__":
    app.run()
