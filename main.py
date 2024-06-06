import os
import warnings
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import PyPDF2
from pymongo import MongoClient
import nltk
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Suppress specific warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure MongoDB
try:
    client = MongoClient('mongodb+srv://testdb:testdb@cluster0.ovrarc4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['exam_database']
    collection = db['exam_questions']
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Download NLTK resources
try:
    nltk.download('punkt')
except Exception as e:
    print(f"Error downloading NLTK resources: {e}")

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("Received a request")
        if 'pdfFile' not in request.files:
            return jsonify({'message': 'No file part'}), 400

        file = request.files['pdfFile']
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400

        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            print(f"File {filename} saved successfully.")

            # Extract text from PDF
            text = extract_text_from_pdf(filepath)
            print("Extracted text from PDF")

            # Generate questions
            questions = generate_questions(text)
            print("Generated questions")

            # Store questions in MongoDB
            collection.insert_one({'filename': filename, 'questions': questions})
            print("Stored questions in MongoDB")

            # Generate PDF
            pdf_data = generate_pdf(questions)
            pdf_filename = f"{filename}_questions.pdf"

            return send_file(pdf_data, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')

        return jsonify({'message': 'Invalid file format'}), 400
    except Exception as e:
        print(f"Error processing the upload: {e}")
        return jsonify({'message': 'Internal server error'}), 500

def extract_text_from_pdf(filepath):
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def generate_questions(text):
    sentences = nltk.sent_tokenize(text)
    questions = {
        "multiple_choice": [],
        "true_false": [],
        "short_answer": [],
        "essay": []
    }

    # Generate 5 multiple choice questions
    for _ in range(5):
        sentence = random.choice(sentences)
        correct_answer = sentence
        options = [correct_answer]
        while len(options) < 4:  # Typically, multiple choice has 4 options
            random_sentence = random.choice(sentences)
            if random_sentence != correct_answer and random_sentence not in options:
                options.append(random_sentence)
        random.shuffle(options)
        questions['multiple_choice'].append({
            "question": correct_answer,
            "options": options,
            "answer": correct_answer
        })

    # Generate 5 true/false questions
    for _ in range(5):
        sentence = random.choice(sentences)
        true_false_statement = sentence
        true_false_answer = "True" if random.choice([True, False]) else "False"
        questions['true_false'].append({
            "question": true_false_statement,
            "answer": true_false_answer
        })

    # Generate 2 short answer questions
    for _ in range(2):
        sentence = random.choice(sentences)
        question_text = "What does the following statement mean: " + sentence
        questions['short_answer'].append({
            "question": question_text,
            "answer": sentence
        })

    # Generate 2 essay questions
    for _ in range(2):
        sentence = random.choice(sentences)
        if not sentence.endswith("?"):
            sentence += "?"
        questions['essay'].append({
            "question": sentence,
            "answer": "Detailed answer required."
        })

    return questions

def generate_pdf(questions):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica", 12)
    y = height - 40

    p.drawString(30, y, "Generated Questions and Answers")
    y -= 20

    for category, qs in questions.items():
        p.drawString(30, y, f"{category.capitalize().replace('_', ' ')} Questions:")
        y -= 20
        for q in qs:
            p.drawString(50, y, f"Question: {q['question']}")
            y -= 15
            if category == "multiple_choice":
                for option in q['options']:
                    p.drawString(70, y, f"Option: {option}")
                    y -= 15
                p.drawString(70, y, f"Answer: {q['answer']}")
                y -= 15
            else:
                p.drawString(70, y, f"Answer: {q['answer']}")
                y -= 20
            if y < 40:
                p.showPage()
                p.setFont("Helvetica", 12)
                y = height - 40

    p.save()
    buffer.seek(0)
    return buffer

# Handle unknown routes
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'message': 'This route is not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)
