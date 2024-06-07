import curses
import vlc
import sys
import threading
import time
import requests

# Constants
APP_NAME = "9Craft Radio"
INSTRUCTIONS = 'space or "P" for play/pause UP & DOWN key for change volume and "Esc" for exit'
INITIAL_STATUS = "Wait for select channel ..."
KEYS = list("1234567890qwertyuiop")

# Global variables
session = requests.Session()
instance = vlc.Instance("--quiet")
urls = []
is_playing = False
playing_now = -1
volume = ""


def load_data():
    """Fetches the radio channel data from the API."""
    global urls
    response = session.get("https://radio.9craft.ir/v1/api/genre/all").json()
    urls = response["data"]


def init_curses():
    """Initializes the curses window."""
    stdscr = curses.initscr()
    curses.start_color()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)

    curses.init_pair(1, 44, curses.COLOR_BLACK)
    curses.init_pair(2, 181, curses.COLOR_BLACK)
    curses.init_pair(3, 223, curses.COLOR_BLACK)
    curses.init_pair(4, 47, curses.COLOR_BLACK)
    curses.init_pair(5, 45, curses.COLOR_BLACK)
    curses.init_pair(6, 206, curses.COLOR_BLACK)
    curses.init_pair(7, 195, curses.COLOR_BLACK)
    curses.init_pair(8, 242, curses.COLOR_BLACK)
    curses.init_pair(9, 171, curses.COLOR_BLACK)
    curses.init_pair(10, 111, curses.COLOR_BLACK)

    return stdscr


def end_curses(stdscr):
    """Restores the terminal to its original state."""
    stdscr.keypad(False)
    curses.nocbreak()
    curses.echo()
    curses.endwin()


def update_display(stdscr, status, volume):
    """Updates the curses window display with the latest information."""
    stdscr.clear()
    stdscr.addstr(0, 0, f"{APP_NAME}\n\n", curses.color_pair(4) | curses.A_BOLD)
    stdscr.addstr("Status: ", curses.color_pair(10))
    stdscr.addstr(f"{status}\n\n", curses.color_pair(9))

    if playing_now == -1:
        genre_name = ""
        music_title = ""
    else:
        genre_name = urls[playing_now]["server_name"]
        music_title = urls[playing_now]["title"]
        stdscr.addstr("Genre: ", curses.color_pair(2))
        stdscr.addstr(f"{genre_name}\n", curses.color_pair(3))
        stdscr.addstr("Music: ", curses.color_pair(2))
        stdscr.addstr(f"{music_title}\n\n", curses.color_pair(3))

    for i, url in enumerate(urls):
        server_name = url["server_name"]
        title = url["title"]
        if i == playing_now:
            stdscr.addstr(f"{KEYS[i]}. ", curses.color_pair(4))
            stdscr.addstr(f"{server_name}: ", curses.color_pair(4))
        else:
            stdscr.addstr(f"{KEYS[i]}. ", curses.color_pair(1))
            stdscr.addstr(f"{server_name}: ", curses.color_pair(5))
        stdscr.addstr(f"{title}\n", curses.color_pair(7))

    stdscr.addstr(f'\n{INSTRUCTIONS}\n', curses.color_pair(8) | curses.A_ITALIC)

    if volume:
        stdscr.addstr("\nVolume: ", curses.color_pair(6))
        stdscr.addstr(f"{volume}%", curses.color_pair(6) | curses.A_ITALIC)
    stdscr.refresh()


def handle_volume_change(player, change):
    """Handles volume change based on user input."""
    current_volume = player.audio_get_volume()
    new_volume = max(0, min(100, current_volume + change))
    player.audio_set_volume(new_volume)
    return f"{new_volume}%"


def main(stdscr):
    """Main function to handle user input and control the player."""
    global volume, playing_now, is_playing
    status = INITIAL_STATUS
    player = instance.media_player_new()

    while True:
        update_display(stdscr, status, volume)
        key = stdscr.getch()
        if key == 27:  # Escape key
            break
        elif key == curses.KEY_UP:
            volume = handle_volume_change(player, 5)
        elif key == curses.KEY_DOWN:
            volume = handle_volume_change(player, -5)
        elif key in (ord("p"), ord("P"), ord(" ")):
            if playing_now != -1:
                if is_playing:
                    player.stop()
                    status = "Paused"
                else:
                    player.play()
                    status = "Playing..."
                is_playing = not is_playing
        elif chr(key) in KEYS:
            index = KEYS.index(chr(key))
            if index < len(urls):
                media = instance.media_new(urls[index]["http_server_url"])
                player.stop()
                player.set_media(media)
                player.play()
                playing_now = index
                is_playing = True
                status = "Playing..."

        update_display(stdscr, status, volume)


def refresh_data(stdscr):
    """Periodically refreshes the radio channel data."""
    while True:
        time.sleep(10)
        load_data()
        update_display(stdscr, INITIAL_STATUS, volume)


if __name__ == "__main__":
    try:
        load_data()
        stdscr = init_curses()
        refresh_thread = threading.Thread(target=refresh_data, args=(stdscr,))
        refresh_thread.daemon = True
        refresh_thread.start()
        try:
            main(stdscr)
        finally:
            end_curses(stdscr)
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        end_curses(stdscr)
        print("ERROR:", e)
        sys.exit(1)
