#!/usr/bin/python

from pytube import YouTube
from pytube.contrib.playlist import Playlist
import pytube
import sqlite3
import telebot
import json
import os

# getting bot token and psw
with open('credentials.json') as json_file:
    credentials = json.load(json_file)

BOT_TOKEN = credentials["BOT_TOKEN"]
authorization_psw = credentials["authorization_psw"]

# connect to db
db = sqlite3.connect('db/db.users', check_same_thread=False)

# connect to bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="markdown")


def add_to_base(username, userid):
    cur = db.cursor()
    cur.execute(
        f"INSERT INTO youtube VALUES ('{userid}','{username}','general')")
    db.commit()


def check_base_user(userid):
    cur = db.cursor()
    cur.execute(f"SELECT rowid FROM youtube WHERE id = ?", (userid,))
    data = cur.fetchall()
    if len(data) == 0:
        return False
    else:
        return True


def get_user_folder(userid):
    cur = db.cursor()
    cur.execute(f"SELECT folder FROM youtube WHERE id = ?", (userid,))
    data = cur.fetchall()
    if len(data) == 0:
        return "general"
    else:
        return data[0][0]


def set_folder(folder, id):
    cur = db.cursor()
    cur.execute(f"UPDATE youtube SET folder = '{folder}' WHERE id = '{id}'")
    db.commit()


def update_stats(id, username, title, size):
    cur = db.cursor()
    cur.execute(
        f"INSERT INTO stats VALUES ('{id}','{username}','{title}','{size}')")
    db.commit()


@bot.message_handler(['set_folder'])
def set_folder_bot(message):
    if not check_base_user(message.from_user.id):
        bot.reply_to(message, f"You not authorized")
        return
    try:
        folder = message.text.split(" ")[1]
    except IndexError:
        bot.reply_to(
            message, f"Incorect usage. \n */set_folder [folder_name]* - change saving folder")
        return
    id = message.from_user.id
    set_folder(folder, id)
    bot.reply_to(message, f"Base folder changed to *{folder}*")


@bot.message_handler(['info'])
def info(message):
    commands = "*/info* - display posible commands \n */start [psw]* - authorization \n */get [video_url]* - download video \n */get_playlist [playlist_url]* - download whole playlist \n */set_folder [folder_name]* - change saving folder"
    bot.reply_to(message, f"Commands: \n {commands}")


@bot.message_handler(['start'])
def authorization(message):
    bot.reply_to(message, f"How to use - /info")
    if check_base_user(message.from_user.id):
        bot.reply_to(message, f"You have already authorized")
        return

    try:
        inserted_psw = message.text.split(" ")[1]
    except IndexError:
        bot.reply_to(message, f"Incorrect psw, */start [psw]* - authorization")
        return
    if inserted_psw == authorization_psw:
        add_to_base(message.from_user.username, message.from_user.id)
        bot.reply_to(message, f"Authorization passed")
    else:
        bot.reply_to(message, f"Incorrect psw")


@bot.message_handler(['get'])
def get_video_bot(message):
    if not check_base_user(message.from_user.id):
        bot.reply_to(message, f"You are not logged in")
        return
    try:
        url = message.text.split(" ")[1]
    except IndexError:
        bot.reply_to(
            message, f"Incorrect url, */get [video_url]* - download video")
        return
    try:
        video = YouTube(url)
    except pytube.exceptions.RegexMatchError:
        bot.reply_to(message, f"Incorrect url: {url}")
        return
    get_video(video, message)


@bot.message_handler(['get_playlist'])
def get_playlist_bot(message):
    if not check_base_user(message.from_user.id):
        bot.reply_to(message, f"You are not logged in")
        return
    try:
        url = message.text.split(" ")[1]
    except IndexError:
        bot.reply_to(
            message, f"Incorrect url, */get_playlist [playlist_url]* - download whole playlist")
        return

    try:
        playlist = Playlist(url)
    except KeyError:
        bot.reply_to(message, f"Incorrect url: {url}")
        return

    try:
        len(playlist.videos)
    except KeyError:
        bot.reply_to(message, f"Incorrect playlist: {url}")
        return

    bot.reply_to(message, f"Loading playlist: *{playlist.title}*")
    for video in playlist.videos:
        get_video(video, message, additional_folder=playlist.title)
    bot.reply_to(message, f"Done with playlist: *{playlist.title}*")


def get_video(video, message, additional_folder=""):
    folder = get_user_folder(message.from_user.id)
    if additional_folder:
        path = os.path.join("videos", folder, additional_folder)
    else:
        path = os.path.join("videos", folder)
    os.makedirs(path, exist_ok=True)
    bot.reply_to(message, f"Loading video: *{video.title}*")
    print(f"Loading video: *{video.title}*")
    video.streams.filter(progressive=True, file_extension='mp4').order_by(
        'resolution').desc().first().download(path)
    bot.reply_to(message, f"Done with *{video.title}*")
    print(f"Done with *{video.title}*")
    update_stats(message.from_user.id,
                 message.from_user.username,
                 video.title,
                 video.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().filesize_approx)


bot.infinity_polling()


# create new bot instance
