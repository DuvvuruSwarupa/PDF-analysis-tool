import os
import warnings
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import PyPDF2
from pymongo import MongoClient
import nltk
import random

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

            return jsonify({'message': 'File successfully uploaded and questions stored to MongoDB successfully', 'questions': questions}), 200

        return jsonify({'message': 'Invalid file format'}), 400
    except Exception as e:
        print(f"Error processing the upload: {e}")
        return jsonify({'message': 'Internal server error'}), 500


def extract_text_from_pdf(filepath):
    try:
        from PyPDF2 import PdfReader

        with open(filepath, 'rb') as file:
            reader = PdfReader(file)
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

    # Print all categorized questions
    print("Categorized Questions:")
    for category, qs in questions.items():
        print(f"{category.capitalize()} Questions:")
        for q in qs:
            print(f"  - {q}")
    return questions

# Handle unknown routes
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'message': 'This route is not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change the port number if needed
