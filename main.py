import os

import subprocess

import pytesseract
import speech_recognition as sr

from PIL import Image
import requests
from bs4 import BeautifulSoup as b
import telebot
from telebot import types
import random
import easyocr
from pathlib import Path


URL1 = 'https://miuz.ru/search/?q='
URL2 = '&correct=Y&where=iblock_Catalog&s=+'
API_KEY = '5357377382:AAHJpCPm14Pl1W-VfBgSO2hOWBr-bjkKme0'
likeItem = ['Очистить список']


def parser(url):
    r = requests.get(url)
    soup = b(r.text, 'html.parser')
    item = soup.find_all('span', class_='product__price-val')
    return [c.text for c in item]


def delBut(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    unique_likeItem = list(set(likeItem))
    random.shuffle(unique_likeItem)
    for element in unique_likeItem:
        markup.add(types.KeyboardButton(element))
    bot.send_message(chat_id, 'Кнопки удалены', reply_markup=markup)
    return


def addBut(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    likeItem.append(message.text)
    unique_likeItem = list(set(likeItem))
    random.shuffle(unique_likeItem)
    for element in unique_likeItem:
        markup.add(types.KeyboardButton(element))
    return markup


def getTextFromImage(src):
    reader = easyocr.Reader(["ru", "en"])
    result = reader.readtext(src, detail=0, paragraph=True)
    return result


bot = telebot.TeleBot(API_KEY)


@bot.message_handler(commands=['Начать', 'Рестарт'])
def hello(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(message.chat.id, 'Привет! Введи имя товара:', reply_markup=markup)


@bot.message_handler(content_types=['photo'])
def handler_file(message):
    Path(f'files/{message.chat.id}/').mkdir(parents=True, exist_ok=True)
    file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    src = f'files/{message.chat.id}/' + file_info.file_path.replace('photos/', '')
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)
    text = getTextFromImage(src)
    bot.send_message(message.chat.id, "easyocr: " + str(text))
    img = Image.open(src)
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    custom_conf = r'--oem 3 --psm 6'
    result2 = pytesseract.image_to_string(img, lang='rus', config=custom_conf)
    bot.send_message(message.chat.id, "pytesseract: " + result2)
    os.remove(src)


@bot.message_handler(content_types=['voice'])
def get_audio_messages(message):
    r = sr.Recognizer()
    Path(f'files/{message.chat.id}/').mkdir(parents=True, exist_ok=True)
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    src = f'files/{message.chat.id}/' + file_info.file_path.replace('voice/', '')
    print(src)
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)

    src_filename = src
    dest_filename = str.replace(src, '.oga', 'output.wav')

    process = subprocess.run(['C:\\ffmpeg\\bin\\ffmpeg.exe', '-i', src_filename, dest_filename])
    if process.returncode != 0:
        raise Exception("Something went wrong")

    with sr.AudioFile(dest_filename) as source:
        user_audio = r.record(source)

    text = r.recognize_vosk(user_audio, language='ru-RU')
    bot.send_message(message.chat.id, text)
    os.remove(src_filename)
    os.remove(dest_filename)


bot.polling(none_stop=True, interval=0)
