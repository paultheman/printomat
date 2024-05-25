import os

FILE_TYPES = ['jpg', 'jpeg', 'png', 'pdf', 'tiff', 'bmp']

DEBUG = True

INACTIVITY_LIMIT = 20 * 1000    # milliseconds
MAX_TRIES_TIMEOUT = 10          # seconds
MAX_TRIES = 10                  # maximum tries to enter a string
C_WIDTH = 500                   # preview tk.Canvas width
C_HEIGHT = 500                  # preview tk.Canvas height
W_WIDTH = 1024                  # window width
W_HEIGHT = 600                  # window height

RAND_SEQ_LENGTH = 7             # One Time Password length

ENTRY_RM_INTERVAL = 1800        # seconds, interval to delete old uploaded user entries
ENTRIES_FPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'tmp')
WEBSERVER_FPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'webserver')


