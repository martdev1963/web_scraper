from flask import Flask, render_template, request, jsonify, send_from_directory
from web_scraper import WebScraper  # Import your existing scraper class
import os
import json
import csv
from io import StringIO
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape():
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('urls'):
            return jsonify({'error': 'No URLs provided'}), 400
        
        # Initialize scraper with options
        scraper = WebScraper(
            delay=data.get('delay', 1.0),
            timeout=data.get('timeout', 10)
        )
        
        # Configure extraction
        config = {
            'extract_links': data.get('extractLinks', True),
            'extract_text': data.get('extractText', True),
            'extract_images': data.get('extractImages', True),
            'extract_tables': data.get('extractTables', True),
            'text_selector': data.get('textSelector')
        }
        
        # Scrape the URLs
        results = scraper.scrape_multiple_pages(data['urls'], config)
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/json', methods=['POST'])
def export_json():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Create a temporary file
    filename = f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join('temp', filename)
    
    # Ensure temp directory exists
    os.makedirs('temp', exist_ok=True)
    
    # Write JSON data
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return jsonify({'filename': filename})

@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Flatten the data for CSV
    flattened_data = []
    for item in data:
        flat_item = {
            'url': item['url'],
            'title': item['title'],
            'timestamp': item['timestamp'],
            'num_links': len(item.get('links', [])),
            'num_images': len(item.get('images', [])),
            'num_tables': len(item.get('tables', [])),
            'text_preview': ' '.join(item.get('text', []))[:200] + '...' if item.get('text') else ''
        }
        flattened_data.append(flat_item)
    
    # Create CSV string
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=flattened_data[0].keys())
    writer.writeheader()
    writer.writerows(flattened_data)
    csv_data = output.getvalue()
    
    # Create a temporary file
    filename = f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join('temp', filename)
    
    # Ensure temp directory exists
    os.makedirs('temp', exist_ok=True)
    
    # Write CSV data
    with open(filepath, 'w', newline='') as f:
        f.write(csv_data)
    
    return jsonify({'filename': filename})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('temp', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)