let video = null;
let totalQuestions = parseInt(document.getElementById('progress').innerText.split('of')[1]);

// Set up Speech Recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US'; // change this if needed
    recognition.interimResults = false; // only final results
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            }
        }
        if (finalTranscript) {
            document.querySelector('#answer').value = finalTranscript;
            console.log('Recognized speech:', finalTranscript);
            // Optional: auto-submit after voice input
            // submitAnswer();
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech Recognition Error:', event.error);
        if (event.error === 'no-speech') {
            alert('No speech detected. Please try again.');
        } else {
            alert('Speech recognition error: ' + event.error);
        }
    };

    recognition.onend = () => {
        console.log('Speech recognition ended.');
        // You can choose to restart here if continuous listening is desired
    };
} else {
    alert('Your browser does not support Web Speech API. Please use Google Chrome desktop.');
}

window.onload = function () {
    video = document.getElementById('video');

    // Start webcam
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => { video.srcObject = stream; })
        .catch(err => {
            alert('Unable to access camera: ' + err);
        });

    // Speak first question and start listening
    const firstQuestion = document.getElementById('question').innerText;
    speakQuestion(firstQuestion);

    setTimeout(() => {
        if (recognition) recognition.start();
    }, 500);
};

// Speak question aloud
function speakQuestion(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    window.speechSynthesis.speak(utterance);
}

// Manual mic trigger from Speak button
function startSpeechRecognition() {
    if (recognition) {
        recognition.start();
    } else {
        alert('Speech recognition not supported in your browser.');
    }
}

// Submit answer to backend
function submitAnswer() {
    const answerField = document.getElementById('answer');
    const answer = answerField.value.trim();
    if (!answer) {
        alert('Please provide an answer, either by speaking or typing.');
        return;
    }

    // Capture webcam snapshot
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 320;
    canvas.height = video.videoHeight || 240;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const imageData = canvas.toDataURL('image/jpeg');

    fetch('/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer: answer, image: imageData })
    })
    .then(res => res.json())
    .then(data => {
        if (data.done) {
            window.location.href = "/complete";
        } else {
            // Update question and reset input
            document.getElementById("question").innerText = data.next_question;
            document.getElementById("progress").innerText = `Question ${data.current} of ${totalQuestions}`;
            answerField.value = '';

            // Speak the new question
            speakQuestion(data.next_question);

            // Auto-start speech recognition after short pause
            setTimeout(() => {
                if (recognition) recognition.start();
            }, 700);
        }
    })
    .catch(error => {
        console.error("Error submitting answer:", error);
        alert('Error submitting your answer. Please try again.');
    });
}
