from flask import Flask, render_template, request, jsonify
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber
import docx
import string
import os

app = Flask(__name__)

# Download NLTK data (run once)
import nltk
nltk.download('punkt')
nltk.download('stopwords')

def preprocess_text(text):
    # Remove punctuation and lowercase
    text = text.translate(str.maketrans('', '', string.punctuation)).lower()
    # Tokenize and remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text)
    filtered_text = [word for word in tokens if word not in stop_words]
    return ' '.join(filtered_text)

def extract_text(file):
    if file.filename.endswith('.pdf'):
        with pdfplumber.open(file) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
        return text
    elif file.filename.endswith('.docx'):
        doc = docx.Document(file)
        return '\n'.join([para.text for para in doc.paragraphs])
    else:
        return file.read().decode('utf-8')

def check_plagiarism(text1, text2):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    return round(similarity * 100, 2)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    # Get user input
    user_text = request.form.get('text')
    reference_file = request.files.get('file')
    
    if not user_text or not reference_file:
        return jsonify({'error': 'Missing text or file!'})
    
    try:
        reference_text = extract_text(reference_file)
        processed_user = preprocess_text(user_text)
        processed_ref = preprocess_text(reference_text)
        similarity = check_plagiarism(processed_user, processed_ref)
        return jsonify({'similarity': similarity})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
