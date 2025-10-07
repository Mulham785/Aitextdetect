import numpy as np
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import Counter
import math
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk

nltk.download('punkt')


def calculate_perplexity(text, n=2):
    """Calculate perplexity using n-gram model"""
    tokens = word_tokenize(text.lower())
    ngrams = list(zip(*[tokens[i:] for i in range(n)]))
    ngram_counts = Counter(ngrams)
    total_ngrams = len(ngrams)

    if total_ngrams == 0:
        return float('inf')

    # Calculate log probability
    log_prob = 0
    for ngram in ngrams:
        count = ngram_counts[ngram]
        prob = count / total_ngrams
        log_prob += math.log(prob) if prob > 0 else 0

    # Calculate perplexity
    perplexity = math.exp(-log_prob / total_ngrams)
    return perplexity


def calculate_burstiness(text):
    """Calculate burstiness as variance of sentence lengths"""
    sentences = sent_tokenize(text)
    sentence_lengths = [len(word_tokenize(sent)) for sent in sentences]

    if len(sentence_lengths) < 2:
        return 0.0

    mean_length = np.mean(sentence_lengths)
    variance = np.var(sentence_lengths)

    # Normalize burstiness
    burstiness = variance / (mean_length ** 2) if mean_length > 0 else 0
    return burstiness


def analyze_text(text):
    """Analyze text for AI-generated content indicators"""
    perplexity = calculate_perplexity(text)
    burstiness = calculate_burstiness(text)

    # Calculate AI proportion based on metrics
    normalized_perplexity = min(perplexity / 100, 1.0)  # Normalize to 0-1
    normalized_burstiness = min(burstiness / 2, 1.0)  # Normalize to 0-1

    # AI text tends to have lower perplexity and burstiness
    ai_proportion = 0.6 * (1 - normalized_perplexity) + 0.4 * (1 - normalized_burstiness)
    ai_proportion = max(0, min(1, ai_proportion))  # Clamp between 0 and 1

    return perplexity, burstiness, ai_proportion


def compare_with_documents(text, documents):
    """Compare text with a list of documents using TF-IDF and cosine similarity"""
    if not documents:
        return 0.0

    # Create a list with the input text and all comparison documents
    all_texts = [text] + [doc.content for doc in documents]

    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer().fit_transform(all_texts)

    # Calculate cosine similarity between input text and each document
    vectors = vectorizer.toarray()
    text_vector = vectors[0:1]
    doc_vectors = vectors[1:]

    similarities = cosine_similarity(text_vector, doc_vectors)[0]

    # Return average similarity
    return np.mean(similarities)


def comprehensive_text_analysis(text):
    """Comprehensive analysis comparing with stored AI and human documents"""
    from app.models import Text

    # Basic metrics
    perplexity, burstiness, ai_proportion = analyze_text(text)

    # Get AI and human documents from database
    ai_docs = Text.query.filter_by(is_ai=True).all()
    human_docs = Text.query.filter_by(is_ai=False).all()

    # Calculate similarities
    ai_similarity = compare_with_documents(text, ai_docs)
    human_similarity = compare_with_documents(text, human_docs)

    # Calculate overall AI score based on all metrics
    # Weighted combination of all indicators
    overall_ai_score = (
            0.3 * ai_proportion +
            0.3 * ai_similarity +
            0.2 * (1 - human_similarity) +
            0.1 * (1 - perplexity) +
            0.1 * (1 - burstiness)
    )

    return {
        'perplexity': perplexity,
        'burstiness': burstiness,
        'ai_proportion': ai_proportion,
        'ai_similarity': ai_similarity,
        'human_similarity': human_similarity,
        'overall_ai_score': overall_ai_score
    }