import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///phonebook.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)

DATA_FILE = 'phonebook_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        for contact in data:
            existing = Contact.query.filter_by(name=contact['name']).first()
            if not existing:
                new_contact = Contact(name=contact['name'], phone=contact['phone'])
                db.session.add(new_contact)
        db.session.commit()

def save_data():
    contacts = Contact.query.all()
    data = [{'name': c.name, 'phone': c.phone} for c in contacts]
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contacts')
def get_contacts():
    contacts = Contact.query.all()
    return jsonify([{'id': c.id, 'name': c.name, 'phone': c.phone} for c in contacts])

@app.route('/add_contact', methods=['POST'])
def add_contact():
    name = request.form.get('name')
    phone = request.form.get('phone')
    if not name or not phone:
        return jsonify({'error': '名前と電話番号を入力してください'}), 400
    existing = Contact.query.filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'この名前は既に登録されています'}), 400
    new_contact = Contact(name=name, phone=phone)
    db.session.add(new_contact)
    db.session.commit()
    save_data()
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('query', '')
    contacts = Contact.query.filter(Contact.name.contains(query) | Contact.phone.contains(query)).all()
    return jsonify([{'name': c.name, 'phone': c.phone} for c in contacts])

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    save_data()
    return '', 204

@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        load_data()
    print("Database initialized and data loaded.")

if __name__ == '__main__':
    app.run(debug=True)