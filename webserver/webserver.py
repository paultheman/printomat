import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'src'))
from constants import *
from rand import Entry

from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import base64
import io

app = Flask(__name__)

app.config['DEBUG'] = True if DEBUG is True else False
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

@app.route('/')
def index():
    return render_template('index.html', file_types=FILE_TYPES)

@app.route('/upload', methods = ['POST'])
def upload():
    uploaded_files = request.files.getlist('files')
    valid_files_index = []

    for index, each in enumerate(uploaded_files):
        if each.filename == '':
            return redirect('/')
        if any(each.filename.endswith('.' + ext) for ext in FILE_TYPES):
            valid_files_index.append(index)

    if valid_files_index:
        entry = Entry()
        qr = entry.qr
        genStr = entry.genStr
        buf = io.BytesIO()
        qr.save(buf, format='PNG')
        # buf.seek(0)
        qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        for each in valid_files_index:
            uploaded_files[each].save(
                os.path.join(ENTRIES_FPATH, genStr, secure_filename(
                    uploaded_files[each].filename)))
        
        return render_template('upload.html', qr_base64=qr_base64, genStr=genStr)
    else:
        return 'No valid files found'

    
@app.errorhandler(413)
def request_entity_too_large(error):
    return f'Maximum upload size is 25 MB', 413


app.run(port=8080, host='0.0.0.0')