# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pre_processing import get_pdf_text, get_text_chunks, summarize_data, user_input, fetch_org_info_from_genai
import os
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.memory import ConversationBufferMemory
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_community.llms import HuggingFaceHub
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_mail import Mail, Message
import random
from db import employees


app = Flask(__name__)
app.secret_key = 'aa8104f270d2ba3bcf463e1e5a10ae64'  # Change this to a secure key


app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'

mail = Mail(app)

def generate_otp():
    return random.randint(100000, 999999)

def send_otp_email(recipient_email, otp_code):
    msg = Message('Your OTP Code',
                  sender=os.getenv('MAIL_USERNAME'),  
                  recipients=[recipient_email])
    msg.body = f'Your OTP code is: {otp_code}'
    mail.send(msg)


# Home route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in employees and employees[username]['password'] == password:
            session['username'] = username
            session['otp'] = generate_otp()
            send_otp_email(employees[username]['email'], session['otp'])
            return redirect(url_for('verify_otp')) 
        else:
            flash('Invalid credentials')
    return render_template('login.html')



@app.route('/verify', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == str(session['otp']):
            return redirect(url_for('index'))
        else:
            flash('Invalid OTP')
    return render_template('verify.html')


@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['pdf_file']
    
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Invalid file type. Only PDFs are allowed.'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)

        try:
            raw_text = get_pdf_text(filepath)
            text_chunks = get_text_chunks(raw_text)

            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            new_db = FAISS.from_texts(text_chunks, embeddings)
            
            new_db.save_local("faiss_index")
        except Exception as e:
            return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500
        finally:
            os.remove(filepath)

        return jsonify({'message': 'PDF processed successfully'}), 200

@app.route('/summarize_pdf', methods=['POST'])
def summarize_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['pdf_file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)

        summary = summarize_data(filepath)
        
        os.remove(filepath)
        
        return jsonify({'summary': summary}), 200


@app.route('/ask_question', methods=['POST'])
def ask_question():
    data = request.get_json()
    user_question = data.get('question', '')
    if user_question:
        try:
            response = user_input(user_question)
            return jsonify({'response': response}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'No question provided'}), 400


@app.route('/fetch_org_info', methods=['POST'])
def fetch_org_info():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['pdf_file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)

        org_info = fetch_org_info_from_genai(filepath)
        
        os.remove(filepath)
        
        return jsonify({'orgInfo': org_info}), 200


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('otp', None)
    return redirect(url_for('login'))



if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
