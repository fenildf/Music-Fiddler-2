"""
A simple plugin that fiddles with music volume to reinforce quick reviewing.

Before using:
- This plugin was made for Linux. It will require modification to work on another OS.
- Ensure that the "amixer" command works on your computer. If it doesn't, you're going to need to modify the code somehow. Don't ask me how.
- Change all lines (in the plugin source) marked with "CHANGEME" according to your preferences.
"""

from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
from anki.hooks import addHook
from random import randint, choice
from re import search
from subprocess import Popen, PIPE, call
from shlex import split as shlex_split
from time import sleep
STEPS = 35
MIN_SPEAKER = 55
MAX_SPEAKER = 85
MIN_HEADPHONES = 20
MAX_HEADPHONES = 40
CTR = 0

from threading import Thread


def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step


def get_number():
    global CTR
    CTR+=1
    if (CTR < 5):
        return initial_distrobution()
    elif CTR >= 5 and CTR < 10:
        return secondary_distrobution()
    elif CTR >= 10:
        return final_distrobution()


def final_distrobution():
    speaker_range = MAX_SPEAKER - MIN_SPEAKER
    headphone_range = MAX_HEADPHONES - MIN_HEADPHONES
    speaker_distro = [MAX_SPEAKER] * 2 + [speaker_range / 2 + MIN_SPEAKER] * 2 + [speaker_range / 3 + MIN_SPEAKER] * 3
    headphone_distro = [MAX_HEADPHONES] * 2 + [headphone_range / 2 + MIN_HEADPHONES] * 2 + [headphone_range / 3 +
                                                                                            MIN_HEADPHONES] * 3
    return choice(speaker_distro) if on_speaker else choice(headphone_distro)


def secondary_distrobution():
    if on_speaker:
        return choice([a for a in drange(MIN_SPEAKER, MAX_SPEAKER, float(MAX_SPEAKER - MIN_SPEAKER) / 3)])
    else:
        return choice([a for a in drange(MIN_HEADPHONES, MAX_HEADPHONES, float(MAX_HEADPHONES - MIN_HEADPHONES) / 3)])


def initial_distrobution():
    if on_speaker:
        return MAX_SPEAKER
    else:
        return MAX_HEADPHONES


def resetMusicTimer():
    "Boosts volume back up and starts the music timer."
    # CHANGEME: The next lines are a python dictionary associating deck names with times (in milliseconds) between volume-decrements.
    # Eg, when using the deck "brainscience", volume will decrement every 5 seconds. When using a deck without a listed name, "other" is used.
    # Change this according to your decks. Decks with shorter, easier cards need less time.
    deckMusicTimes = {
        "CS_373": 5000,
        "LinearAlgebra": 5000,
        "Joke": 1000,
        "other": 2000,
    }
    if mw.col.decks.current()['name'] in deckMusicTimes:
        mw.musicTimeToDecrement = deckMusicTimes[mw.col.decks.current()['name']]
    else:
        mw.musicTimeToDecrement = deckMusicTimes["other"]
    boostMusicVolume()
    mw.musicTimer = QTimer(mw)
    mw.musicTimer.setSingleShot(True)
    mw.musicTimer.start(mw.musicTimeToDecrement)
    mw.connect(mw.musicTimer, SIGNAL("timeout()"), decrementMusicVolume)
    # showInfo(mw.state)


def changeMusicVolume(change, steps=0):
    "Changes volume according to string; can be either absolute ('40') or change ('2%-')."
    if steps == 0:
        call(shlex_split("amixer set Master " + str(change)))  # CHANGEME somehow, if amixer doesn't work
    else:
        cur = get_state()
        interval = 1. / steps
        for a in drange(cur, int(change), float(int(change) - cur) / steps):
            call(shlex_split("amixer set Master " + str(a)))
            sleep(interval)


def boostMusicVolume():
    # showInfo("boosted") #To test changes, you can uncomment this line.
    Thread(target=changeMusicVolume, args=(get_number(), STEPS)).start()

    # if on_speaker:
    #     Thread(target=changeMusicVolume, args=(randint(MIN_SPEAKER, MAX_SPEAKER), STEPS)).start()
    # else:
    #     Thread(target=changeMusicVolume, args=(randint(MIN_HEADPHONES, MAX_HEADPHONES), STEPS)).start()


    # CHANGEME: Set to however high you want your volume to go each time it's boosted back.
    # Protip: your music-playing program might have its own "volume multiplier" that you can adjust easily.


def killMusicVolume():
    # showInfo("killed") #To test changes, you can uncomment this line.
    changeMusicVolume("10")
    # CHANGEME: Set to how low volume should go when it dies, eg due to undoing a card.


def decrementMusicVolume():
    "When reviewing, decrements volume, then sets a timer to call itself. When not reviewing, kills volume and stops timer."
    if mw.state == "review":
        # showInfo("music volume goes down") #To test changes, you can uncomment this line.
        changeMusicVolume(str(2) + "%-")  # CHANGEME if you prefer smaller or bigger volume jumps.
        mw.musicTimer.start(mw.musicTimeToDecrement)  # (start the timer again)
    else:
        killMusicVolume()
        mw.musicTimer = None  # (kill the timer if you're not reviewing)


def get_state():
    # exp = r".*?(\d+) \[(\d+)%\]"
    exp = r".*?(\d+) "
    cmd = shlex_split("amixer get Master")
    return int(search(exp, Popen(cmd, stdout=PIPE).stdout.readlines()[4]).groups()[0])


def on_speaker():
    cmd = shlex_split("amixer get Speaker")
    return search(r"\[(on)\]", Popen(cmd, stdout=PIPE).stdout.readlines()[5]).groups()[0] == 'on'


addHook("showQuestion", resetMusicTimer)
