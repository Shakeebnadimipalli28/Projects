from flask import Flask, render_template, request, jsonify, send_file, session
import cv2, os
import numpy as np
from keras.models import load_model
from textblob import TextBlob
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import base64
import io
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change to your secret key
app.config['UPLOAD_FOLDER'] = 'static/captures'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load facial emotion model and cascade classifier
face_model = load_model('model.h5')
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']

# Define questions
questions = [
    "How have you been feeling emotionally on a day-to-day basis?",
        "Can you describe any recent changes in your mood, such as feeling more sad, anxious, or irritable than usual?",
        "Have you lost interest or pleasure in activities that you used to enjoy?",
        "How is your sleep? Are you having trouble falling or staying asleep, or are you sleeping too much?",
        "How is your appetite? Have you experienced significant weight loss or gain recently?",
        "Do you often feel nervous, anxious, or on edge? Are there specific situations that trigger these feelings?",
        "Do you have difficulty concentrating, making decisions, or remembering things?",
        "Have you had any thoughts about harming yourself or ending your life? If so, do you have a plan?",
        "How are your relationships with family and friends? Do you feel supported by the people around you?",
        "Do you use alcohol, drugs, or other substances? If so, how often and in what quantities, and do you feel it impacts your daily life?"
    
]

def get_face_emotion(img_path):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, 1.1, 3)
        if len(faces) == 0:
            return "No face detected"
    (x, y, w, h) = faces[0]
    face = gray[y:y+h, x:x+w]
    face = cv2.resize(face, (48, 48)).astype('float') / 255.0
    face = np.expand_dims(face, axis=0)
    face = np.expand_dims(face, axis=-1)
    preds = face_model.predict(face)
    return emotion_labels[np.argmax(preds)]

def get_text_sentiment(answer):
    polarity = TextBlob(answer).sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

def assess_health_condition(text_emos, face_emos):
    negative_indicators = ['Negative', 'Sad', 'Fear', 'Angry', 'Disgust']
    negative_count = 0
    for t_em, f_em in zip(text_emos, face_emos):
        if t_em == 'Negative':
            negative_count += 1
        if f_em in negative_indicators:
            negative_count += 1

    if negative_count == 0:
        return "No apparent mental health concerns detected."
    elif negative_count <= 3:
        return "Mild signs of emotional distress detected. Consider consultation if symptoms persist."
    else:
        return "Several signs of emotional distress detected. It is recommended to consult a mental health professional."

def generate_pdf_report(questions, answers, text_emotions, face_emotions, images, summary):
    c = canvas.Canvas("report.pdf", pagesize=letter)
    width, height = letter
    y = height - 50
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, y, "Mental Health Assessment Report")
    y -= 40
    
    for i in range(len(questions)):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, f"Q{i+1}: {questions[i]}")
        y -= 15
        c.setFont("Helvetica", 11)
        c.drawString(30, y, f"Answer: {answers[i]}")
        y -= 15
        c.drawString(30, y, f"Text Sentiment: {text_emotions[i]}")
        y -= 15
        c.drawString(30, y, f"Facial Emotion: {face_emotions[i]}")
        y -= 15
        try:
            c.drawImage(images[i], 400, y-40, width=80, height=80)
        except:
            pass
        y -= 100
        if y < 100:
            c.showPage()
            y = height - 50
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y, "Summary Assessment:")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(30, y, summary)
    y -= 15
    c.drawString(30, y, "This automated report combines text sentiment and facial emotion analysis.")
    y -= 15
    c.drawString(30, y, "Please consult a qualified mental health professional for interpretation.")
    
    c.save()

@app.route('/')
def home():
    session['answers'] = []
    session['text_emotions'] = []
    session['face_emotions'] = []
    session['images'] = []
    session['q_index'] = 0
    return render_template('index.html', question=questions[0], total=len(questions))

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    answer = data['answer']
    img_data = data['image'].split(',')[1]  # Remove base64 header
    img_bytes = base64.b64decode(img_data)
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], f"q{session['q_index']+1}.jpg")
    with open(img_path, 'wb') as f:
        f.write(img_bytes)
    
    txt_em = get_text_sentiment(answer)
    face_em = get_face_emotion(img_path)
    
    session['answers'].append(answer)
    session['text_emotions'].append(txt_em)
    session['face_emotions'].append(face_em)
    session['images'].append(img_path)
    
    session['q_index'] += 1
    
    if session['q_index'] >= len(questions):
        # Generate summary
        summary = assess_health_condition(session['text_emotions'], session['face_emotions'])
        # Generate PDF
        generate_pdf_report(
            questions,
            session['answers'],
            session['text_emotions'],
            session['face_emotions'],
            session['images'],
            summary
        )
        # Store summary in session for results page
        session['summary'] = summary
        return jsonify({'done': True})
    
    return jsonify({
        'done': False,
        'next_question': questions[session['q_index']],
        'current': session['q_index'] + 1
    })

@app.route('/complete')
def complete():
    summary = session.get('summary', 'No summary available.')
    # Additionally, you may calculate stats here for detailed analytics
    # For example, % distribution of emotions and sentiments for charts
    return render_template('complete.html', summary=summary)

@app.route('/download')
def download():
    return send_file("report.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

