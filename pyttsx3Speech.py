import pyttsx3

engine = pyttsx3.init()


def text_to_speech(text):
    try:
        # 播放文本
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error in text-to-speech: {e}")


def pyttsx3_init():
    # 设置语速（可选）
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)

    voices = engine.getProperty('voices')
    for voice in voices:
        print("ID:", voice.id, "Name:", voice.name, "Lang:", voice.languages)
    # 设置语音引擎（可选，具体可用的引擎可以查看pyttsx3文档）
    # engine.setProperty('voice', voices[0].id)
