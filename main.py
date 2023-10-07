import streamlit as st
import pandas as pd
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip
import os
import glob
import numpy as np
import ffmpeg
import openai
import dotenv

# .envファイルを読み込み
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

URLS = []
STATIC_PATH = "./static"
apps = []
MP4_PATH = "./movie/"


def shorter_than_ten_minute(info, *, incomplete):
    """Download only videos shorter than ten minute (or with unknown duration)"""
    duration = info.get('duration')
    if duration and duration > 60 * 2:
        return 'The video is too longer'


def append_apps(path):
    apps.append(path)


def convert_video_to_audio(video_file, audio_file):
    ffmpeg.input(video_file).output(audio_file, acodec='mp3').run()


def get_audio_filename(video_filename):
    audio_filename = video_filename.rsplit('.', 1)[0] + '.mp3'
    return audio_filename


def create_screanshots(mp4_file_name):
    file = os.path.basename(os.path.splitext(mp4_file_name)[0])
    
    # フォルダ内のすべてのファイル(スクリーンショット)を取得します（サブディレクトリも含む）。
    files = glob.glob(STATIC_PATH + '**/*', recursive=True)
    for f in files:
        # ファイルのみ削除します（サブディレクトリは削除しません）。
        if os.path.isfile(f):
            os.remove(f)
    
    # 動画を開いてスクリーンショットを取得
    clip = VideoFileClip(mp4_file_name)
    duration = int(clip.duration)

    for i in range(duration):
        screenshot_file = f'{i}_{file}.jpg'
        # スクリーンショットを保存
        clip.save_frame(f'static/{screenshot_file}', t=i)
        # スクリーンショットファイルのパスを格納
        append_apps(f'./app/static/{screenshot_file}')


def create_trascript(mp4_file_name):
    # 音声ファイルのパス
    audio_file_path = get_audio_filename(mp4_file_name)

    # もし既に同じ名前の音声ファイルが存在する場合、削除する
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)

    # 動画を音声に変換
    convert_video_to_audio(mp4_file_name, audio_file_path)

    # 音声を時間ごとに文字列に変換
    with open(audio_file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(
            file=audio_file,
            model="whisper-1",
            prompt="これは日本のCMの音声です。適切な日本語の字幕を付けてください。",
            response_format="srt",
            language="ja"
            
        )
    return transcript


def main():
    transcript = ''
    # ユーザーからYouTubeのURLを取得し、YoutubeDLを使用して動画をダウンロード
    with st.expander("Youtube取得"):
        url = st.text_input('Enter the YouTube video URL')
        URLS.append(url)

        # ボタンが押されたときに動画をダウンロードとスクリーンショットの取得を開始
        if st.button('Download videos'):
            try:
                # 動画をダウンロード
                ydl_opts = {
                    'match_filter': shorter_than_ten_minute,
                    'format': 'best',
                    'outtmpl': f'{MP4_PATH}%(title)s.%(ext)s',  # 保存先のパスを指定
                }
                file_names = []
                with YoutubeDL(ydl_opts) as ydl:
                    for url in URLS:
                        info = ydl.extract_info(url, download=True)
                        file_names.append(ydl.sanitize_info(info)['requested_downloads'][0]['filename'])
                st.success('Screenshots downloaded successfully!')
            except Exception as e:
                st.error('An error occurred: ' + str(e))   

    # ディレクトリ内の全ての .mp4 ファイルを取得します。
    mp4_files = glob.glob(MP4_PATH + '*.mp4')
    # mp4_filesの中身を全て加工
    mp4_files = [os.path.basename(mp4_file) for mp4_file in mp4_files]
    if not mp4_files:
        st.warning("上記よりYoutubeでCM動画のURLを入力して、動画をダウンロードしてください。")
        st.stop()
    mp4_file_name = mp4_files[0]

    # selectboxで動画を選択する
    mp4_file_name = st.selectbox(
        'Select video to display',
        mp4_files
    )

    if st.button('Create info'):
        with st.spinner('Create info...'):
            create_screanshots(os.path.join(MP4_PATH, mp4_file_name))
            transcript = create_trascript(os.path.join(MP4_PATH, mp4_file_name))

    data_df = pd.DataFrame({"apps": apps})

    # 画面を2分割
    col1, col2 = st.columns([3, 1])

    # 動画表示
    col1.subheader("video")
    video_file = open(f'{os.path.join(MP4_PATH, mp4_file_name)}', 'rb')
    video_bytes = video_file.read()
    col1.video(video_bytes)

    # スクリーンショット表示
    col2.subheader("screanshots")
    col2.data_editor(
        data_df,
        column_config={
            "apps": st.column_config.ImageColumn(
                "Preview Image", width="small", help="Streamlit app preview screenshots"
            )
        },
        hide_index=False,
        height=300,
    )

    # expanderで文字列を表示
    with st.expander("transcript"):
        st.write(transcript)


if __name__ == "__main__":
    main()
