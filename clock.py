import sys
import os
import platform
import signal
import datetime
import time
import json
import locale
import random
import requests
import logging

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QPixmap, QBrush, QColor
from PyQt4.QtGui import QPainter, QImage, QFont
from PyQt4.QtCore import Qt

from hyperpixel_backlight import Backlight

sys.dont_write_bytecode = True

_LOGGER = logging.getLogger(__name__)

try:
    import clock_settings
except ImportError:
    _LOGGER.error("ERROR: Config file not found. Copy 'clock_settings.py.example' to 'clock_settings.py' before you edit. You can do this with the command: cp clock_settings.py.example clock_settings.py")
    sys.exit(1)

def tick():
    global hourpixmap, minpixmap, secpixmap
    global hourpixmap2, minpixmap2, secpixmap2
    global lastmin, lastday, lasttimestr
    global clockrect
    global datex

    if Date_Locale != "":
        try:
            locale.setlocale(locale.LC_TIME, Date_Locale)
        except:
            pass

    now = datetime.datetime.now()
    angle = now.second * 6
    ts = secpixmap.size()
    secpixmap2 = secpixmap.transformed(
        QtGui.QMatrix().scale(
            float(clockrect.width()) / ts.height(),
            float(clockrect.height()) / ts.height()
        ).rotate(angle),
        Qt.SmoothTransformation
    )
    sechand.setPixmap(secpixmap2)
    ts = secpixmap2.size()
    sechand.setGeometry(
        clockrect.center().x() - ts.width() / 2,
        clockrect.center().y() - ts.height() / 2,
        ts.width(),
        ts.height()
    )
    if now.minute != lastmin:
        lastmin = now.minute
        angle = now.minute * 6
        ts = minpixmap.size()
        minpixmap2 = minpixmap.transformed(
            QtGui.QMatrix().scale(
                float(clockrect.width()) / ts.height(),
                float(clockrect.height()) / ts.height()
            ).rotate(angle),
            Qt.SmoothTransformation
        )
        minhand.setPixmap(minpixmap2)
        ts = minpixmap2.size()
        minhand.setGeometry(
            clockrect.center().x() - ts.width() / 2,
            clockrect.center().y() - ts.height() / 2,
            ts.width(),
            ts.height()
        )

        angle = ((now.hour % 12) + now.minute / 60.0) * 30.0
        ts = hourpixmap.size()
        hourpixmap2 = hourpixmap.transformed(
            QtGui.QMatrix().scale(
                float(clockrect.width()) / ts.height(),
                float(clockrect.height()) / ts.height()
            ).rotate(angle),
            Qt.SmoothTransformation
        )
        hourhand.setPixmap(hourpixmap2)
        ts = hourpixmap2.size()
        hourhand.setGeometry(
            clockrect.center().x() - ts.width() / 2,
            clockrect.center().y() - ts.height() / 2,
            ts.width(),
            ts.height()
        )

    if clock_settings.display_date :
       if now.day != lastday:
          lastday = now.day
        # date
          sup = 'th'
          if (now.day == 1 or now.day == 21 or now.day == 31):
              sup = 'st'
          if (now.day == 2 or now.day == 22):
              sup = 'nd'
          if (now.day == 3 or now.day == 23):
              sup = 'rd'
          if Date_Locale != "":
              sup = ""
          ds = "{0:%A %B} {0.day}<sup>{1}</sup> {0.year}".format(now, sup)
          datex.setText(ds)

def qtstart():
    global ctimer

    ctimer = QtCore.QTimer()
    ctimer.timeout.connect(tick)
    ctimer.start(1000)

def realquit():
    QtGui.QApplication.exit(0)

def myquit(a=0, b=0):
    global ctimer,mytimer, bl

    bl.cleanup()
    ctimer.stop()
    mytimer.stop()
    QtCore.QTimer.singleShot(30, realquit)

# define default values for new/optional config variables.

background = "/images/" + clock_settings.background
clock_face = "/images/clockface.png"
hour_hand = "/images/hourhand.png"
min_hand = "/images/minhand.png"
sec_hand = "/images/sechand.png"

text_color = '#bef'

# gives all text additional attributes using QT style notation
# example: font_attr = 'font-weight: bold; '
#font_attr = 'font: 24pt'

# The Python Locale for date/time (locale.setlocale)
#  '' for default Pi Setting
# Locales must be installed in your Pi.. to check what is installed
# locale -a
# to install locales
# sudo dpkg-reconfigure locales
Date_Locale = ''

CLOCK_OFF, CLOCK_ON = 0, 1

#display_date = 0

lastmin = -1
lastday = -1
pdy = ""
lasttimestr = ""

def clock_prep():
    global hourpixmap, minpixmap, secpixmap
    global hourpixmap2, minpixmap2, secpixmap2
    global lastmin, lastday, lasttimestr
    global clockrect
    global datex
    global w, app, desktop, rec,height, width
    global sechand, minhand, hourhand

    app = QtGui.QApplication(sys.argv)
    desktop = app.desktop()
    rec = desktop.screenGeometry()
    height = rec.height()
    width = rec.width()

    signal.signal(signal.SIGINT, myquit)

    w = QtGui.QWidget()
    w.setWindowTitle(os.path.basename(__file__))

    w.setStyleSheet("QWidget { background-color: black;}")

    #xscale = float(width) / 1440.0
    #yscale = float(height) / 900.0
    xscale = float(width) / 720.0
    yscale = float(height) / 720.0

    frames = []
    framep = 0

    frame1 = QtGui.QFrame(w)
    frame1.setObjectName("frame1")
    frame1.setGeometry(0, 0, width, height)
    frame1.setStyleSheet("#frame1 { background-color: black; border-image: url(" +
                         sys.path[0] + background + ") 0 0 0 0 stretch stretch;}")
    frames.append(frame1)

    if clock_settings.display_date :
       frame2 = QtGui.QFrame(w)
       frame2.setObjectName("frame2")
       frame2.setGeometry(0, 0, width, height)
       frame2.setStyleSheet("#frame2 { background-color: blue; border-image: url(" +
                            sys.path[0] + background + ") 0 0 0 0 stretch stretch;}")
       frame2.setVisible(False)
       frames.append(frame2)

    foreGround = QtGui.QFrame(frame1)
    foreGround.setObjectName("foreGround")
    foreGround.setStyleSheet("#foreGround { background-color: transparent; }")
    foreGround.setGeometry(0, 0, width, height)

    clockface = QtGui.QFrame(foreGround)
    clockface.setObjectName("clockface")
    clockrect = QtCore.QRect(
        width / 2 - height * .4,
#       height * .45 - height * .4,
        height * .45 - height * .4 + 36,
        height * .8,
        height * .8)
    clockface.setGeometry(clockrect)
    clockface.setStyleSheet(
        "#clockface { background-color: transparent; border-image: url(" +
        sys.path[0] + clock_face +
        ") 0 0 0 0 stretch stretch;}")

    hourhand = QtGui.QLabel(foreGround)
    hourhand.setObjectName("hourhand")
    hourhand.setStyleSheet("#hourhand { background-color: transparent; }")

    minhand = QtGui.QLabel(foreGround)
    minhand.setObjectName("minhand")
    minhand.setStyleSheet("#minhand { background-color: transparent; }")

    sechand = QtGui.QLabel(foreGround)
    sechand.setObjectName("sechand")
    sechand.setStyleSheet("#sechand { background-color: transparent; }")

    hourpixmap = QtGui.QPixmap(sys.path[0] + hour_hand)
    hourpixmap2 = QtGui.QPixmap(sys.path[0] + hour_hand)

    minpixmap = QtGui.QPixmap(sys.path[0] + min_hand)
    minpixmap2 = QtGui.QPixmap(sys.path[0] + min_hand)

    secpixmap = QtGui.QPixmap(sys.path[0] + sec_hand)
    secpixmap2 = QtGui.QPixmap(sys.path[0] + sec_hand)

    if clock_settings.display_date :
       datex = QtGui.QLabel(foreGround)
       datex.setObjectName("datex")
       datex.setStyleSheet("#datex { font-family:sans-serif; color: " +
                           text_color +
                           "; background-color: transparent; font-size: " +
                           str(int(50 * xscale)) +
                           "px; " +
                           clock_settings.font_attr +
                           "}")
       datex.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
#       datex.setGeometry(0, 0, width, 100)
       datex.setGeometry(0, 660, width, 100)

    stimer = QtCore.QTimer()
    stimer.singleShot(10, qtstart)
    
def check_msa_status() : 
    global mytimer, bl, secstogo, secstogo_loc,msa_url

    def turn_clock (w,onoff) :
        if onoff == CLOCK_ON :
            w.show()
            w.showFullScreen()
        else :
            w.hide()

    if secstogo_loc >= 0:
        if secstogo_loc :
            secstogo_loc -= 1
    else :
        secstogo = -1

    try:
        r = requests.get(msa_url)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    o=json.loads(r.text)
    for i in o: c = i
    playing_status = o[c]

    if playing_status in [ "STOPPED","PAUSED_PLAYBACK" ] :
        if secstogo_loc :
            if bl.power == False : bl.set_power(True)
            _LOGGER.debug("CLOCK_ON -> PLAYING STATUS: %s", playing_status)
            turn_clock (w,CLOCK_ON)
        else:
            if bl.power == True : bl.set_power(False)
            _LOGGER.debug("CLOCK_OFF -> PLAYING STATUS: %s",playing_status)
            turn_clock (w,CLOCK_OFF)
    elif playing_status == "PLAYING" :
        if bl.power == False : bl.set_power(True)
        _LOGGER.debug("CLOCK_OFF -> PLAYING STATUS: %s",playing_status)
        turn_clock (w,CLOCK_OFF)
        secstogo_loc = secstogo

    mytimer = QtCore.QTimer()
    mytimer.timeout.connect(check_msa_status)
    mytimer.start(1000)

def setup_logging():
    """Set up logging facilities for the script."""

    log_level = getattr(clock_settings, "log_level", logging.INFO)
    log_file = getattr(clock_settings, "log_file", None)
    if log_file:
        log_path = os.path.expanduser(log_file)
    else:
        log_path = None

    fmt = "%(asctime)s %(levelname)7s - %(message)s"
    logging.basicConfig(format=fmt, level=log_level)

    # Suppress overly verbose logs from libraries that aren't helpful
#    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
#    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

    if log_path is None:
        return

    log_path_exists = os.path.isfile(log_path)
    log_dir = os.path.dirname(log_path)

    if (log_path_exists and os.access(log_path, os.W_OK)) or (
        not log_path_exists and os.access(log_dir, os.W_OK)
    ):
        _LOGGER.info("Writing to log file: %s", log_path)
        logfile_handler = logging.FileHandler(log_path, mode="a")

        logfile_handler.setLevel(log_level)
        logfile_handler.setFormatter(logging.Formatter(fmt))

        logger = logging.getLogger("")
        logger.addHandler(logfile_handler)
    else:
        _LOGGER.error("Cannot write to %s, check permissions and ensure directory exists", log_path)

def main() :
    global bl,old_playing_status,secstogo,secstogo_loc,on_duty,msa_url
    old_playing_status = "NoNe"

    msa_url = "http://" + clock_settings.msa_address + ":" + clock_settings.msa_port + "/status"

    setup_logging()

    _LOGGER.debug("msa_url: %s", msa_url)
    _LOGGER.debug("clock_timeout: %s", clock_settings.clock_timeout)

    secstogo = clock_settings.clock_timeout
    secstogo_loc = secstogo

    bl = Backlight()

    clock_prep()
    check_msa_status()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

