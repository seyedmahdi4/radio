import curses
import vlc
import sys
import threading
import time
import requests


name_ = f"9Craft Radio"
data = '"p" for play/pause UP & DOWN key for change volume and "Esc" for exit'
status = "Wait for select channel ..."
title = ""
vol = ""
keys = list("1234567890qwertyui")
is_playing = False
playing_now = -1

s = requests.Session()
instance = vlc.Instance("--quiet")


def load_data():
    global urls
    res = s.get("https://radio.9craft.ir/v1/api/genre/all").json()
    urls = res["data"]


def init_curses():
    stdscr = curses.initscr()
    curses.start_color()
    curses.init_pair(1, 44, curses.COLOR_BLACK)
    curses.init_pair(2, 223, curses.COLOR_BLACK)
    curses.init_pair(3, 227, curses.COLOR_BLACK)
    curses.init_pair(4, 47, curses.COLOR_BLACK)
    curses.init_pair(5, 45, curses.COLOR_BLACK)
    curses.init_pair(6, 206, curses.COLOR_BLACK)
    curses.init_pair(7, 195, curses.COLOR_BLACK)
    curses.init_pair(8, 242, curses.COLOR_BLACK)
    curses.init_pair(9, 221, curses.COLOR_BLACK)
    curses.init_pair(10, 226, curses.COLOR_BLACK)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    return stdscr


def end_curses(stdscr):
    stdscr.keypad(False)
    curses.nocbreak()
    curses.echo()
    curses.endwin()


def update_display(stdscr):
    global vol
    stdscr.clear()
    stdscr.addstr(0, 0, f"{name_}\n\n", curses.color_pair(4) | curses.A_BOLD)
    stdscr.addstr(f"Status: ", curses.color_pair(10))
    stdscr.addstr(f"{status}\n\n", curses.color_pair(9))

    if playing_now == -1:
        name = ""
        music = ""
    else:
        name = urls[playing_now]["server_name"]
        music = urls[playing_now]["title"]
        stdscr.addstr(f"Genre: ", curses.color_pair(2))
        stdscr.addstr(f"{name}\n", curses.color_pair(3))
        stdscr.addstr(f"Music: ", curses.color_pair(2))
        stdscr.addstr(f"{music}\n\n", curses.color_pair(3))

    for i, url in enumerate(urls, start=0):
        name__ = url["server_name"]
        title = url["title"]
        stdscr.addstr(f"{keys[i]}. ", curses.color_pair(1))
        stdscr.addstr(f"{name__}: ", curses.color_pair(5))
        stdscr.addstr(f"{title}\n", curses.color_pair(7))

    stdscr.addstr(f'\n{data}\n', curses.color_pair(8) | curses.A_ITALIC)

    if vol:
        stdscr.addstr("\nVolume: ", curses.color_pair(6))
        stdscr.addstr(f"{vol}%", curses.color_pair(6) | curses.A_ITALIC)
    stdscr.refresh()


def main(stdscr):
    global vol, playing_now, status, is_playing
    player = instance.media_player_new()

    while True:
        update_display(stdscr)
        key = stdscr.getch()
        if key == 27:
            break
        elif key == curses.KEY_UP:
            vol_ = player.audio_get_volume()
            new_vol = min(vol_ + 10, 100)
            player.audio_set_volume(new_vol)
            if player.audio_get_volume() != 100:
                vol = f"{player.audio_get_volume() + 10}"

        elif key == curses.KEY_DOWN:
            vol_ = player.audio_get_volume()
            new_vol = max(vol_ - 10, 0)
            player.audio_set_volume(new_vol)
            if player.audio_get_volume() != 0:
                vol = f"{player.audio_get_volume() - 10}"

        elif key == ord("p") and playing_now != -1:
            if is_playing:
                player.stop()
                status = "Pused"
                is_playing = False
            else:
                player.play()
                status = "Playing..."
                is_playing = True

        elif chr(key) in keys:
            ind = keys.index(chr(key))
            if ind < len(urls):
                media = instance.media_new(urls[ind]["http_server_url"])
                player.stop()
                player.set_media(media)
                player.play()
                playing_now = ind
                is_playing = True
            status = "Playing.."
        update_display(stdscr)


def loop(stdscr):
    global vol
    while 1:
        time.sleep(10)
        load_data()
        vol = ""
        update_display(stdscr)


if __name__ == "__main__":
    try:
        load_data()
        stdscr = init_curses()
        t = threading.Thread(target=loop, args=(stdscr,))
        t.daemon = True
        t.start()
        main(stdscr)
    except KeyboardInterrupt:
        end_curses(stdscr)
        sys.exit()
    except Exception as e:
        print("EROOR:", e)
