from flask import Flask, request, render_template, jsonify
import os
import re
import math
import random
from collections import Counter

app = Flask(__name__)


def calculate_text_statistics(text):
    """Calculate various statistics about the text"""
    # Clean text
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = text.split()

    if not words:
        return None

    # Calculate statistics
    word_count = len(words)
    unique_words = len(set(words))
    avg_word_length = sum(len(word) for word in words) / word_count

    # Sentence count (rough estimate)
    sentences = text.split('.')
    sentence_count = len([s for s in sentences if s.strip()])

    # Calculate lexical diversity (unique words / total words)
    lexical_diversity = unique_words / word_count if word_count > 0 else 0

    # Calculate average sentence length
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

    # Count common words
    common_words = ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i']
    common_word_count = sum(1 for word in words if word in common_words)
    common_word_ratio = common_word_count / word_count if word_count > 0 else 0

    return {
        'word_count': word_count,
        'unique_words': unique_words,
        'avg_word_length': avg_word_length,
        'sentence_count': sentence_count,
        'lexical_diversity': lexical_diversity,
        'avg_sentence_length': avg_sentence_length,
        'common_word_ratio': common_word_ratio
    }


def is_ai_generated(text):
    """
    Analyze text and return AI detection result using statistical analysis
    This is a heuristic approach based on common patterns in AI-generated text
    """
    try:
        stats = calculate_text_statistics(text)
        if not stats:
            return {"error": "Could not analyze text"}

        # Heuristic scoring based on common AI text patterns
        score = 0

        # AI text often has higher lexical diversity
        if stats['lexical_diversity'] > 0.7:
            score += 1

        # AI text often has longer average sentence length
        if stats['avg_sentence_length'] > 20:
            score += 1

        # AI text often has consistent word length
        if 4.5 <= stats['avg_word_length'] <= 5.5:
            score += 1

        # AI text often uses common words at a certain rate
        if 0.2 <= stats['common_word_ratio'] <= 0.4:
            score += 1

        # AI text often has consistent paragraph structure
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 1:
            avg_para_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            if 30 <= avg_para_length <= 100:
                score += 1

        # Additional heuristic: check for certain phrases common in AI text
        ai_phrases = [
            "in conclusion", "furthermore", "moreover", "however", "therefore",
            "as a result", "consequently", "additionally", "nevertheless", "nonetheless"
        ]
        text_lower = text.lower()
        ai_phrase_count = sum(1 for phrase in ai_phrases if phrase in text_lower)
        if ai_phrase_count > 2:
            score += 1

        # Additional heuristic: check for very consistent sentence lengths
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) > 3:
            sentence_lengths = [len(s.split()) for s in sentences]
            # Calculate coefficient of variation (std dev / mean)
            mean_length = sum(sentence_lengths) / len(sentence_lengths)
            if mean_length > 0:
                variance = sum((x - mean_length) ** 2 for x in sentence_lengths) / len(sentence_lengths)
                std_dev = math.sqrt(variance)
                cv = std_dev / mean_length
                # Lower CV means more consistent sentence lengths, which is common in AI text
                if cv < 0.4:
                    score += 1

        # Determine if text is AI-generated based on score
        max_score = 7
        confidence = score / max_score

        # Consider it AI-generated if score is at least 4 out of 7
        ai_generated = score >= 4

        return {
            "ai_generated": ai_generated,
            "confidence": f"{confidence:.2%}",
            "score": f"{score}/{max_score}",
            "label": "AI" if ai_generated else "Human",
            "statistics": stats
        }
    except Exception as e:
        return {"error": str(e)}


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle text input
        text_input = request.form.get('text_input', '').strip()

        # Handle file upload
        file = request.files.get('file_upload')
        file_content = ""

        if file and file.filename.endswith('.txt'):
            try:
                file_content = file.read().decode('utf-8')
            except Exception as e:
                return render_template('test2.html', error=f"File read error: {str(e)}")

        # Combine both inputs (prioritize direct text input)
        full_text = text_input if text_input else file_content

        if not full_text:
            return render_template('test2.html', error="Please enter text or upload a file")

        # Analyze text
        result = is_ai_generated(full_text)

        # Render results
        return render_template('test2.html',
                               result=result,
                               original_text=full_text[:200] + "..." if len(full_text) > 200 else full_text)

    return render_template('test2.html')


@app.route('/api/detect', methods=['POST'])
def api_detect():
    """API endpoint for programmatic access"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    result = is_ai_generated(data['text'])
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)