import os
import warnings
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
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
    db = client['exam_database1']
    collection = db['exam_questions1']
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Download NLTK resources
try:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')
    nltk.download('stopwords')
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
            if not text.strip():
                return jsonify({'message': 'Failed to extract text from the PDF'}), 400

            print("Extracted text from PDF")

            # Generate questions
            questions = generate_questions(text)
            print("Generated questions")

            # Store questions in MongoDB
            collection.insert_one({'filename': filename, 'questions': questions})
            print("Stored questions in MongoDB")

            return jsonify({'message': 'File successfully uploaded and questions stored to MongoDB successfully'}), 200

        return jsonify({'message': 'Invalid file format'}), 400
    except Exception as e:
        print(f"Error processing the upload: {e}")
        return jsonify({'message': 'Internal server error'}), 500

def extract_text_from_pdf(filepath):
    try:
        with open(filepath, 'rb') as file:
            reader = PdfReader(file)
            text = ''
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def generate_questions(text):
    sentences = nltk.sent_tokenize(text)
    if not sentences:
        raise ValueError("No sentences found in the extracted text.")
    
    questions = {
        "multiple_choice": [],
        "true_false": [],
        "short_answer": [],
        "essay": []
    }

    key_phrases = extract_key_phrases(sentences)

    # Generate multiple choice questions
    while len(questions['multiple_choice']) < 5 and key_phrases:
        key_phrase = key_phrases.pop()
        question, options, answer = create_multiple_choice_question(key_phrase, sentences)
        if question:
            questions['multiple_choice'].append({
                "question": question,
                "options": options,
                "answer": answer
            })

    # Generate true/false questions
    while len(questions['true_false']) < 5 and key_phrases:
        key_phrase = key_phrases.pop()
        question, answer = create_true_false_question(key_phrase, sentences)
        if question:
            questions['true_false'].append({
                "question": question,
                "answer": answer
            })

    # Generate short answer questions
    while len(questions['short_answer']) < 5 and key_phrases:
        key_phrase = key_phrases.pop()
        question, answer = create_short_answer_question(key_phrase, sentences)
        if question:
            questions['short_answer'].append({
                "question": question,
                "answer": answer
            })

    # Generate essay questions
    while len(questions['essay']) < 5 and key_phrases:
        key_phrase = key_phrases.pop()
        question, answer = create_essay_question(key_phrase, sentences)
        if question:
            questions['essay'].append({
                "question": question,
                "answer": answer
            })

    # Print all categorized questions
    print("Categorized Questions:")
    for category, qs in questions.items():
        print(f"{category.capitalize()} Questions:")
        for q in qs:
            print(f"  - {q}")
    return questions

def extract_key_phrases(sentences):
    # Use more sophisticated key phrase extraction
    key_phrases = []
    for sentence in sentences:
        words = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(words)
        for i in range(len(tagged)):
            if tagged[i][1] in ['NN', 'NNS', 'NNP', 'NNPS']:  # Noun or proper noun
                key_phrases.append(tagged[i][0])
    # Remove duplicates and return
    return list(set(key_phrases))

def create_multiple_choice_question(key_phrase, sentences):
    relevant_sentences = [sentence for sentence in sentences if key_phrase in sentence]
    if not relevant_sentences:
        return None, None, None  # No question can be generated without relevant sentences

    correct_answer = random.choice(relevant_sentences)
    question = f"What is the significance of {key_phrase}?"

    options = [correct_answer]
    while len(options) < 4:
        random_sentence = random.choice(sentences)
        if random_sentence != correct_answer and random_sentence not in options:
            options.append(random_sentence)
    random.shuffle(options)

    return question, options, correct_answer

def create_true_false_question(key_phrase, sentences):
    relevant_sentences = [sentence for sentence in sentences if key_phrase in sentence]
    if not relevant_sentences:
        return None, None  # No question can be generated without relevant sentences

    relevant_sentence = random.choice(relevant_sentences)
    is_true = random.choice([True, False])
    if is_true:
        question = f"True or False: {relevant_sentence}"
        answer = "True"
    else:
        question = f"True or False: {relevant_sentence} (This statement is False)"
        answer = "False"
    return question, answer

def summarize_sentences(sentences):
    # Tokenize the sentences and remove stopwords
    stop_words = set(nltk.corpus.stopwords.words('english'))
    word_tokens = nltk.word_tokenize(' '.join(sentences))
    filtered_words = [w for w in word_tokens if not w.lower() in stop_words]
    
    # Calculate the frequency distribution of the words
    freq_dist = nltk.FreqDist(filtered_words)
    
    # Select the most common words as key phrases
    key_phrases = [word for word, freq in freq_dist.most_common(5)]
    
    # Create a summary using sentences that contain the key phrases
    summary = []
    for sentence in sentences:
        for phrase in key_phrases:
            if phrase in sentence:
                summary.append(sentence)
                break
                
    return ' '.join(summary)

def create_short_answer_question(key_phrase, sentences):
    relevant_sentences = [sentence for sentence in sentences if key_phrase in sentence]
    if not relevant_sentences:
        return None, None  # No question can be generated without relevant sentences

    summary = summarize_sentences(relevant_sentences)
    question = f"Describe the importance of {key_phrase}?"
    answer = summary
    return question, answer

def create_essay_question(key_phrase, sentences):
    relevant_sentences = [sentence for sentence in sentences if key_phrase in sentence]
    if not relevant_sentences:
        return None, None  # No question can be generated without relevant sentences

    summary = summarize_sentences(relevant_sentences)
    question = f"Discuss the role of {key_phrase}?"
    answer = summary
    return question, answer

# Handle unknown routes
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'message': 'This route is not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change the port number if needed
