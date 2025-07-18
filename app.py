from flask import Flask, render_template, request, jsonify, send_from_directory
from WebScraper import WebScraper
import os
import json
import csv
from datetime import datetime
import logging
from functools import wraps

app = Flask(__name__, static_folder='static')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function for Vercel detection
def is_vercel():
    return os.environ.get('VERCEL', '').lower() in ('1', 'true')

# Improved static files handler
@app.route('/static/<path:filename>')
def static_files(filename):
    static_path = os.path.join(os.getcwd(), 'static') if is_vercel() else app.static_folder
    return send_from_directory(static_path, filename)

try:
    import serverless_wsgi
except ImportError:
    serverless_wsgi = None

def handler(event, context):
    if serverless_wsgi is None:
        raise RuntimeError("serverless-wsgi is not available")
    return serverless_wsgi.handle_request(app, event, context)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape():
    try:
        data = request.get_json()
        logger.info(f"Received scrape request: {data}")
        
        # Validate input
        if not data or 'urls' not in data:
            logger.error("No URLs provided")
            return jsonify({'error': 'No URLs provided'}), 400
            
        # Ensure URLs is a list
        urls = data['urls'] if isinstance(data['urls'], list) else [data['urls']]
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            logger.error("Empty or invalid URLs provided")
            return jsonify({'error': 'Empty or invalid URLs provided'}), 400
        
        # Initialize scraper with options
        scraper = WebScraper(
            delay=float(data.get('delay', 1.0)),
            timeout=int(data.get('timeout', 10))
        )
        
        # Configure extraction
        config = {
            'extract_links': bool(data.get('extractLinks', True)),
            'extract_text': bool(data.get('extractText', True)),
            'extract_images': bool(data.get('extractImages', True)),
            'extract_tables': bool(data.get('extractTables', True)),
            'text_selector': data.get('textSelector') or None
        }
        
        logger.info(f"Starting scrape with config: {config}")
        
        # Scrape the URLs
        results = scraper.scrape_multiple_pages(urls, config)
        
        if not results:
            logger.warning("No results returned from scraper")
            return jsonify({'error': 'No data was scraped successfully'}), 400
            
        logger.info(f"Successfully scraped {len(results)} pages")
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/json', methods=['POST'])
def export_json():
    try:
        data = request.get_json()
        if not data:
            logger.error("No data provided for JSON export")
            return jsonify({'error': 'No data provided'}), 400
        
        # Create appropriate temp directory
        temp_dir = '/tmp' if is_vercel() else 'temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create filename with timestamp
        filename = f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(temp_dir, filename)
        
        # Write JSON data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON export created: {filename}")
        return jsonify({
            'filename': filename,
            'message': 'JSON export created successfully'
        })
        
    except Exception as e:
        logger.error(f"JSON export failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    try:
        data = request.get_json()
        if not data:
            logger.error("No data provided for CSV export")
            return jsonify({'error': 'No data provided'}), 400
        
        # Flatten the data for CSV
        flattened_data = []
        for item in data:
            flat_item = {
                'url': item.get('url', ''),
                'title': item.get('title', ''),
                'timestamp': item.get('timestamp', ''),
                'num_links': len(item.get('links', [])),
                'num_images': len(item.get('images', [])),
                'num_tables': len(item.get('tables', [])),
                'text_preview': ' '.join(item.get('text', []))[:200] + '...' if item.get('text') else ''
            }
            flattened_data.append(flat_item)
        
        # Create appropriate temp directory
        temp_dir = '/tmp' if is_vercel() else 'temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create filename with timestamp
        filename = f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(temp_dir, filename)
        
        # Write CSV data
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if flattened_data:
                fieldnames = flattened_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_data)
        
        logger.info(f"CSV export created: {filename}")
        return jsonify({
            'filename': filename,
            'message': 'CSV export created successfully'
        })
        
    except Exception as e:
        logger.error(f"CSV export failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        temp_dir = '/tmp' if is_vercel() else 'temp'
        return send_from_directory(temp_dir, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"File download failed: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    # Create appropriate temp directory
    temp_dir = '/tmp' if is_vercel() else 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    
    # Only run Flask dev server locally
    if not is_vercel():
        app.run(debug=True, port=3001)