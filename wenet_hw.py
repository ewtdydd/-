import tkinter as tk
from tkinter import filedialog, scrolledtext
from pyaudio import PyAudio, paInt16, Stream
import wave
import threading
import wenet
from googletrans import Translator

framerate = 16000  # 采样率
num_samples = 2000  # 采样点
channels = 1  # 声道
sampwidth = 2  # 采样宽度2字节
FILEPATH = 'speech.wav'  # 确保默认文件名是speech.wav
TRANSLATED_FILEPATH = 'translated.txt'
is_recording = False
is_playing = False


def reset_labels():
    """Reset the text of labels to initial state."""
    status_label.config(text="")
    result_text.delete(1.0, tk.END)
    translation_text.delete(1.0, tk.END)


def start_record():
    global is_recording
    reset_labels()
    is_recording = True
    threading.Thread(target=record).start()


def stop_record():
    global is_recording
    is_recording = False


def record():
    pa = PyAudio()
    stream = pa.open(format=paInt16, channels=channels,
                     rate=framerate, input=True, frames_per_buffer=num_samples)
    my_buf = []
    status_label.config(text='正在录音...')

    while is_recording:
        string_audio_data = stream.read(num_samples)
        my_buf.append(string_audio_data)
    status_label.config(text='录音结束.')
    save_wave_file(FILEPATH, my_buf)  # 确保保存的文件是FILEPATH，即speech.wav
    stream.close()
    wenet_('1')  # 假设录音完成后进行中文识别


def save_wave_file(filepath, data):
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes(b''.join(data))
    wf.close()


def translate_text(text, src='zh-cn', dest='en'):
    translator = Translator()
    translation = translator.translate(text, src=src, dest=dest)
    return translation.text, translation.extra_data['confidence']


def save_translation(filepath, translation):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(translation)


def wenet_(n):
    if n == '1':
        model = wenet.load_model('chinese')
    elif n == '2':
        model = wenet.load_model('english')
    else:
        status_label.config(text='输入错误！')
        return
    status_label.config(text='识别中...')
    root.update_idletasks()
    result = model.transcribe(FILEPATH)  # 使用FILEPATH，即speech.wav
    text = result['text']
    confidence = result.get('confidence', '未知')
    result_text.insert(tk.END, f'识别结果: {text}\n置信度: {confidence}\n')
    root.update_idletasks()

    if n == '1':
        status_label.config(text='翻译中...')
        root.update_idletasks()
        translation, confidence = translate_text(text)
        translation_text.insert(tk.END, f'翻译结果: {translation}\n')
        save_translation(TRANSLATED_FILEPATH, translation)
        status_label.config(text=f'翻译结果已保存到 {TRANSLATED_FILEPATH}')
    else:
        status_label.config(text='')


def select_file():
    reset_labels()
    global FILEPATH
    FILEPATH = filedialog.askopenfilename()
    if FILEPATH:
        status_label.config(text=f'已选择文件: {FILEPATH}')
        wenet_('1')


def refresh_screen():
    reset_labels()
    status_label.config(text='刷新成功!')


def play_audio():
    global is_playing
    if is_playing:
        return
    is_playing = True
    threading.Thread(target=_play_audio).start()


def _play_audio():
    global is_playing
    wf = wave.open(FILEPATH, 'rb')
    pa = PyAudio()
    stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                     channels=wf.getnchannels(),
                     rate=wf.getframerate(),
                     output=True)
    data = wf.readframes(num_samples)
    while data:
        stream.write(data)
        data = wf.readframes(num_samples)
    stream.close()
    pa.terminate()
    is_playing = False
    status_label.config(text='音频播放结束.')


def main():
    global root
    root = tk.Tk()
    root.title("语音识别与翻译")
    root.geometry("900x600")  # 固定窗口大小
    root.resizable(False, False)

    record_start_button = tk.Button(root, text="开始录音", command=start_record, width=20, height=2)
    record_start_button.pack(pady=10)

    record_stop_button = tk.Button(root, text="停止录音", command=stop_record, width=20, height=2)
    record_stop_button.pack(pady=10)

    select_file_button = tk.Button(root, text="选择文件", command=select_file, width=20, height=2)
    select_file_button.pack(pady=10)

    play_audio_button = tk.Button(root, text="播放音频", command=play_audio, width=20, height=2)
    play_audio_button.pack(pady=10)

    global status_label
    status_label = tk.Label(root, text="", wraplength=580)
    status_label.pack(pady=10)

    result_frame = tk.Frame(root)
    result_frame.pack(pady=10, fill="both", expand=True)

    global result_text
    result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=8)
    result_text.pack(pady=10, fill="both", expand=True)

    translation_frame = tk.Frame(root)
    translation_frame.pack(pady=10, fill="both", expand=True)

    global translation_text
    translation_text = scrolledtext.ScrolledText(translation_frame, wrap=tk.WORD, height=8)
    translation_text.pack(pady=10, fill="both", expand=True)

    refresh_button = tk.Button(root, text="刷新", command=refresh_screen, width=10, height=1)
    refresh_button.place(x=570, y=10)

    root.mainloop()


if __name__ == '__main__':
    main()
