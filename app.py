from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import os

app = Flask(__name__)

EXCEL_FILE = 'travel_log.xlsx'

# Create Excel file if it doesn't exist
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=[
        'Date', 'Source', 'Destination', 'Start_KM', 'End_KM',
        'Start_Time', 'End_Time', 'KM_Covered', 'Time_Taken'
    ])
    df.to_excel(EXCEL_FILE, index=False)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_qr')
def generate_qr():
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    form_url = request.host_url + 'form'
    qr.add_data(form_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    return render_template('qr.html', qr_code=img_str)

@app.route('/form')
def show_form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    
    # Calculate KM covered
    km_covered = float(data['end_km']) - float(data['start_km'])
    
    # Calculate time taken
    start_time = datetime.strptime(data['start_time'], '%H:%M')
    end_time = datetime.strptime(data['end_time'], '%H:%M')
    time_taken = str(end_time - start_time)
    
    new_row = {
        'Date': data['date'],
        'Source': data['source'],
        'Destination': data['destination'],
        'Start_KM': data['start_km'],
        'End_KM': data['end_km'],
        'Start_Time': data['start_time'],
        'End_Time': data['end_time'],
        'KM_Covered': km_covered,
        'Time_Taken': time_taken
    }
    
    df = pd.read_excel(EXCEL_FILE)
    df = df._append(new_row, ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
