import numpy as np
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import Counter
import math
import nltk

nltk.download('punkt')
#   percent to know if text unique or not
def calculate_perplexity(Text,n = 2 ):
    tokens = word_tokenize(Text.lower())
    ngrams = list(zip(*[tokens[i:] for i in range(n)]))
    ngram_counts = Counter(ngrams)
    total_ngrams = len(ngrams)
    if total_ngrams == 0:
        return float('inf')
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
    # This is a simplified heuristic
    normalized_perplexity = min(perplexity / 100, 1.0)  # Normalize to 0-1
    normalized_burstiness = min(burstiness / 2, 1.0)  # Normalize to 0-1

    # AI text tends to have lower perplexity and burstiness
    ai_proportion = 0.6 * (1 - normalized_perplexity) + 0.4 * (1 - normalized_burstiness)
    ai_proportion = max(0, min(1, ai_proportion))  # Clamp between 0 and 1

    return perplexity, burstiness, ai_proportion




