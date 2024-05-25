import os
import string
from datetime import datetime, time
import qrcode
from logger import logger
import shutil
from constants import *
from PIL import Image
import threading


class Entry:
    counter = 0

    def __init__(self):
        self.length = RAND_SEQ_LENGTH
        self.generate_random_no_str(RAND_SEQ_LENGTH)

        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.entry_path = os.path.join(ENTRIES_FPATH, self.genStr)
        self._qr = self.createQR()
        Entry.counter += 1
        logger.info("Created new Entry -> %s RandomSeq -> '%s'" % (Entry.counter, self.genStr))

    def generate_random_string(self, length: int) -> str:
        self._genStr = ''.join([string.ascii_uppercase[int.from_bytes(os.urandom(1), byteorder='big') 
                                         % len(string.ascii_uppercase)] for _ in range(length)])
        return self._genStr
    
    def generate_random_no_str(self, length: int) -> str:
        self._genStr = ''.join([(string.ascii_uppercase+string.digits)[int.from_bytes(os.urandom(1), byteorder='big') 
                                         % len(string.ascii_uppercase + string.digits)] for _ in range(length)])
        return self._genStr
    
    @property
    def genStr(self) -> str:
        return self._genStr
    
    @property
    def qr(self) -> Image:
        return self._qr

    def createQR(self) -> Image:
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=3
            )        
        qr.add_data(self.genStr)
        qr.make(fit=True)
        if not os.path.exists(self.entry_path):
            os.makedirs(self.entry_path)
        # returns <class 'qrcode.image.pil.PilImage'>
        return qr.make_image(fill_color="black", back_color="white")


class Cleaner():
    def clean_old_entries(self, interval: int) -> None:
        
        current_Unix_time:float = datetime.timestamp(datetime.now())

        for folder_name in os.listdir(ENTRIES_FPATH):
            if DEBUG is True and folder_name == "TEST1NG":
                continue
            entry_path = os.path.join(ENTRIES_FPATH, folder_name)
            creation_time = os.stat(entry_path).st_ctime
            
            if current_Unix_time - creation_time > interval:
                log_str = f"Removing '{folder_name}' ... "
                try:
                    shutil.rmtree(entry_path)
                    log_str += ('Done')
                except Exception as e:
                    log_str += f'Error: {repr(e)}'
    
                logger.info(log_str)


def remove_entries():
    Cleaner().clean_old_entries(ENTRY_RM_INTERVAL)
    cleaner_thread = threading.Timer(ENTRY_RM_INTERVAL, remove_entries)
    cleaner_thread.daemon = True
    cleaner_thread.start()

remove_entries()