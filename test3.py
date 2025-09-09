from flask import Flask, request, render_template, jsonify
import os
import re
import math
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import string
import zipfile
import io

app = Flask(__name__)

# Download all required NLTK resources
try:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('punkt_tab')  # Additional resource needed for sentence tokenization
except Exception as e:
    print(f"Error downloading NLTK resources: {e}")


class AIDetector:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))

    def extract_features(self, text):
        """Extract advanced features from text"""
        try:
            # Basic cleaning
            text = re.sub(r'[^\w\s\.\?\!]', '', text)

            # Sentence and word tokenization
            sentences = sent_tokenize(text)
            words = [word.lower() for word in word_tokenize(text) if word.isalpha()]
            word_count = len(words)

            if word_count < 10:
                return None

            features = {}

            # 1. Lexical Features
            features['lexical_diversity'] = len(set(words)) / word_count
            features['ttr'] = len(set(words)) / word_count  # Type-Token Ratio
            features['mattr'] = self.calculate_mattr(words)

            # 2. Syntactic Features
            features['avg_sentence_length'] = word_count / len(sentences) if sentences else 0
            sentence_lengths = [len(word_tokenize(s)) for s in sentences]
            features['sentence_length_variance'] = np.var(sentence_lengths) if len(sentences) > 1 else 0

            # 3. Word Frequency Features
            word_freq = Counter(words)
            top_words = word_freq.most_common(10)
            features['top_word_ratio'] = sum(count for word, count in top_words) / word_count

            # 4. Punctuation Features
            features['punctuation_ratio'] = sum(1 for char in text if char in string.punctuation) / word_count

            # 5. Burstiness
            features['burstiness'] = self.calculate_burstiness(words)

            # 6. Perplexity-like measure
            features['perplexity'] = self.calculate_simple_perplexity(words)

            # 7. Stopword Features
            stopword_count = sum(1 for word in words if word in self.stop_words)
            features['stopword_ratio'] = stopword_count / word_count

            return features
        except Exception as e:
            print(f"Error in feature extraction: {e}")
            return None

    def calculate_mattr(self, words, window_size=50):
        """Moving Average Type-Token Ratio"""
        if len(words) < window_size:
            return len(set(words)) / len(words)

        tt_ratios = []
        for i in range(len(words) - window_size + 1):
            window = words[i:i + window_size]
            tt_ratios.append(len(set(window)) / window_size)

        return sum(tt_ratios) / len(tt_ratios)

    def calculate_burstiness(self, words):
        """Calculate burstiness of word usage"""
        if len(words) < 2:
            return 0

        word_counts = Counter(words)
        freqs = list(word_counts.values())
        mean_freq = np.mean(freqs)
        std_freq = np.std(freqs)

        if mean_freq == 0:
            return 0
        return (std_freq - mean_freq) / (std_freq + mean_freq)

    def calculate_simple_perplexity(self, words, n=2):
        """Calculate simplified perplexity measure"""
        if len(words) < n + 1:
            return 0

        ngrams = []
        for i in range(len(words) - n):
            ngrams.append(tuple(words[i:i + n]))

        ngram_counts = Counter(ngrams)
        total_ngrams = len(ngrams)

        entropy = 0.0
        for count in ngram_counts.values():
            probability = count / total_ngrams
            entropy -= probability * math.log(probability + 1e-10, 2)

        return 2 ** entropy

    def detect(self, text):
        """Detect if text is AI-generated using heuristic approach"""
        try:
            features = self.extract_features(text)
            if not features:
                return {"error": "Text too short or invalid"}

            # Heuristic scoring
            score = 0
            max_score = 7

            # 1. Lexical diversity (AI tends to be higher)
            if features['lexical_diversity'] > 0.7:
                score += 1

            # 2. Sentence length variance (AI tends to be more consistent)
            if features['sentence_length_variance'] < 20:
                score += 1

            # 3. Stopword ratio (AI may use fewer stopwords)
            if features['stopword_ratio'] < 0.3:
                score += 1

            # 4. Burstiness (Human text tends to be more bursty)
            if features['burstiness'] < 0.2:
                score += 1

            # 5. Perplexity (AI text tends to be less surprising)
            if features['perplexity'] < 50:
                score += 1

            # 6. Punctuation consistency
            if 0.05 <= features['punctuation_ratio'] <= 0.15:
                score += 1

            # 7. MATTR (AI tends to be more consistent)
            if features['mattr'] > 0.6:
                score += 1

            confidence = score / max_score
            ai_generated = confidence > 0.6

            return {
                "ai_generated": ai_generated,
                "confidence": f"{confidence:.2%}",
                "score": f"{score}/{max_score}",
                "label": "AI" if ai_generated else "Human",
                "features": features
            }
        except Exception as e:
            return {"error": str(e)}


# Initialize detector
detector = AIDetector()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text_input = request.form.get('text_input', '').strip()
        file = request.files.get('file_upload')
        file_content = ""

        if file:
            if file.filename.endswith('.txt'):
                try:
                    file_content = file.read().decode('utf-8')
                except Exception as e:
                    return render_template('test3.html', error=f"File read error: {str(e)}")
            elif file.filename.endswith('.zip'):
                try:
                    with zipfile.ZipFile(io.BytesIO(file.read())) as z:
                        for name in z.namelist():
                            if name.endswith('.txt'):
                                with z.open(name) as f:
                                    file_content += f.read().decode('utf-8') + "\n\n"
                except Exception as e:
                    return render_template('test3.html', error=f"ZIP file error: {str(e)}")

        full_text = text_input if text_input else file_content

        if not full_text:
            return render_template('test3.html', error="Please enter text or upload a file")

        result = detector.detect(full_text)

        return render_template('test3.html',
                               result=result,
                               original_text=full_text[:500] + "..." if len(full_text) > 500 else full_text)

    return render_template('test3.html')


@app.route('/api/detect', methods=['POST'])
def api_detect():
    """API endpoint for programmatic access"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    result = detector.detect(data['text'])
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)