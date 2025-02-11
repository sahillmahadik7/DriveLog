from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import os

app = Flask(__name__, template_folder='.')  # Set template folder to current directory

# Configure database (Use PostgreSQL in production, SQLite for local testing)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///travel_log.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define the database model
class TravelLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    start_km = db.Column(db.Float, nullable=False)
    end_km = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    km_covered = db.Column(db.Float, nullable=False)
    time_taken = db.Column(db.String(10), nullable=False)

# Create the database tables (Only runs once at startup)
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
    
    # Calculate KM covered
    km_covered = float(data['end_km']) - float(data['start_km'])
    
    # Calculate time taken
    start_time = datetime.strptime(data['start_time'], '%H:%M')
    end_time = datetime.strptime(data['end_time'], '%H:%M')
    time_taken = str(end_time - start_time)
    
    new_entry = TravelLog(
        date=data['date'],
        source=data['source'],
        destination=data['destination'],
        start_km=data['start_km'],
        end_km=data['end_km'],
        start_time=data['start_time'],
        end_time=data['end_time'],
        km_covered=km_covered,
        time_taken=time_taken
    )
    
    db.session.add(new_entry)
    db.session.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
