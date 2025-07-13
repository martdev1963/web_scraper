document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const scraperForm = document.getElementById('scraperForm');
    const clearBtn = document.getElementById('clearBtn');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsContainer = document.getElementById('resultsContainer');
    const successAlert = document.getElementById('successAlert');
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const exportJsonBtn = document.getElementById('exportJson');
    const exportCsvBtn = document.getElementById('exportCsv');

    // Close alert buttons
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });

    // Clear form
    clearBtn.addEventListener('click', function() {
        scraperForm.reset();
        resultsContainer.style.display = 'none';
        successAlert.style.display = 'none';
        errorAlert.style.display = 'none';
    });

    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all tabs and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(`${tabId}Tab`).classList.add('active');
        });
    });

    // Form submission
    scraperForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading indicator
        loadingIndicator.style.display = 'flex';
        resultsContainer.style.display = 'none';
        successAlert.style.display = 'none';
        errorAlert.style.display = 'none';
        
        // Get form data
        const formData = {
            urls: document.getElementById('urls').value.split('\n')
                .map(url => url.trim())
                .filter(url => url !== ''),
            extractLinks: document.getElementById('extractLinks').checked,
            extractText: document.getElementById('extractText').checked,
            extractImages: document.getElementById('extractImages').checked,
            extractTables: document.getElementById('extractTables').checked,
            textSelector: document.getElementById('textSelector').value || null,
            delay: parseFloat(document.getElementById('requestDelay').value) || 1.0,
            timeout: parseInt(document.getElementById('timeout').value) || 10
        };

        try {
            // Call backend API
            const response = await fetch('/api/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to scrape');
            }
            
            // Display results
            displayResults(data);
            successAlert.style.display = 'flex';
            resultsContainer.style.display = 'block';
            
        } catch (error) {
            console.error('Scraping error:', error);
            errorMessage.textContent = error.message;
            errorAlert.style.display = 'flex';
        } finally {
            loadingIndicator.style.display = 'none';
        }
    });

    // Export buttons
    exportJsonBtn.addEventListener('click', function() {
        // In a real implementation, this would download the JSON file
        alert('JSON export functionality would be implemented here');
    });

    exportCsvBtn.addEventListener('click', function() {
        // In a real implementation, this would download the CSV file
        alert('CSV export functionality would be implemented here');
    });

    // Function to display results
    function displayResults(data) {
        if (!data || data.length === 0) {
            document.getElementById('summaryTab').innerHTML = '<p>No data was scraped successfully.</p>';
            return;
        }

        // Display summary
        document.getElementById('summaryTab').innerHTML = `
            <h4>Scraping Summary</h4>
            <p>Successfully scraped ${data.length} page(s).</p>
            <div class="result-item">
                <div class="result-title">Summary Statistics</div>
                <div class="result-meta">
                    <span><i class="fas fa-link"></i> ${data.reduce((acc, page) => acc + (page.links ? page.links.length : 0), 0)} links found</span>
                    <span><i class="fas fa-image"></i> ${data.reduce((acc, page) => acc + (page.images ? page.images.length : 0), 0)} images found</span>
                    <span><i class="fas fa-table"></i> ${data.reduce((acc, page) => acc + (page.tables ? page.tables.length : 0), 0)} tables found</span>
                </div>
            </div>
            ${data.map(page => `
                <div class="result-item">
                    <div class="result-title">${page.title || 'Untitled Page'}</div>
                    <div class="result-url">${page.url}</div>
                    <div class="result-meta">
                        <span><i class="fas fa-clock"></i> ${new Date(page.timestamp).toLocaleString()}</span>
                        <span><i class="fas fa-link"></i> ${page.links ? page.links.length : 0} links</span>
                        <span><i class="fas fa-image"></i> ${page.images ? page.images.length : 0} images</span>
                        <span><i class="fas fa-table"></i> ${page.tables ? page.tables.length : 0} tables</span>
                    </div>
                </div>
            `).join('')}
        `;

        // Display links
        document.getElementById('linksTab').innerHTML = data.map(page => `
            <div class="result-item">
                <div class="result-title">Links from: ${page.title || 'Untitled Page'}</div>
                <div class="result-url">${page.url}</div>
                ${page.links && page.links.length > 0 ? `
                    <ul class="links-list">
                        ${page.links.map(link => `<li><a href="${link}" target="_blank" rel="noopener noreferrer">${link}</a></li>`).join('')}
                    </ul>
                ` : '<p>No links found on this page.</p>'}
            </div>
        `).join('');

        // Display text
        document.getElementById('textTab').innerHTML = data.map(page => `
            <div class="result-item">
                <div class="result-title">Text from: ${page.title || 'Untitled Page'}</div>
                <div class="result-url">${page.url}</div>
                ${page.text && page.text.length > 0 ? `
                    <div class="text-content">
                        ${page.text.map(text => `<p>${text}</p>`).join('')}
                    </div>
                ` : '<p>No text content found on this page.</p>'}
            </div>
        `).join('');

        // Display images
        document.getElementById('imagesTab').innerHTML = data.map(page => `
            <div class="result-item">
                <div class="result-title">Images from: ${page.title || 'Untitled Page'}</div>
                <div class="result-url">${page.url}</div>
                ${page.images && page.images.length > 0 ? `
                    <div class="image-grid">
                        ${page.images.map(image => `
                            <div class="image-item">
                                <img src="${image.url}" alt="${image.alt}" 
                                     onerror="this.src='https://via.placeholder.com/200x150?text=Image+Not+Available'">
                                <div class="image-info">
                                    <p><strong>Filename:</strong> ${image.filename}</p>
                                    <p><strong>Alt Text:</strong> ${image.alt || 'None'}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : '<p>No images found on this page.</p>'}
            </div>
        `).join('');

        // Display tables
        document.getElementById('tablesTab').innerHTML = data.map(page => `
            <div class="result-item">
                <div class="result-title">Tables from: ${page.title || 'Untitled Page'}</div>
                <div class="result-url">${page.url}</div>
                ${page.tables && page.tables.length > 0 ? `
                    ${page.tables.map((table, index) => `
                        <h5>Table ${index + 1}</h5>
                        <div class="table-container">
                            <table>
                                ${table.map((row, rowIndex) => `
                                    <tr>
                                        ${row.map(cell => `
                                            ${rowIndex === 0 ? `<th>${cell}</th>` : `<td>${cell}</td>`}
                                        `).join('')}
                                    </tr>
                                `).join('')}
                            </table>
                        </div>
                    `).join('')}
                ` : '<p>No tables found on this page.</p>'}
            </div>
        `).join('');
    }
});