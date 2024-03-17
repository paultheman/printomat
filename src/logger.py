import logging, logging.handlers
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
folder_path = os.path.join('..', 'log')
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
#file_handler = logging.handlers.RotatingFileHandler(filename=(os.path.join(folder_path, datetime.now().strftime("%Y%m%d") + '.log')), 
#                                                    mode='a', maxBytes=20971520)
file_handler = logging.handlers.TimedRotatingFileHandler(filename=(os.path.join(folder_path, 'runtime.log')), 
                                                            when='midnight', interval=1, backupCount=2, delay='True')

formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)