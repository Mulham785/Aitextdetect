from flask import jsonify, request, render_template, redirect, url_for, flash
from app import app, db
from app.models import Text, AnalysisResult
from app.text_analyzer import analyze_text
from app.pdf_extractor import extract_text_from_pdf, save_uploaded_file
import os
import datetime


# UI Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])  # Changed function name to match route
def analyze():  # Changed function name to match route
    # Check if it's a file upload or text input
    if 'file' in request.files and request.files['file'].filename != '':
        # File upload
        file = request.files['file']
        if file and file.filename.lower().endswith('.pdf'):
            # Save the file
            file_path = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])

            # Extract text from PDF
            text_content = extract_text_from_pdf(file_path)

            if text_content:
                source = 'pdf'
                topic = 'Uploaded PDF'
            else:
                flash('Error extracting text from PDF')
                return redirect(url_for('index'))
        else:
            flash('Only PDF files are allowed')
            return redirect(url_for('index'))
    else:
        # Text input
        text_content = request.form.get('text', '')
        if not text_content:
            flash('Please enter text or upload a file')
            return redirect(url_for('index'))

        source = 'manual'
        topic = 'Manual Input'
        file_path = None

    # Create a new text entry
    text = Text(
        content=text_content,
        source=source,
        topic=topic,
        file_path=file_path
    )
    db.session.add(text)
    db.session.commit()

    # Analyze the text
    perplexity, burstiness, ai_proportion = analyze_text(text_content)

    analysis = AnalysisResult(
        text_id=text.id,
        perplexity=perplexity,
        burstiness=burstiness,
        ai_proportion=ai_proportion
    )
    db.session.add(analysis)
    db.session.commit()

    # Redirect to results page
    return redirect(url_for('results', text_id=text.id))


@app.route('/results/<int:text_id>')
def results(text_id):
    text = Text.query.get_or_404(text_id)
    analysis = AnalysisResult.query.filter_by(text_id=text_id).first()

    return render_template('results.html',
                           text=text,
                           analysis=analysis)

# API Endpoints remain the same...