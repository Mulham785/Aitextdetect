from flask import jsonify, request, render_template, redirect, url_for
from app import app, db
from app.models import Text, AnalysisResult, ACMTopic
from app.text_analyzer import comprehensive_text_analysis
from app.pdf_extractor import extract_text_from_pdf, save_uploaded_file
from app.ai_generator import initialize_acm_topics, generate_ai_document
import os
import datetime


# Function to initialize ACM topics
def initialize_app():
    with app.app_context():
        if ACMTopic.query.count() == 0:
            initialize_acm_topics()


# UI Routes
@app.route('/')
def index():
    # Get statistics for dashboard
    ai_count = Text.query.filter_by(is_ai=True).count()
    human_count = Text.query.filter_by(is_ai=False).count()
    analysis_count = AnalysisResult.query.count()
    topic_count = ACMTopic.query.count()

    # Get recent analyses
    recent_analyses = AnalysisResult.query.order_by(AnalysisResult.analyzed_at.desc()).limit(5).all()

    return render_template('index.html',
                           ai_count=ai_count,
                           human_count=human_count,
                           analysis_count=analysis_count,
                           topic_count=topic_count,
                           recent_analyses=recent_analyses)


@app.route('/upload_ai', methods=['GET', 'POST'])
def upload_ai():
    if request.method == 'POST':
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
                    topic = 'Uploaded AI Document'
                else:
                    return render_template('upload_ai.html', error='Error extracting text from PDF')
            else:
                return render_template('upload_ai.html', error='Only PDF files are allowed')
        else:
            # Text input
            text_content = request.form.get('text', '')
            if not text_content:
                return render_template('upload_ai.html', error='Please enter text or upload a file')

            source = 'manual'
            topic = 'Manual AI Input'
            file_path = None

        # Create a new AI text entry
        text = Text(
            content=text_content,
            source=source,
            topic=topic,
            file_path=file_path,
            is_ai=True
        )
        db.session.add(text)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('upload_ai.html')


@app.route('/upload_human', methods=['GET', 'POST'])
def upload_human():
    if request.method == 'POST':
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
                    topic = 'Uploaded Human Document'
                else:
                    return render_template('upload_human.html', error='Error extracting text from PDF')
            else:
                return render_template('upload_human.html', error='Only PDF files are allowed')
        else:
            # Text input
            text_content = request.form.get('text', '')
            if not text_content:
                return render_template('upload_human.html', error='Please enter text or upload a file')

            source = 'manual'
            topic = 'Manual Human Input'
            file_path = None

        # Create a new human text entry
        text = Text(
            content=text_content,
            source=source,
            topic=topic,
            file_path=file_path,
            is_ai=False
        )
        db.session.add(text)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('upload_human.html')


@app.route('/generate_ai', methods=['GET', 'POST'])
def generate_ai():
    if request.method == 'POST':
        topic_name = request.form.get('topic')
        if not topic_name:
            return render_template('generate_ai.html', topics=ACMTopic.query.all(), error='Please select a topic')

        # Generate AI document
        ai_content = generate_ai_document(topic_name)

        # Create a new AI text entry
        text = Text(
            content=ai_content,
            source='generated',
            topic=topic_name,
            is_ai=True,
            acm_topic=topic_name
        )
        db.session.add(text)
        db.session.commit()

        return redirect(url_for('index'))

    topics = ACMTopic.query.all()
    return render_template('generate_ai.html', topics=topics)


@app.route('/detect', methods=['GET', 'POST'])
def detect():
    if request.method == 'POST':
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
                    topic = 'Uploaded for Detection'
                else:
                    return render_template('detect.html', error='Error extracting text from PDF')
            else:
                return render_template('detect.html', error='Only PDF files are allowed')
        else:
            # Text input
            text_content = request.form.get('text', '')
            if not text_content:
                return render_template('detect.html', error='Please enter text or upload a file')

            source = 'manual'
            topic = 'Manual Input for Detection'
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

        # Perform comprehensive analysis
        analysis_results = comprehensive_text_analysis(text_content)

        # Save analysis results
        analysis = AnalysisResult(
            text_id=text.id,
            perplexity=analysis_results['perplexity'],
            burstiness=analysis_results['burstiness'],
            ai_proportion=analysis_results['ai_proportion'],
            ai_similarity=analysis_results['ai_similarity'],
            human_similarity=analysis_results['human_similarity']
        )
        db.session.add(analysis)
        db.session.commit()

        # Redirect to results page
        return redirect(url_for('results', text_id=text.id))

    return render_template('detect.html')


@app.route('/results/<int:text_id>')
def results(text_id):
    text = Text.query.get_or_404(text_id)
    analysis = AnalysisResult.query.filter_by(text_id=text_id).first()

    return render_template('results.html',
                           text=text,
                           analysis=analysis)


# New routes for viewing documents
@app.route('/view_ai_docs')
def view_ai_docs():
    # Get filter parameters
    topic_filter = request.args.get('topic', '')
    source_filter = request.args.get('source', '')

    # Build query
    query = Text.query.filter_by(is_ai=True)

    if topic_filter:
        query = query.filter(Text.topic.contains(topic_filter))

    if source_filter:
        query = query.filter_by(source=source_filter)

    documents = query.order_by(Text.id.desc()).all()
    topics = ACMTopic.query.all()

    return render_template('view_ai_docs.html', documents=documents, topics=topics)


@app.route('/view_human_docs')
def view_human_docs():
    # Get filter parameters
    topic_filter = request.args.get('topic', '')
    source_filter = request.args.get('source', '')

    # Build query
    query = Text.query.filter_by(is_ai=False)

    if topic_filter:
        query = query.filter(Text.topic.contains(topic_filter))

    if source_filter:
        query = query.filter_by(source=source_filter)

    documents = query.order_by(Text.id.desc()).all()

    return render_template('view_human_docs.html', documents=documents)


@app.route('/view_document/<int:doc_id>')
def view_document(doc_id):
    text = Text.query.get_or_404(doc_id)
    analysis = AnalysisResult.query.filter_by(text_id=doc_id).first()

    return render_template('view_document.html', text=text, analysis=analysis)


@app.route('/analyze_document/<int:doc_id>')
def analyze_document(doc_id):
    text = Text.query.get_or_404(doc_id)

    # Perform comprehensive analysis
    analysis_results = comprehensive_text_analysis(text.content)

    # Save or update analysis results
    analysis = AnalysisResult.query.filter_by(text_id=doc_id).first()

    if analysis:
        analysis.perplexity = analysis_results['perplexity']
        analysis.burstiness = analysis_results['burstiness']
        analysis.ai_proportion = analysis_results['ai_proportion']
        analysis.ai_similarity = analysis_results['ai_similarity']
        analysis.human_similarity = analysis_results['human_similarity']
        analysis.analyzed_at = datetime.datetime.utcnow()
    else:
        analysis = AnalysisResult(
            text_id=doc_id,
            perplexity=analysis_results['perplexity'],
            burstiness=analysis_results['burstiness'],
            ai_proportion=analysis_results['ai_proportion'],
            ai_similarity=analysis_results['ai_similarity'],
            human_similarity=analysis_results['human_similarity']
        )
        db.session.add(analysis)

    db.session.commit()

    return redirect(url_for('view_document', doc_id=doc_id))


@app.route('/view_all_analyses')
def view_all_analyses():
    # Get filter parameters
    document_type = request.args.get('document_type', '')
    min_ai_score = request.args.get('min_ai_score', '')
    max_ai_score = request.args.get('max_ai_score', '')

    # Build query
    query = db.session.query(AnalysisResult, Text).join(Text)

    if document_type == 'ai':
        query = query.filter(Text.is_ai == True)
    elif document_type == 'human':
        query = query.filter(Text.is_ai == False)

    if min_ai_score:
        query = query.filter(AnalysisResult.ai_proportion >= float(min_ai_score))

    if max_ai_score:
        query = query.filter(AnalysisResult.ai_proportion <= float(max_ai_score))

    analyses = query.order_by(AnalysisResult.analyzed_at.desc()).all()

    return render_template('view_all_analyses.html', analyses=analyses)
# API Endpoints remain the same...