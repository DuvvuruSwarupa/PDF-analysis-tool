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
    nltk.download('averaged_perceptron_tagger')
except Exception as e:
    print(f"Error downloading NLTK resources: {e}")

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'pdfFile' not in request.files:
            return jsonify({'message': 'No file part'}), 400

        file = request.files['pdfFile']
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400

        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Extract text from PDF
            text = extract_text_from_pdf(filepath)

            # Generate questions
            questions = generate_questions(text)

            # Store questions in MongoDB
            collection.insert_one({'filename': filename, 'questions': questions})

            return jsonify({'message': 'File successfully uploaded and questions stored to MongoDB successfully'}), 200

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
        correct_answer = extract_relevant_answer(sentence, sentences)
        options = [correct_answer]
        while len(options) < 4:  # Typically, multiple choice has 4 options
            random_sentence = random.choice(sentences)
            option_answer = extract_relevant_answer(random_sentence, sentences)
            if option_answer != correct_answer and option_answer not in options:
                options.append(option_answer)
        random.shuffle(options)
        questions['multiple_choice'].append({
            "question": sentence,
            "options": options,
            "answer": correct_answer
        })

    # Generate 5 true/false questions
    for _ in range(5):
        sentence = random.choice(sentences)
        true_false_statement = sentence
        correct_answer = extract_relevant_answer(sentence, sentences)
        true_false_answer = "True" if correct_answer in sentence else "False"
        questions['true_false'].append({
            "question": true_false_statement,
            "answer": true_false_answer
        })

    # Generate 2 short answer questions
    for _ in range(2):
        question, answer = generate_short_answer_question(sentences)
        questions['short_answer'].append({
            "question": question,
            "answer": answer
        })

    # Generate 2 essay questions
    for _ in range(2):
        question, answer = generate_essay_question(sentences)
        questions['essay'].append({
            "question": question,
            "answer": answer
        })

    return questions

def generate_short_answer_question(sentences):
    sentence = random.choice(sentences)
    words = nltk.word_tokenize(sentence)
    tagged_words = nltk.pos_tag(words)
    
    noun_phrases = [word for word, tag in tagged_words if tag in ('NN', 'NNS', 'NNP', 'NNPS')]
    
    if noun_phrases:
        question = f"What is {noun_phrases[0]}?"
        answer = extract_relevant_answer(sentence, sentences)
    else:
        question = f"Explain: {sentence}"
        answer = extract_relevant_answer(sentence, sentences)
    
    return question, answer

def generate_essay_question(sentences):
    sentence = random.choice(sentences)
    words = nltk.word_tokenize(sentence)
    tagged_words = nltk.pos_tag(words)
    
    verbs = [word for word, tag in tagged_words if tag.startswith('VB')]
    
    if verbs:
        question = f"Discuss the significance of {verbs[0]} in the context of {sentence}"
        answer = extract_relevant_answer(sentence, sentences)
    else:
        question = f"Discuss: {sentence}"
        answer = extract_relevant_answer(sentence, sentences)
    
    return question, answer

def extract_relevant_answer(question, sentences):
    question_words = set(nltk.word_tokenize(question.lower()))
    best_match = None
    best_overlap = 0

    for sentence in sentences:
        sentence_words = set(nltk.word_tokenize(sentence.lower()))
        overlap = len(question_words & sentence_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = sentence

    return best_match if best_match else "No relevant information found."

# Handle unknown routes
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'message': 'This route is not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)
