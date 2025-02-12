from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from datetime import datetime
import qrcode
from io import BytesIO
import base64

app = Flask(__name__, template_folder='.')

# Load Firebase credentials from environment variable
firebase_key_json = os.getenv('FIREBASE_KEY')  # Get the key from Render
if not firebase_key_json:
    raise ValueError("FIREBASE_KEY environment variable not set")

firebase_key = json.loads(firebase_key_json)  # Convert JSON string to dictionary
cred = credentials.Certificate(firebase_key)  # Use credentials from env variable
firebase_admin.initialize_app(cred)

db = firestore.client()
collection = db.collection('travel_log')  # Collection name in Firestore

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
    
    new_entry = {
        "date": data['date'],
        "source": data['source'],
        "destination": data['destination'],
        "start_km": float(data['start_km']),
        "end_km": float(data['end_km']),
        "km_covered": km_covered,
        "start_time": data['start_time'],
        "end_time": data['end_time'],
        "time_taken": time_taken
    }
    
    collection.add(new_entry)  # Add data to Firestore
    
    return jsonify({"success": True, "message": "Data saved successfully!"})

@app.route('/view_data')
def view_data():
    docs = collection.stream()  # Get all documents from the collection
    data = [doc.to_dict() for doc in docs]  # Convert documents to dictionaries
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
