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

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')


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

            # Basic statistics
            features['word_count'] = word_count
            features['unique_words'] = len(set(words))
            features['avg_word_length'] = sum(len(word) for word in words) / word_count

            # Lexical features
            features['lexical_diversity'] = len(set(words)) / word_count
            features['mattr'] = self.calculate_mattr(words)

            # Sentence features
            features['sentence_count'] = len(sentences)
            sentence_lengths = [len(word_tokenize(sent)) for sent in sentences]
            features['avg_sentence_length'] = sum(sentence_lengths) / len(sentences) if sentences else 0
            features['sentence_length_variance'] = np.var(sentence_lengths) if len(sentences) > 1 else 0

            # Readability
            features['flesch_kincaid'] = self.calculate_flesch_kincaid(text, sentences, word_count)

            # Word frequency
            word_freq = Counter(words)
            features['top_word_ratio'] = sum(count for word, count in word_freq.most_common(10)) / word_count

            # Stopwords
            stopword_count = sum(1 for word in words if word in self.stop_words)
            features['stopword_ratio'] = stopword_count / word_count

            # Burstiness
            features['burstiness'] = self.calculate_burstiness(words)

            # Perplexity
            features['perplexity'] = self.calculate_simple_perplexity(words)

            # Technical terms
            features['technical_terms'] = self.extract_technical_terms(text)

            return features
        except Exception as e:
            print(f"Error in feature extraction: {e}")
            return None

    def extract_technical_terms(self, text):
        """Extract potential technical terms using POS patterns"""
        words = word_tokenize(text)
        pos_tags = nltk.pos_tag(words)

        # Pattern: Adjective + Noun or Noun + Noun
        terms = []
        for i in range(len(pos_tags) - 1):
            word1, tag1 = pos_tags[i]
            word2, tag2 = pos_tags[i + 1]

            if (tag1.startswith('JJ') and tag2.startswith('NN')) or \
                    (tag1.startswith('NN') and tag2.startswith('NN')):
                terms.append(f"{word1} {word2}")

        return list(set(terms[:20]))  # Return up to 20 unique terms

    def classify_content(self, text):
        """Classify text into content categories"""
        keywords = {
            "Technology": ["algorithm", "programming", "software", "hardware", "system"],
            "Science": ["research", "study", "experiment", "theory", "analysis"],
            "Business": ["market", "business", "finance", "investment", "strategy"],
            "Education": ["learning", "education", "teaching", "student", "school"],
            "Health": ["medical", "health", "disease", "treatment", "patient"]
        }

        text_lower = text.lower()
        scores = {category: 0 for category in keywords}

        # Score based on keywords
        for category, terms in keywords.items():
            for term in terms:
                if term in text_lower:
                    scores[category] += 1

        # Get top categories
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_categories = [cat for cat, score in sorted_categories[:2] if score > 0]

        return top_categories if top_categories else ["General"]

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

    def calculate_flesch_kincaid(self, text, sentences, word_count):
        """Calculate Flesch-Kincaid readability score"""
        syllable_count = sum(self.count_syllables(word) for word in word_tokenize(text))
        sentence_count = len(sentences)

        if word_count == 0 or sentence_count == 0:
            return 0

        return 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)

    def count_syllables(self, word):
        """Approximate syllable count"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count += 1
        return count

    def detect(self, text):
        """Detect if text is AI-generated with content analysis"""
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

            # 6. MATTR (AI tends to be more consistent)
            if features['mattr'] > 0.6:
                score += 1

            # 7. Top word concentration (AI may overuse certain words)
            if features['top_word_ratio'] > 0.25:
                score += 1

            confidence = score / max_score
            ai_generated = confidence > 0.6

            # Content classification
            categories = self.classify_content(text)

            return {
                "ai_generated": ai_generated,
                "confidence": f"{confidence:.2%}",
                "confidence_value": confidence * 100,  # Add this for the progress bar
                "label": "AI" if ai_generated else "Human",
                "features": features,
                "categories": categories,
                "score": f"{score}/{max_score}"
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
                    return render_template('test4.html', error=f"File read error: {str(e)}")
            elif file.filename.endswith('.zip'):
                try:
                    with zipfile.ZipFile(io.BytesIO(file.read())) as z:
                        for name in z.namelist():
                            if name.endswith('.txt'):
                                with z.open(name) as f:
                                    file_content += f.read().decode('utf-8') + "\n\n"
                except Exception as e:
                    return render_template('test4.html', error=f"ZIP file error: {str(e)}")

        full_text = text_input if text_input else file_content

        if not full_text:
            return render_template('test4.html', error="Please enter text or upload a file")

        result = detector.detect(full_text)

        return render_template('test4.html',
                               result=result,
                               original_text=full_text[:500] + "..." if len(full_text) > 500 else full_text)

    # For GET requests, pass an empty result
    return render_template('test4.html', result=None)


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