import socket
import speech_recognition as sr
import threading  # 追加
import time  # <--- newly imported

# サーバ側の設定
HOST = '0.0.0.0'  # 全インターフェースで待ち受け
PORT = 50007      # 適宜ポート番号を設定

# オーディオのパラメータ設定（例：16kHz, 16bit PCM）
SAMPLE_RATE = 44100  # サンプルレート
SAMPLE_WIDTH = 2     # 16bitの場合は2バイト
CHUNK_DURATION = 0.1   # 一度に認識する音声の時間（秒）
CHUNK_SIZE = SAMPLE_RATE * SAMPLE_WIDTH * CHUNK_DURATION

recognizer = sr.Recognizer()

def process_audio(audio_bytes):
    # AudioDataオブジェクトを作成
    audio_data = sr.AudioData(audio_bytes, SAMPLE_RATE, SAMPLE_WIDTH)
    try:
        # GoogleのWeb Speech APIを使用して認識
        text = recognizer.recognize_google(audio_data, language="ja-JP")
        print("認識結果:", text)
    except sr.UnknownValueError:
        print("認識できませんでした")
    except sr.RequestError as e:
        print("APIリクエストエラー:", e)

buffer = b''
count = 0
last_data_time = time.time()  # Initialize last data receipt time
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)  # 1秒のタイムアウトを設定
        s.bind((HOST, PORT))
        s.listen(1)
        print("接続待機中：{}:{}".format(HOST, PORT))
        while True:
            try:
                conn, addr = s.accept()
            except socket.timeout:
                # タイムアウトでループ上でKeyboardInterruptが拾えるようにする
                continue
            with conn:
                # print("接続先:", addr)
                conn.settimeout(1)
                while True:
                    try:
                        data = conn.recv(4096)
                    except socket.timeout:
                        continue
                    if not data:
                        break
                    buffer += data
                    count += len(data)

                    if time.time() - last_data_time >= 2:
                        count = 0
                        buffer = b''

                    last_data_time = time.time() 

                    while count >= CHUNK_SIZE:
                        chunk = buffer
                        count = 0
                        threading.Thread(target=process_audio, args=(chunk,), daemon=True).start()
except KeyboardInterrupt:
    print("Ctrl+Cが押されたため、終了します")