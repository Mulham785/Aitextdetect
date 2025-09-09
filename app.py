from flask import Flask, render_template, request
from datetime import datetime
import random
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

app = Flask(__name__)
#MODEL_NAME = "bert-base-grover-detector"

#MODEL_NAME = "distilbert-base-uncased-detector"
#MODEL_NAME = "roberta-base-openai-detector"
MODEL_NAME = "Hello-SimpleAI/chatgpt-detector-roberta"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)


def detect_ai_text(text):
    """
    Function to detect if text is AI-generated
    Returns a dictionary with probabilities for human and AI
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

    return {
        "human": round(probs[0][0].item(), 4),
        "ai": round(probs[0][1].item(), 4)
    }

def fake_ai_detector(text):
    return random.randint(5, 95) if text.strip() else 0






@app.route('/')
def index():
    return render_template('index.html', ai_score=None, current_year=datetime.now().year)

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.form.get('input_text', '').strip()
    ai_score = detect_ai_text(text)
    return render_template('index.html', ai_score=ai_score['ai']*100, current_year=datetime.now().year)

if __name__ == '__main__':
    app.run(debug=True)
