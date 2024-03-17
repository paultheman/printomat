import os
import string
from datetime import datetime, time
import qrcode
from logger import logger
import shutil

RAND_SEQ_LENGTH = 7
COLLECTION = set()
ENTRIES_FPATH = os.path.join('..', 'tmp')
ENTRY_RM_INTERVAL = 18000

class Entry:
    counter = 0

    def __init__(self):
        self.length = RAND_SEQ_LENGTH
        self.generate_random_no_str(RAND_SEQ_LENGTH)

        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.entry_path = os.path.join(ENTRIES_FPATH, self.genStr)
        self.createQR()
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

    def createQR(self) -> None:
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=5
            )        
        qr.add_data(self.genStr)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_name = self.genStr + '_' + self.timestamp +'.png'
        if not os.path.exists(self.entry_path):
            os.makedirs(self.entry_path)
        img_path = os.path.join(self.entry_path, img_name)
        img.save(img_path)
        COLLECTION.add(self.genStr)

class Cleaner():
    def clean_old_entries(self, current_Unix_time: float, interval: int) -> set:
        removed_entries = set()

        for folder_name in os.listdir(ENTRIES_FPATH):
            entry_path = os.path.join(ENTRIES_FPATH, folder_name)
            creation_time = os.stat(entry_path).st_ctime

            if current_Unix_time - creation_time > interval:
                log_str = f"Removing '{folder_name}' ... "
                try:
                    shutil.rmtree(entry_path)
                    log_str += ('Done')
                    removed_entries.add(folder_name)
                except Exception as e:
                    log_str += f'Error: {repr(e)}'
    
                logger.info(log_str)
        return removed_entries

# removed_entries = Cleaner().clean_old_entries(datetime.timestamp(datetime.now()), ENTRY_RM_INTERVAL)

if __name__ == "__main__":
    for _ in range(3):
        Entry()