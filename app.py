import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
from io import BytesIO
import base64
from dotenv import load_dotenv

# Load environment variables from .env (only for local development)
load_dotenv()

app = Flask(__name__, template_folder='.')

# Use DATABASE_URL from environment variables (Render provides this automatically)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)

# Define Database Model
class TravelLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    source = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255), nullable=False)
    start_km = db.Column(db.Float, nullable=False)
    end_km = db.Column(db.Float, nullable=False)
    km_covered = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    time_taken = db.Column(db.String(20), nullable=False)

# Create tables if they don’t exist
with app.app_context():
    db.create_all()

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

    km_covered = float(data['end_km']) - float(data['start_km'])
    
    start_time = datetime.strptime(data['start_time'], '%H:%M')
    end_time = datetime.strptime(data['end_time'], '%H:%M')
    time_taken = str(end_time - start_time)

    new_entry = TravelLog(
        date=data['date'],
        source=data['source'],
        destination=data['destination'],
        start_km=float(data['start_km']),
        end_km=float(data['end_km']),
        km_covered=km_covered,
        start_time=data['start_time'],
        end_time=data['end_time'],
        time_taken=time_taken
    )
    
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"success": True, "message": "Data saved successfully!"})

@app.route('/view_data')
def view_data():
    entries = TravelLog.query.all()
    data = [
        {
            "date": entry.date,
            "source": entry.source,
            "destination": entry.destination,
            "start_km": entry.start_km,
            "end_km": entry.end_km,
            "km_covered": entry.km_covered,
            "start_time": entry.start_time,
            "end_time": entry.end_time,
            "time_taken": entry.time_taken
        } for entry in entries
    ]
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
