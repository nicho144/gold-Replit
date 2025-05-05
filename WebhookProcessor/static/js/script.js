document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysis-form');
    const resultContainer = document.getElementById('result-container');
    const spinner = document.getElementById('loading-spinner');
    const errorAlert = document.getElementById('error-alert');
    
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Show spinner, hide results and errors
            spinner.classList.remove('d-none');
            resultContainer.classList.add('d-none');
            errorAlert.classList.add('d-none');
            
            // Get form data
            const formData = {
                ticker_front: document.getElementById('ticker-front').value,
                ticker_next: document.getElementById('ticker-next').value,
                physical_demand: document.getElementById('physical-demand').value,
                price_breakout: document.getElementById('price-breakout').checked
            };
            
            try {
                // Send API request
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
                
                // Hide spinner
                spinner.classList.add('d-none');
                
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                
                const data = await response.json();
                displayResults(data);
                
            } catch (error) {
                console.error('Error:', error);
                spinner.classList.add('d-none');
                errorAlert.textContent = `Error: ${error.message || 'Failed to analyze market data'}`;
                errorAlert.classList.remove('d-none');
            }
        });
    }
    
    function displayResults(data) {
        // Clear previous results
        resultContainer.innerHTML = '';
        
        // Create signal header with appropriate color
        const signalClass = data.signal.includes('BEARISH') ? 'text-danger' : 
                          data.signal.includes('BULLISH') ? 'text-success' : 'text-warning';
        
        const resultHTML = `
            <div class="card bg-dark border-secondary">
                <div class="card-header">
                    <h3 class="mb-0 ${signalClass}">${data.signal}</h3>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h4>Market Analysis</h4>
                            <ul class="list-group list-group-flush bg-transparent">
                                ${data.reasons.map(reason => `<li class="list-group-item bg-dark text-light border-secondary">${reason}</li>`).join('')}
                            </ul>
                            
                            <h4 class="mt-4">Recommendations</h4>
                            <ul class="list-group list-group-flush">
                                ${data.recommendations.map(rec => `<li class="list-group-item bg-dark text-light border-secondary">${rec}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card bg-dark border-secondary mb-3">
                                <div class="card-header">Contract Prices</div>
                                <div class="card-body">
                                    <div class="d-flex justify-content-between mb-2">
                                        <span>Front Contract:</span>
                                        <span class="fw-bold">${data.prices.front_contract}</span>
                                    </div>
                                    <div class="d-flex justify-content-between mb-2">
                                        <span>Next Contract:</span>
                                        <span class="fw-bold">${data.prices.next_contract}</span>
                                    </div>
                                    <div class="d-flex justify-content-between mb-2">
                                        <span>Contango Spread:</span>
                                        <span class="fw-bold">${data.prices.contango_spread}</span>
                                    </div>
                                    <div class="d-flex justify-content-between">
                                        <span>Contango %:</span>
                                        <span class="fw-bold">${data.prices.contango_percentage}%</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card bg-dark border-secondary">
                                <div class="card-header">Market Metrics</div>
                                <div class="card-body">
                                    <div class="d-flex justify-content-between mb-2">
                                        <span>Market Condition:</span>
                                        <span class="fw-bold">${data.market_condition || 'N/A'}</span>
                                    </div>
                                    <div class="d-flex justify-content-between mb-2">
                                        <span>Term Structure:</span>
                                        <span class="fw-bold">${data.term_structure || 'N/A'}</span>
                                    </div>
                                    <div class="d-flex justify-content-between">
                                        <span>Confidence Score:</span>
                                        <span class="fw-bold">${data.confidence_score || 'N/A'}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card-footer text-muted">
                    Analysis generated at: ${new Date(data.analysis_timestamp).toLocaleString() || new Date().toLocaleString()}
                </div>
            </div>
        `;
        
        resultContainer.innerHTML = resultHTML;
        resultContainer.classList.remove('d-none');
    }
    
    // Example data setup
    const exampleBtn = document.getElementById('example-data-btn');
    if (exampleBtn) {
        exampleBtn.addEventListener('click', function() {
            document.getElementById('ticker-front').value = 'GC=F';
            document.getElementById('ticker-next').value = 'GCM24.CMX';
            document.getElementById('physical-demand').value = 'declining';
            document.getElementById('price-breakout').checked = false;
        });
    }
});
