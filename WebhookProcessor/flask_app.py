import os
import logging
from flask import Flask, request, jsonify, render_template, json
from datetime import datetime
from models import MarketInput
from utils import analyze_futures_market
from market_data_utils import (
    get_premarket_data, 
    get_gold_term_structure, 
    get_interest_rate_impact,
    analyze_market_sentiment,
    detect_gold_cycle_thresholds,
    get_economic_expectations,
    get_comprehensive_analysis
)
from gold_futures_curve import get_gold_futures_curve

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Simple JSON date encoder function to be used within each route
def json_serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# Create Flask app for use with Gunicorn
app = Flask(__name__, 
    static_folder="static",
    template_folder="templates")

@app.route("/")
def flask_root():
    """Render the main frontend interface"""
    try:
        # Create a homepage with quicklinks to the main dashboard features
        # We'll pass some basic market data to display directly on the homepage
        
        # Get basic market data if possible
        try:
            # Import functions we need
            from fred_data_utils import get_real_interest_rates
            from market_data_utils import get_gold_term_structure_data
            enhanced_data = True
        except ImportError:
            enhanced_data = False
        
        homepage_data = {}
        
        if enhanced_data:
            try:
                # Get key market data for homepage display
                real_rates = get_real_interest_rates()
                if real_rates and "real_rates" in real_rates and "t10y" in real_rates["real_rates"]:
                    homepage_data["real_10y_rate"] = real_rates["real_rates"]["t10y"]
                
                gold_structure = get_gold_term_structure_data()
                if gold_structure and "prices" in gold_structure and "front_month" in gold_structure["prices"]:
                    homepage_data["gold_price"] = gold_structure["prices"]["front_month"].get("price", "N/A")
            except Exception as e:
                logger.warning(f"Error getting enhanced homepage data: {str(e)}")
        
        return render_template("index.html", homepage_data=homepage_data, enhanced_data=enhanced_data)
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route("/docs-custom")
def flask_custom_docs():
    """Render custom documentation page"""
    return render_template("documentation.html")

# API endpoints returning pure JSON data (for API consumers)
@app.route("/api/premarket")
def flask_premarket_api():
    """Get premarket data for major futures contracts (API endpoint)"""
    try:
        premarket_data = get_premarket_data()
        return jsonify(premarket_data)
    except Exception as e:
        logger.error(f"Error getting premarket data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/gold/term-structure")
def flask_gold_term_structure_api():
    """Analyze gold futures term structure (GC1, GC2, GC3) (API endpoint)"""
    try:
        term_structure_data = get_gold_term_structure()
        return jsonify(term_structure_data)
    except Exception as e:
        logger.error(f"Error analyzing gold term structure: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/interest-impact")
def flask_interest_impact_api():
    """Analyze impact of interest rates on gold prices (API endpoint)"""
    try:
        interest_impact_data = get_interest_rate_impact()
        return jsonify(interest_impact_data)
    except Exception as e:
        logger.error(f"Error analyzing interest rate impact: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/market-sentiment")
def flask_market_sentiment_api():
    """Analyze market sentiment and its impact on gold (API endpoint)"""
    try:
        sentiment_data = analyze_market_sentiment()
        return jsonify(sentiment_data)
    except Exception as e:
        logger.error(f"Error analyzing market sentiment: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/gold-cycle")
def flask_gold_cycle_api():
    """Detect potential gold cycle turning points (API endpoint)"""
    try:
        cycle_data = detect_gold_cycle_thresholds()
        return jsonify(cycle_data)
    except Exception as e:
        logger.error(f"Error detecting gold cycle thresholds: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/economic-expectations")
def flask_economic_expectations_api():
    """Analyze current economic expectations for gold (API endpoint)"""
    try:
        economic_data = get_economic_expectations()
        return jsonify(economic_data)
    except Exception as e:
        logger.error(f"Error analyzing economic expectations: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/comprehensive")
def flask_comprehensive_api():
    """Get comprehensive market analysis combining all indicators (API endpoint)"""
    try:
        comprehensive_data = get_comprehensive_analysis()
        return jsonify(comprehensive_data)
    except Exception as e:
        logger.error(f"Error generating comprehensive analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Web UI routes with templates
@app.route("/market/premarket")
def flask_premarket():
    """Get premarket data for major futures contracts (Web UI)"""
    try:
        premarket_data = get_premarket_data()
        return render_template(
            "market_data.html",
            title="Premarket Data",
            description="Latest premarket data for major futures contracts and indices",
            data=premarket_data,
            endpoint_type="premarket"
        )
    except Exception as e:
        logger.error(f"Error getting premarket data: {str(e)}")
        return render_template(
            "market_data.html",
            title="Premarket Data",
            description="Error fetching premarket data",
            data={"error": str(e), "timestamp": str(datetime.now())},
            endpoint_type="error"
        )

@app.route("/market/gold/term-structure")
def flask_gold_term_structure():
    """Analyze gold futures term structure (GC1, GC2, GC3) (Web UI)"""
    try:
        term_structure_data = get_gold_term_structure()
        
        # Prepare formatted data for the template
        formatted_data = "<div class='row mb-4'>"
        
        # Show front-month futures price
        formatted_data += "<div class='col-md-4'>"
        formatted_data += "<div class='card bg-dark border-secondary h-100'>"
        formatted_data += "<div class='card-header'><h5>Front Month (GC1)</h5></div>"
        formatted_data += "<div class='card-body'>"
        front_month = term_structure_data.get('prices', {}).get('front_month', {})
        price = front_month.get('price', 'N/A')
        contract = front_month.get('contract', 'N/A')
        formatted_data += f"<p><strong>Contract:</strong> {contract}</p>"
        formatted_data += f"<p><strong>Price:</strong> <span class='data-value'>${price}</span></p>"
        formatted_data += "</div></div></div>"
        
        # Show second-month futures price
        formatted_data += "<div class='col-md-4'>"
        formatted_data += "<div class='card bg-dark border-secondary h-100'>"
        formatted_data += "<div class='card-header'><h5>Second Month (GC2)</h5></div>"
        formatted_data += "<div class='card-body'>"
        second_month = term_structure_data.get('prices', {}).get('second_month', {})
        price = second_month.get('price', 'N/A') 
        contract = second_month.get('contract', 'N/A')
        formatted_data += f"<p><strong>Contract:</strong> {contract}</p>"
        formatted_data += f"<p><strong>Price:</strong> <span class='data-value'>${price}</span></p>"
        formatted_data += "</div></div></div>"
        
        # Show third-month futures price
        formatted_data += "<div class='col-md-4'>"
        formatted_data += "<div class='card bg-dark border-secondary h-100'>"
        formatted_data += "<div class='card-header'><h5>Third Month (GC3)</h5></div>"
        formatted_data += "<div class='card-body'>"
        third_month = term_structure_data.get('prices', {}).get('third_month', {})
        price = third_month.get('price', 'N/A')
        contract = third_month.get('contract', 'N/A')
        formatted_data += f"<p><strong>Contract:</strong> {contract}</p>"
        formatted_data += f"<p><strong>Price:</strong> <span class='data-value'>${price}</span></p>"
        formatted_data += "</div></div></div>"
        
        formatted_data += "</div>"  # End of row
        
        # Show spread data
        formatted_data += "<div class='row mb-4'>"
        formatted_data += "<div class='col-md-6'>"
        formatted_data += "<div class='card bg-dark border-secondary'>"
        formatted_data += "<div class='card-header'><h5>Term Structure Spreads</h5></div>"
        formatted_data += "<div class='card-body'>"
        
        # Get spread data
        spreads = term_structure_data.get('spreads', {})
        gc1_gc2 = spreads.get('gc1_gc2', 0)
        gc2_gc3 = spreads.get('gc2_gc3', 0)
        
        # Format spreads with color coding
        gc1_gc2_class = "data-positive" if gc1_gc2 > 0 else "data-negative"
        gc2_gc3_class = "data-positive" if gc2_gc3 > 0 else "data-negative"
        
        formatted_data += f"<p><strong>GC1-GC2 Spread:</strong> <span class='data-value {gc1_gc2_class}'>${abs(gc1_gc2)}</span> ({'Contango' if gc1_gc2 < 0 else 'Backwardation'})</p>"
        formatted_data += f"<p><strong>GC2-GC3 Spread:</strong> <span class='data-value {gc2_gc3_class}'>${abs(gc2_gc3)}</span> ({'Contango' if gc2_gc3 < 0 else 'Backwardation'})</p>"
        formatted_data += "</div></div></div>"
        
        # Show structure implications
        formatted_data += "<div class='col-md-6'>"
        formatted_data += "<div class='card bg-dark border-secondary'>"
        formatted_data += "<div class='card-header'><h5>Market Implications</h5></div>"
        formatted_data += "<div class='card-body'>"
        formatted_data += f"<p>{term_structure_data.get('analysis', {}).get('implication', 'No implications available.')}</p>"
        formatted_data += "</div></div></div>"
        formatted_data += "</div>"  # End of row
        
        # Add explanation of term structure
        formatted_data += "<div class='row mb-4'>"
        formatted_data += "<div class='col-12'>"
        formatted_data += "<div class='card bg-dark border-secondary'>"
        formatted_data += "<div class='card-header'><h5>Understanding Gold Futures Term Structure</h5></div>"
        formatted_data += "<div class='card-body'>"
        formatted_data += "<p>The term structure of gold futures shows the relationship between near-term and longer-term contract prices.</p>"
        formatted_data += "<ul>"
        formatted_data += "<li><strong>Contango:</strong> When longer-dated futures are priced higher than shorter-dated futures. This is the normal state for gold markets due to storage costs and interest rates.</li>"
        formatted_data += "<li><strong>Backwardation:</strong> When shorter-dated futures are priced higher than longer-dated futures. This is unusual for gold and often signals strong immediate demand or supply shortages.</li>"
        formatted_data += "</ul>"
        formatted_data += "<p>Changes in term structure can provide early signals about shifts in market sentiment and physical demand dynamics.</p>"
        formatted_data += "</div></div></div></div>"
        
        # Add open interest section
        oi_data = term_structure_data.get('open_interest', {})
        if oi_data:
            formatted_data += "<div class='row mb-4'>"
            formatted_data += "<div class='col-12'>"
            formatted_data += "<div class='card bg-dark border-secondary'>"
            formatted_data += "<div class='card-header'><h5>Open Interest Analysis</h5></div>"
            formatted_data += "<div class='card-body'>"
            formatted_data += "<div class='row'>"
            
            # Front month OI
            formatted_data += "<div class='col-md-4'>"
            front_oi = oi_data.get('front_month_oi', 'N/A')
            front_oi_change = oi_data.get('front_month_oi_change', 0)
            oi_change_class = "data-positive" if front_oi_change > 0 else "data-negative"
            
            formatted_data += f"<p><strong>Front Month OI:</strong> {front_oi}</p>"
            formatted_data += f"<p><strong>Change:</strong> <span class='{oi_change_class}'>{front_oi_change}%</span></p>"
            formatted_data += "</div>"
            
            # Exhaustion signal
            formatted_data += "<div class='col-md-8'>"
            signal = oi_data.get('exhaustion_signal', 'None detected')
            signal_class = "data-negative" if "bearish" in signal.lower() else "data-positive"
            
            formatted_data += f"<p><strong>Potential Exhaustion Signal:</strong> <span class='{signal_class}'>{signal}</span></p>"
            formatted_data += f"<p>{oi_data.get('signal_explanation', '')}</p>"
            formatted_data += "</div>"
            
            formatted_data += "</div></div></div></div></div>"  # End of OI section
        
        return render_template(
            "market_data.html",
            title="Gold Term Structure",
            description="Analysis of gold futures term structure (contango/backwardation)",
            data=term_structure_data,
            formatted_data=formatted_data,
            endpoint_type="term_structure"
        )
    except Exception as e:
        logger.error(f"Error analyzing gold term structure: {str(e)}")
        return render_template(
            "market_data.html",
            title="Gold Term Structure",
            description="Error analyzing gold term structure",
            data={"error": str(e), "timestamp": str(datetime.now())},
            endpoint_type="error"
        )

@app.route("/market/real-rates")
def flask_real_rates():
    """Analyze real interest rates and their impact on gold (Web UI)"""
    try:
        # Import here to avoid circular imports
        from fred_data_utils import get_real_interest_rates
        
        # Get real interest rates data from FRED
        fred_data = get_real_interest_rates()
        
        # Prepare data for template
        formatted_data = "<div class='row mb-4'>"
        
        # 10-year section
        formatted_data += "<div class='col-md-4'>"
        formatted_data += "<div class='card bg-dark border-secondary h-100'>"
        formatted_data += "<div class='card-header'><h5>10-Year Treasury</h5></div>"
        formatted_data += "<div class='card-body'>"
        formatted_data += f"<p><strong>Nominal Rate:</strong> <span class='data-value'>{fred_data['nominal_rates'].get('t10y', 'N/A')}%</span></p>"
        formatted_data += f"<p><strong>Inflation Expectation:</strong> <span class='data-value'>{fred_data['inflation_expectations'].get('t10y', 'N/A')}%</span></p>"
        
        t10y_real = fred_data['real_rates'].get('t10y', 0)
        real_rate_class = "data-negative" if t10y_real < 0 else "data-positive"
        formatted_data += f"<p><strong>Real Rate:</strong> <span class='data-value {real_rate_class}'>{t10y_real}%</span></p>"
        formatted_data += "</div></div></div>"
        
        # 5-year section
        formatted_data += "<div class='col-md-4'>"
        formatted_data += "<div class='card bg-dark border-secondary h-100'>"
        formatted_data += "<div class='card-header'><h5>5-Year Treasury</h5></div>"
        formatted_data += "<div class='card-body'>"
        formatted_data += f"<p><strong>Nominal Rate:</strong> <span class='data-value'>{fred_data['nominal_rates'].get('t5y', 'N/A')}%</span></p>"
        formatted_data += f"<p><strong>Inflation Expectation:</strong> <span class='data-value'>{fred_data['inflation_expectations'].get('t5y', 'N/A')}%</span></p>"
        
        t5y_real = fred_data['real_rates'].get('t5y', 0)
        real_rate_class = "data-negative" if t5y_real < 0 else "data-positive"
        formatted_data += f"<p><strong>Real Rate:</strong> <span class='data-value {real_rate_class}'>{t5y_real}%</span></p>"
        formatted_data += "</div></div></div>"
        
        # 2-year section
        formatted_data += "<div class='col-md-4'>"
        formatted_data += "<div class='card bg-dark border-secondary h-100'>"
        formatted_data += "<div class='card-header'><h5>2-Year Treasury</h5></div>"
        formatted_data += "<div class='card-body'>"
        formatted_data += f"<p><strong>Nominal Rate:</strong> <span class='data-value'>{fred_data['nominal_rates'].get('t2y', 'N/A')}%</span></p>"
        formatted_data += f"<p><strong>Inflation Expectation:</strong> <span class='data-value'>{fred_data['inflation_expectations'].get('t2y', 'N/A')}%</span></p>"
        
        t2y_real = fred_data['real_rates'].get('t2y', 0)
        real_rate_class = "data-negative" if t2y_real < 0 else "data-positive"
        formatted_data += f"<p><strong>Real Rate:</strong> <span class='data-value {real_rate_class}'>{t2y_real}%</span></p>"
        formatted_data += "</div></div></div>"
        
        formatted_data += "</div>"  # End of row
        
        # Add market implications
        formatted_data += "<div class='row mb-4'>"
        formatted_data += "<div class='col-12'>"
        formatted_data += "<div class='card bg-dark border-secondary'>"
        formatted_data += "<div class='card-header'><h5>Market Implications</h5></div>"
        formatted_data += "<div class='card-body'>"
        formatted_data += f"<p class='mb-0'>{fred_data['analysis'].get('implication', '')}</p>"
        formatted_data += "</div></div></div></div>"
        
        # Add explanation of real rates
        formatted_data += "<div class='row mb-4'>"
        formatted_data += "<div class='col-12'>"
        formatted_data += "<div class='card bg-dark border-secondary'>"
        formatted_data += "<div class='card-header'><h5>Understanding Real Interest Rates</h5></div>"
        formatted_data += "<div class='card-body'>"
        formatted_data += "<p>Real interest rates represent the actual return on investment after accounting for inflation.</p>"
        formatted_data += "<p><strong>Calculation:</strong> Real Rate = Nominal Rate - Expected Inflation Rate</p>"
        formatted_data += "<ul>"
        formatted_data += "<li><strong>Positive real rates:</strong> Investors earn a return higher than inflation, often negative for gold prices.</li>"
        formatted_data += "<li><strong>Negative real rates:</strong> Cash loses purchasing power over time, often positive for gold prices.</li>"
        formatted_data += "</ul>"
        formatted_data += "<p>When real rates are negative, the opportunity cost of holding gold (which pays no interest) is reduced or eliminated, making gold more attractive as a store of value.</p>"
        formatted_data += "</div></div></div></div>"
        
        # Add data source
        formatted_data += "<div class='row'>"
        formatted_data += "<div class='col-12'>"
        formatted_data += "<div class='card bg-dark border-secondary'>"
        formatted_data += "<div class='card-header'><h5>Data Source</h5></div>"
        formatted_data += "<div class='card-body'>"
        formatted_data += f"<p class='mb-0'>{fred_data.get('data_source', 'Federal Reserve Economic Data (FRED)')}</p>"
        formatted_data += "</div></div></div></div>"
        
        return render_template(
            "market_data.html",
            title="Real Interest Rates Analysis",
            description="Real rates = Nominal yields - Inflation expectations",
            data=fred_data,
            formatted_data=formatted_data,
            real_rates={
                "nominal_rate": fred_data['nominal_rates'].get('t10y', 0),
                "inflation_expectation": fred_data['inflation_expectations'].get('t10y', 0),
                "real_rate": fred_data['real_rates'].get('t10y', 0),
                "implication": fred_data['analysis'].get('implication', '')
            },
            endpoint_type="real_rates"
        )
    except Exception as e:
        logger.error(f"Error analyzing real interest rates: {str(e)}")
        return render_template(
            "market_data.html",
            title="Real Interest Rates",
            description="Error analyzing real interest rates",
            data={"error": str(e), "timestamp": str(datetime.now())},
            endpoint_type="error"
        )

@app.route("/market/sentiment")
def flask_market_sentiment():
    """Analyze market sentiment and its impact on gold (Web UI)"""
    try:
        sentiment_data = analyze_market_sentiment()
        # Add timestamp if not present
        if 'timestamp' not in sentiment_data:
            sentiment_data['timestamp'] = str(datetime.now())
            
        # Flatten the nested data structure to match the template expectations
        flattened_data = {
            'timestamp': sentiment_data.get('timestamp', str(datetime.now())),
            'gold_price': sentiment_data.get('current_data', {}).get('gold_price', '--'),
            'gold_change_pct': sentiment_data.get('current_data', {}).get('gold_30d_change_pct', 0),
            'vix': sentiment_data.get('current_data', {}).get('vix', '--'),
            'vix_change_pct': sentiment_data.get('current_data', {}).get('vix_30d_change_pct', 0),
            'market_sentiment': sentiment_data.get('analysis', {}).get('vix_implication', 'Data not available'),
            'gold_outlook': sentiment_data.get('analysis', {}).get('gold_vix_relationship', 'Data not available'),
            'volatility_trend': sentiment_data.get('analysis', {}).get('vix_level', 'Data not available'),
            'correlation_coefficient': sentiment_data.get('correlation', {}).get('correlation_30d', '--'),
            'correlation_interpretation': sentiment_data.get('analysis', {}).get('market_implication', 'Data not available'),
            'implications': []
        }
        
        # Add implications if available
        if 'market_implication' in sentiment_data.get('analysis', {}):
            flattened_data['implications'] = [sentiment_data['analysis']['market_implication']]
        
        return render_template(
            "market_sentiment.html",
            data=flattened_data
        )
    except Exception as e:
        logger.error(f"Error analyzing market sentiment: {str(e)}")
        return render_template(
            "market_sentiment.html",
            data={"error": str(e), "timestamp": str(datetime.now())}
        )

@app.route("/market/gold-cycle")
def flask_gold_cycle():
    """Detect potential gold cycle turning points (Web UI)"""
    try:
        cycle_data = detect_gold_cycle_thresholds()
        # Add timestamp if not present
        if 'timestamp' not in cycle_data:
            cycle_data['timestamp'] = str(datetime.now())
            
        # Flatten the nested data structure to match the template expectations
        flattened_data = {
            'timestamp': cycle_data.get('timestamp', str(datetime.now())),
            'price_data': {
                'current': cycle_data.get('current_data', {}).get('current_price', '--'),
                'change_pct': cycle_data.get('current_data', {}).get('pct_from_52w_low', 0)
            },
            'cycle_position': cycle_data.get('cycle_analysis', {}).get('cycle_position', '--'),
            'cycle_description': cycle_data.get('cycle_analysis', {}).get('risk_level', 'Data not available'),
            'cycle_analysis': cycle_data.get('cycle_analysis', {}).get('action_recommendation', 'Data not available'),
            'implications': [cycle_data.get('cycle_analysis', {}).get('action_recommendation', 'Data not available')],
            'indicators': [],
            'thresholds': []
        }
        
        # Add technical indicators
        if 'technical_metrics' in cycle_data:
            metrics = cycle_data['technical_metrics']
            
            if 'rsi_14' in metrics:
                signal = 'overbought' if metrics['rsi_14'] > 70 else 'oversold' if metrics['rsi_14'] < 30 else 'neutral'
                flattened_data['indicators'].append({
                    'name': 'RSI (14)',
                    'value': metrics['rsi_14'],
                    'signal': 'bullish' if signal == 'oversold' else 'bearish' if signal == 'overbought' else 'neutral'
                })
                
            if 'ma50' in metrics and 'ma200' in metrics:
                ma_signal = 'bullish' if metrics['ma50'] > metrics['ma200'] else 'bearish'
                flattened_data['indicators'].append({
                    'name': 'MA50/MA200 Crossover',
                    'value': metrics.get('ma_ratio', 1.0),
                    'signal': ma_signal
                })
        
        # Add support/resistance thresholds  
        if 'current_data' in cycle_data:
            current_data = cycle_data['current_data']
            current_price = current_data.get('current_price', 0)
            
            if 'price_52w_high' in current_data:
                flattened_data['thresholds'].append({
                    'type': 'resistance (52-week high)',
                    'price': current_data['price_52w_high'],
                    'distance': current_data.get('pct_from_52w_high', 0)
                })
                
            if 'price_52w_low' in current_data:
                flattened_data['thresholds'].append({
                    'type': 'support (52-week low)',
                    'price': current_data['price_52w_low'],
                    'distance': current_data.get('pct_from_52w_low', 0)
                })
                
            # Add technical levels as thresholds if available
            if 'technical_metrics' in cycle_data:
                metrics = cycle_data['technical_metrics']
                
                if 'ma200' in metrics:
                    distance = ((current_price / metrics['ma200']) - 1) * 100
                    flattened_data['thresholds'].append({
                        'type': 'support/resistance (MA200)',
                        'price': metrics['ma200'],
                        'distance': distance
                    })
                    
                if 'ma50' in metrics:
                    distance = ((current_price / metrics['ma50']) - 1) * 100
                    flattened_data['thresholds'].append({
                        'type': 'support/resistance (MA50)',
                        'price': metrics['ma50'],
                        'distance': distance
                    })
        
        return render_template(
            "gold_cycle.html",
            data=flattened_data
        )
    except Exception as e:
        logger.error(f"Error detecting gold cycle thresholds: {str(e)}")
        return render_template(
            "gold_cycle.html",
            data={"error": str(e), "timestamp": str(datetime.now())}
        )

@app.route("/market/economic")
def flask_economic_expectations():
    """Analyze current economic expectations for gold (Web UI)"""
    try:
        economic_data = get_economic_expectations()
        # Add timestamp if not present
        if 'timestamp' not in economic_data:
            economic_data['timestamp'] = str(datetime.now())
            
        # Flatten the nested data structure to match the template expectations
        flattened_data = {
            'timestamp': economic_data.get('timestamp', str(datetime.now())),
            'indicators': [],
            'economic_climate': 'Data not available',
            'central_bank_outlook': 'Data not available',
            'inflation_expectations': 'Data not available',
            'gold_implications': [],
            'forecasts': []
        }
        
        # Add yield curve data to indicators
        if 'yield_curve' in economic_data:
            yield_curve = economic_data['yield_curve']
            
            if 't13w' in yield_curve:
                flattened_data['indicators'].append({
                    'name': '13-Week Treasury',
                    'value': f"{yield_curve['t13w']}%",
                    'change': 0,  # No change data in the original structure
                    'impact': 'Short-term interest rate indicator'
                })
                
            if 't10y' in yield_curve:
                flattened_data['indicators'].append({
                    'name': '10-Year Treasury',
                    'value': f"{yield_curve['t10y']}%",
                    'change': 0,  # No change data in the original structure
                    'impact': 'Benchmark interest rate'
                })
                
            if 't10y_t13w_spread' in yield_curve:
                flattened_data['indicators'].append({
                    'name': '10Y-3M Spread',
                    'value': f"{yield_curve['t10y_t13w_spread']}%",
                    'change': 0,  # No change data in the original structure
                    'impact': 'Recession indicator'
                })
        
        # Add economic outlook information
        if 'economic_outlook' in economic_data:
            outlook = economic_data['economic_outlook']
            
            if 'yield_curve_shape' in outlook and 'recession_signal' in outlook:
                flattened_data['economic_climate'] = f"Yield Curve: {outlook['yield_curve_shape']}. {outlook['recession_signal']}."
                
            if 'gold_implication' in outlook:
                flattened_data['gold_implications'].append(outlook['gold_implication'])
        
        # Add inflation expectations
        if 'inflation_expectations' in economic_data and 'long_term_view' in economic_data['inflation_expectations']:
            flattened_data['inflation_expectations'] = economic_data['inflation_expectations']['long_term_view']
            
        # Add a simple forecast based on the data
        if 'economic_outlook' in economic_data and 'recession_signal' in economic_data['economic_outlook']:
            recession_signal = economic_data['economic_outlook']['recession_signal']
            
            if 'Elevated' in recession_signal:
                recession_prob = 60
                forecast_desc = "Economic slowdown likely in the next 6-12 months"
                gold_impact = "positive" # Safe haven demand
            elif 'Moderate' in recession_signal:
                recession_prob = 40
                forecast_desc = "Some risk of economic slowdown in the next 12 months"
                gold_impact = "neutral"
            else:
                recession_prob = 20
                forecast_desc = "Continued economic growth expected"
                gold_impact = "negative" # Less safe haven demand
                
            flattened_data['forecasts'].append({
                'name': 'Recession Risk',
                'description': forecast_desc,
                'probability': recession_prob,
                'gold_impact': gold_impact
            })
        
        return render_template(
            "economic_outlook.html",
            data=flattened_data
        )
    except Exception as e:
        logger.error(f"Error analyzing economic expectations: {str(e)}")
        return render_template(
            "economic_outlook.html",
            data={"error": str(e), "timestamp": str(datetime.now())}
        )

@app.route("/market/gold/integrated-analysis")
def flask_gold_integrated_analysis():
    """Get integrated gold market analysis (Web UI)"""
    try:
        # Import the advanced market analysis module
        try:
            from advanced_market_analysis import get_integrated_gold_analysis
            advanced_analysis_available = True
        except ImportError:
            logger.warning("Advanced market analysis module not available")
            advanced_analysis_available = False
        
        if advanced_analysis_available:
            # Get integrated gold analysis
            analysis_data = get_integrated_gold_analysis()
            
            return render_template(
                "gold_analysis.html",
                title="Integrated Gold Market Analysis",
                data=analysis_data
            )
        else:
            return render_template(
                "market_data.html",
                title="Gold Market Analysis",
                description="Error: Advanced market analysis module not available",
                data={"error": "Advanced market analysis module not available"},
                endpoint_type="error"
            )
    except Exception as e:
        logger.error(f"Error generating integrated gold analysis: {str(e)}")
        return render_template(
            "market_data.html",
            title="Gold Market Analysis",
            description="Error generating integrated gold analysis",
            data={"error": str(e), "timestamp": str(datetime.now())},
            endpoint_type="error"
        )

@app.route("/market/macroeconomic")
def flask_macroeconomic():
    """Get macroeconomic indicators dashboard (Web UI)"""
    try:
        # Import the macroeconomic indicators module
        try:
            from macroeconomic_indicators import get_comprehensive_macro_dashboard
            macro_available = True
        except ImportError:
            logger.warning("Macroeconomic indicators module not available")
            macro_available = False
        
        if macro_available:
            # Get comprehensive macroeconomic data
            macro_data = get_comprehensive_macro_dashboard()
            
            # Format the data for display
            formatted_data = "<div class='row mb-4'>"
            
            # Interest Rates Section
            if "interest_rates" in macro_data:
                formatted_data += "<div class='col-12 mb-4'>"
                formatted_data += "<div class='card bg-dark border-secondary'>"
                formatted_data += "<div class='card-header'><h4>Interest Rates</h4></div>"
                formatted_data += "<div class='card-body'>"
                
                # Display key interest rates
                formatted_data += "<div class='row'>"
                
                if "rates" in macro_data["interest_rates"]:
                    for series_id, rate_info in macro_data["interest_rates"]["rates"].items():
                        formatted_data += "<div class='col-md-3 mb-3'>"
                        formatted_data += f"<p><strong>{rate_info.get('name', series_id)}:</strong> <span class='data-value'>{rate_info.get('value', 'N/A')}%</span></p>"
                        formatted_data += "</div>"
                
                formatted_data += "</div>"  # End of rates row
                
                # Display key spreads
                formatted_data += "<div class='row mt-3'>"
                formatted_data += "<div class='col-12'>"
                formatted_data += "<h5>Yield Spreads</h5>"
                formatted_data += "</div>"
                
                if "spreads" in macro_data["interest_rates"]:
                    for spread_id, spread_info in macro_data["interest_rates"]["spreads"].items():
                        value = spread_info.get('value', 0)
                        spread_class = "data-positive" if value > 0 else "data-negative"
                        
                        formatted_data += "<div class='col-md-4 mb-3'>"
                        formatted_data += f"<p><strong>{spread_info.get('name', spread_id)}:</strong> <span class='data-value {spread_class}'>{value}%</span></p>"
                        formatted_data += "</div>"
                
                formatted_data += "</div>"  # End of spreads row
                
                # Add analysis
                if "analysis" in macro_data["interest_rates"]:
                    formatted_data += "<div class='row mt-3'>"
                    formatted_data += "<div class='col-12'>"
                    formatted_data += "<h5>Analysis</h5>"
                    
                    for key, value in macro_data["interest_rates"]["analysis"].items():
                        formatted_data += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
                    
                    formatted_data += "</div>"
                    formatted_data += "</div>"  # End of analysis row
                
                formatted_data += "</div></div></div>"  # End of interest rates section
            
            # Inflation Section
            if "inflation" in macro_data:
                formatted_data += "<div class='col-12 mb-4'>"
                formatted_data += "<div class='card bg-dark border-secondary'>"
                formatted_data += "<div class='card-header'><h4>Inflation</h4></div>"
                formatted_data += "<div class='card-body'>"
                
                # Current inflation metrics
                if "current" in macro_data["inflation"]:
                    formatted_data += "<div class='row'>"
                    formatted_data += "<div class='col-12'>"
                    formatted_data += "<h5>Current Inflation Metrics</h5>"
                    formatted_data += "</div>"
                    
                    for series_id, info in macro_data["inflation"]["current"].items():
                        yoy_change = info.get("yoy_change")
                        change_class = ""
                        
                        if yoy_change is not None:
                            change_class = "data-positive" if yoy_change < 2.0 else "data-negative" if yoy_change > 3.0 else "data-neutral"
                        
                        formatted_data += "<div class='col-md-6 mb-3'>"
                        formatted_data += f"<p><strong>{info.get('name', series_id)}:</strong> {info.get('value', 'N/A')}</p>"
                        
                        if yoy_change is not None:
                            formatted_data += f"<p><strong>Year-over-Year Change:</strong> <span class='{change_class}'>{yoy_change}%</span></p>"
                        
                        formatted_data += "</div>"
                    
                    formatted_data += "</div>"  # End of current inflation row
                
                # Inflation expectations
                if "expectations" in macro_data["inflation"]:
                    formatted_data += "<div class='row mt-3'>"
                    formatted_data += "<div class='col-12'>"
                    formatted_data += "<h5>Inflation Expectations</h5>"
                    formatted_data += "</div>"
                    
                    for series_id, info in macro_data["inflation"]["expectations"].items():
                        value = info.get("value", 0)
                        value_class = "data-positive" if value < 2.0 else "data-negative" if value > 3.0 else "data-neutral"
                        
                        formatted_data += "<div class='col-md-6 mb-3'>"
                        formatted_data += f"<p><strong>{info.get('name', series_id)}:</strong> <span class='{value_class}'>{value}%</span></p>"
                        formatted_data += "</div>"
                    
                    formatted_data += "</div>"  # End of inflation expectations row
                
                # Add analysis
                if "analysis" in macro_data["inflation"]:
                    formatted_data += "<div class='row mt-3'>"
                    formatted_data += "<div class='col-12'>"
                    formatted_data += "<h5>Analysis</h5>"
                    
                    for key, value in macro_data["inflation"]["analysis"].items():
                        formatted_data += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
                    
                    formatted_data += "</div>"
                    formatted_data += "</div>"  # End of analysis row
                
                formatted_data += "</div></div></div>"  # End of inflation section
            
            # Economic Growth Section
            if "economic_growth" in macro_data:
                formatted_data += "<div class='col-12 mb-4'>"
                formatted_data += "<div class='card bg-dark border-secondary'>"
                formatted_data += "<div class='card-header'><h4>Economic Growth</h4></div>"
                formatted_data += "<div class='card-body'>"
                
                # Key economic indicators
                if "indicators" in macro_data["economic_growth"]:
                    formatted_data += "<div class='row'>"
                    
                    for series_id, info in macro_data["economic_growth"]["indicators"].items():
                        formatted_data += "<div class='col-md-6 mb-3'>"
                        formatted_data += f"<p><strong>{info.get('name', series_id)}:</strong> {info.get('value', 'N/A')}</p>"
                        
                        # Add change metrics if available
                        if "qoq_change" in info:
                            change_class = "data-positive" if info["qoq_change"] > 0 else "data-negative"
                            formatted_data += f"<p><strong>QoQ Change:</strong> <span class='{change_class}'>{info['qoq_change']}%</span></p>"
                        
                        if "yoy_change" in info:
                            change_class = "data-positive" if info["yoy_change"] > 0 else "data-negative"
                            formatted_data += f"<p><strong>YoY Change:</strong> <span class='{change_class}'>{info['yoy_change']}%</span></p>"
                        
                        if "mom_change" in info:
                            change_class = "data-positive" if info["mom_change"] > 0 else "data-negative"
                            formatted_data += f"<p><strong>MoM Change:</strong> <span class='{change_class}'>{info['mom_change']}</span></p>"
                        
                        formatted_data += "</div>"
                    
                    formatted_data += "</div>"  # End of indicators row
                
                # Add analysis
                if "analysis" in macro_data["economic_growth"]:
                    formatted_data += "<div class='row mt-3'>"
                    formatted_data += "<div class='col-12'>"
                    formatted_data += "<h5>Analysis</h5>"
                    
                    for key, value in macro_data["economic_growth"]["analysis"].items():
                        formatted_data += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
                    
                    formatted_data += "</div>"
                    formatted_data += "</div>"  # End of analysis row
                
                formatted_data += "</div></div></div>"  # End of economic growth section
            
            # Dollar Strength Section
            if "dollar_strength" in macro_data:
                formatted_data += "<div class='col-12 mb-4'>"
                formatted_data += "<div class='card bg-dark border-secondary'>"
                formatted_data += "<div class='card-header'><h4>Dollar Strength</h4></div>"
                formatted_data += "<div class='card-body'>"
                
                # Dollar indexes
                if "indexes" in macro_data["dollar_strength"]:
                    formatted_data += "<div class='row'>"
                    
                    for series_id, info in macro_data["dollar_strength"]["indexes"].items():
                        formatted_data += "<div class='col-md-6 mb-3'>"
                        formatted_data += f"<p><strong>{info.get('name', series_id)}:</strong> {info.get('value', 'N/A')}</p>"
                        
                        # Add change metrics if available
                        if "mom_change" in info:
                            change_class = "data-positive" if info["mom_change"] < 0 else "data-negative"
                            formatted_data += f"<p><strong>MoM Change:</strong> <span class='{change_class}'>{info['mom_change']}%</span></p>"
                        
                        if "yoy_change" in info:
                            change_class = "data-positive" if info["yoy_change"] < 0 else "data-negative"
                            formatted_data += f"<p><strong>YoY Change:</strong> <span class='{change_class}'>{info['yoy_change']}%</span></p>"
                        
                        formatted_data += "</div>"
                    
                    formatted_data += "</div>"  # End of indexes row
                
                # Add analysis
                if "analysis" in macro_data["dollar_strength"]:
                    formatted_data += "<div class='row mt-3'>"
                    formatted_data += "<div class='col-12'>"
                    formatted_data += "<h5>Analysis</h5>"
                    
                    for key, value in macro_data["dollar_strength"]["analysis"].items():
                        formatted_data += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
                    
                    formatted_data += "</div>"
                    formatted_data += "</div>"  # End of analysis row
                
                formatted_data += "</div></div></div>"  # End of dollar strength section
            
            # Combined Analysis Section
            if "combined_analysis" in macro_data:
                formatted_data += "<div class='col-12 mb-4'>"
                formatted_data += "<div class='card bg-dark border-secondary'>"
                formatted_data += "<div class='card-header'><h4>Gold Market Implications</h4></div>"
                formatted_data += "<div class='card-body'>"
                
                # Overall bias
                if "overall_gold_bias" in macro_data["combined_analysis"]:
                    overall_bias = macro_data["combined_analysis"]["overall_gold_bias"]
                    bias_class = "data-positive" if "Bullish" in overall_bias else "data-negative" if "Bearish" in overall_bias else "data-neutral"
                    
                    formatted_data += f"<h3 class='{bias_class} mb-4'>{overall_bias}</h3>"
                
                # Factor counts
                bullish = macro_data["combined_analysis"].get("bullish_factors", 0)
                bearish = macro_data["combined_analysis"].get("bearish_factors", 0)
                neutral = macro_data["combined_analysis"].get("neutral_factors", 0)
                total = macro_data["combined_analysis"].get("total_factors", 0)
                
                if total > 0:
                    formatted_data += "<div class='d-flex justify-content-between mb-4'>"
                    formatted_data += f"<div><span class='badge bg-success'>Bullish: {bullish}/{total}</span></div>"
                    formatted_data += f"<div><span class='badge bg-warning'>Neutral: {neutral}/{total}</span></div>"
                    formatted_data += f"<div><span class='badge bg-danger'>Bearish: {bearish}/{total}</span></div>"
                    formatted_data += "</div>"
                
                # Factor details
                if "gold_implications" in macro_data["combined_analysis"]:
                    formatted_data += "<h5>Factor Breakdown</h5>"
                    formatted_data += "<table class='table table-dark table-striped'>"
                    formatted_data += "<thead><tr><th>Factor</th><th>Implication</th></tr></thead>"
                    formatted_data += "<tbody>"
                    
                    for implication in macro_data["combined_analysis"]["gold_implications"]:
                        factor = implication.get("factor", "")
                        impact = implication.get("implication", "")
                        impact_class = "text-success" if "bullish" in impact.lower() else "text-danger" if "bearish" in impact.lower() else "text-warning"
                        
                        formatted_data += f"<tr><td>{factor}</td><td class='{impact_class}'>{impact}</td></tr>"
                    
                    formatted_data += "</tbody></table>"
                
                formatted_data += "</div></div></div>"  # End of combined analysis section
            
            # Data Source Section
            formatted_data += "<div class='row'>"
            formatted_data += "<div class='col-12'>"
            formatted_data += "<div class='card bg-dark border-secondary'>"
            formatted_data += "<div class='card-header'><h5>Data Source</h5></div>"
            formatted_data += "<div class='card-body'>"
            formatted_data += "<p>Federal Reserve Economic Data (FRED)</p>"
            formatted_data += f"<p class='text-muted'>Last updated: {macro_data.get('timestamp', 'N/A')}</p>"
            formatted_data += "</div></div></div></div>"
            
            return render_template(
                "market_data.html",
                title="Macroeconomic Indicators",
                description="Comprehensive analysis of macroeconomic factors affecting gold markets",
                data=macro_data,
                formatted_data=formatted_data,
                endpoint_type="macroeconomic"
            )
        else:
            return render_template(
                "market_data.html",
                title="Macroeconomic Indicators",
                description="Error: Macroeconomic indicators module not available",
                data={"error": "Macroeconomic indicators module not available"},
                endpoint_type="error"
            )
    except Exception as e:
        logger.error(f"Error generating macroeconomic dashboard: {str(e)}")
        return render_template(
            "market_data.html",
            title="Macroeconomic Dashboard",
            description="Error generating macroeconomic dashboard",
            data={"error": str(e), "timestamp": str(datetime.now())},
            endpoint_type="error"
        )

@app.route("/market/comprehensive")
def flask_comprehensive():
    """Get comprehensive market analysis combining all indicators (Web UI)"""
    try:
        # Import the combined analysis module
        try:
            from combined_analysis import get_integrated_dashboard
            integrated = True
        except ImportError:
            logger.warning("Combined analysis module not available, using legacy analysis")
            integrated = False
        
        if integrated:
            # Use the new integrated dashboard
            comprehensive_data = get_integrated_dashboard()
            
            # Format the data for display
            formatted_data = "<div class='row mb-4'>"
            
            # Market Summary Section
            formatted_data += "<div class='col-12'>"
            formatted_data += "<div class='card bg-dark border-secondary'>"
            formatted_data += "<div class='card-header'><h4>Market Summary</h4></div>"
            formatted_data += "<div class='card-body'>"
            
            # Add GC front month price if available
            if "market_data" in comprehensive_data and "gc1_price" in comprehensive_data["market_data"]:
                formatted_data += f"<p><strong>Gold Front Month Price:</strong> <span class='data-value'>${comprehensive_data['market_data']['gc1_price']}</span></p>"
            
            # Add term structure info if available
            if "market_data" in comprehensive_data and "structure_type" in comprehensive_data["market_data"]:
                formatted_data += f"<p><strong>Term Structure:</strong> <span class='data-value'>{comprehensive_data['market_data']['structure_type']}</span></p>"
            
            # Add real rates info if available
            if "macroeconomic_data" in comprehensive_data and "real_10y_rate" in comprehensive_data["macroeconomic_data"]:
                real_rate = comprehensive_data["macroeconomic_data"]["real_10y_rate"]
                real_rate_class = "data-negative" if real_rate < 0 else "data-positive"
                formatted_data += f"<p><strong>10-Year Real Rate:</strong> <span class='data-value {real_rate_class}'>{real_rate}%</span></p>"
            
            formatted_data += "</div></div></div>"
            formatted_data += "</div>"  # End of row
            
            # Combined Signal Section
            if "combined_signals" in comprehensive_data and "overall_bias" in comprehensive_data["combined_signals"]:
                formatted_data += "<div class='row mb-4'>"
                formatted_data += "<div class='col-12'>"
                formatted_data += "<div class='card bg-dark border-secondary'>"
                formatted_data += "<div class='card-header'><h4>Overall Market Bias</h4></div>"
                formatted_data += "<div class='card-body'>"
                
                overall_bias = comprehensive_data["combined_signals"]["overall_bias"]
                bias_class = "data-positive" if "Bullish" in overall_bias else "data-negative" if "Bearish" in overall_bias else "data-neutral"
                
                formatted_data += f"<h2 class='{bias_class}'>{overall_bias}</h2>"
                
                if "recommendation" in comprehensive_data["combined_signals"]:
                    formatted_data += f"<p><strong>Recommendation:</strong> {comprehensive_data['combined_signals']['recommendation']}</p>"
                
                # Add signal counts
                bullish = comprehensive_data["combined_signals"].get("bullish_signals", 0)
                bearish = comprehensive_data["combined_signals"].get("bearish_signals", 0)
                neutral = comprehensive_data["combined_signals"].get("neutral_signals", 0)
                total = comprehensive_data["combined_signals"].get("total_signals", 0)
                
                formatted_data += "<div class='d-flex justify-content-between mt-3'>"
                formatted_data += f"<div><span class='badge bg-success'>Bullish: {bullish}/{total}</span></div>"
                formatted_data += f"<div><span class='badge bg-warning'>Neutral: {neutral}/{total}</span></div>"
                formatted_data += f"<div><span class='badge bg-danger'>Bearish: {bearish}/{total}</span></div>"
                formatted_data += "</div>"
                
                formatted_data += "</div></div></div>"
                formatted_data += "</div>"  # End of row
            
            # Correlation Analysis Section
            if "correlated_analysis" in comprehensive_data and "analysis" in comprehensive_data["correlated_analysis"]:
                formatted_data += "<div class='row mb-4'>"
                formatted_data += "<div class='col-12'>"
                formatted_data += "<div class='card bg-dark border-secondary'>"
                formatted_data += "<div class='card-header'><h4>Correlation Analysis</h4></div>"
                formatted_data += "<div class='card-body'>"
                
                if "correlation_signal" in comprehensive_data["correlated_analysis"]["analysis"]:
                    signal = comprehensive_data["correlated_analysis"]["analysis"]["correlation_signal"]
                    signal_class = "data-positive" if "bull" in signal.lower() else "data-negative" if "bear" in signal.lower() else "data-neutral"
                    
                    formatted_data += f"<p><strong>Signal:</strong> <span class='{signal_class}'>{signal}</span></p>"
                
                if "signal_explanation" in comprehensive_data["correlated_analysis"]["analysis"]:
                    formatted_data += f"<p>{comprehensive_data['correlated_analysis']['analysis']['signal_explanation']}</p>"
                
                formatted_data += "</div></div></div>"
                formatted_data += "</div>"  # End of row
            
            # Divergence Analysis Section
            if "divergence_analysis" in comprehensive_data and "analysis" in comprehensive_data["divergence_analysis"]:
                formatted_data += "<div class='row mb-4'>"
                formatted_data += "<div class='col-12'>"
                formatted_data += "<div class='card bg-dark border-secondary'>"
                formatted_data += "<div class='card-header'><h4>Divergence Analysis</h4></div>"
                formatted_data += "<div class='card-body'>"
                
                if "summary" in comprehensive_data["divergence_analysis"]["analysis"]:
                    formatted_data += f"<p><strong>Summary:</strong> {comprehensive_data['divergence_analysis']['analysis']['summary']}</p>"
                
                if "recommendation" in comprehensive_data["divergence_analysis"]["analysis"]:
                    formatted_data += f"<p><strong>Recommendation:</strong> {comprehensive_data['divergence_analysis']['analysis']['recommendation']}</p>"
                
                # Add details if divergences were detected
                if "divergences" in comprehensive_data["divergence_analysis"] and comprehensive_data["divergence_analysis"]["divergences"]:
                    formatted_data += "<p><strong>Detected Divergences:</strong></p>"
                    formatted_data += "<ul>"
                    
                    for key, value in comprehensive_data["divergence_analysis"]["divergences"].items():
                        if key != "explanation" and key != "potential_signal":
                            formatted_data += f"<li>{value}</li>"
                    
                    formatted_data += "</ul>"
                    
                    if "explanation" in comprehensive_data["divergence_analysis"]["divergences"]:
                        formatted_data += f"<p>{comprehensive_data['divergence_analysis']['divergences']['explanation']}</p>"
                    
                    if "potential_signal" in comprehensive_data["divergence_analysis"]["divergences"]:
                        formatted_data += f"<p><strong>Signal:</strong> {comprehensive_data['divergence_analysis']['divergences']['potential_signal']}</p>"
                
                formatted_data += "</div></div></div>"
                formatted_data += "</div>"  # End of row
            
            # Macro Indicators Section
            if "macroeconomic_data" in comprehensive_data:
                formatted_data += "<div class='row mb-4'>"
                formatted_data += "<div class='col-12'>"
                formatted_data += "<div class='card bg-dark border-secondary'>"
                formatted_data += "<div class='card-header'><h4>Macroeconomic Indicators</h4></div>"
                formatted_data += "<div class='card-body'>"
                
                # Show real rates
                if "real_rates" in comprehensive_data["macroeconomic_data"] and "analysis" in comprehensive_data["macroeconomic_data"]["real_rates"]:
                    formatted_data += f"<p><strong>Real Rates Impact:</strong> {comprehensive_data['macroeconomic_data']['real_rates']['analysis'].get('implication', 'N/A')}</p>"
                
                # Show yield curve
                if "yield_curve" in comprehensive_data["macroeconomic_data"] and "analysis" in comprehensive_data["macroeconomic_data"]["yield_curve"]:
                    formatted_data += f"<p><strong>Yield Curve:</strong> {comprehensive_data['macroeconomic_data']['yield_curve']['analysis'].get('shape', 'N/A')}</p>"
                    formatted_data += f"<p><strong>Recession Signal:</strong> {comprehensive_data['macroeconomic_data']['yield_curve']['analysis'].get('recession_signal', 'N/A')}</p>"
                
                formatted_data += "</div></div></div>"
                formatted_data += "</div>"  # End of row
            
            # Data Source Section
            formatted_data += "<div class='row'>"
            formatted_data += "<div class='col-12'>"
            formatted_data += "<div class='card bg-dark border-secondary'>"
            formatted_data += "<div class='card-header'><h5>Data Sources</h5></div>"
            formatted_data += "<div class='card-body'>"
            formatted_data += "<p>Market data: Yahoo Finance</p>"
            formatted_data += "<p>Economic data: Federal Reserve Economic Data (FRED)</p>"
            formatted_data += f"<p class='text-muted'>Last updated: {comprehensive_data.get('timestamp', 'N/A')}</p>"
            formatted_data += "</div></div></div></div>"
            
            return render_template(
                "market_data.html",
                title="Enhanced Comprehensive Analysis",
                description="Integrated analysis combining market data with macroeconomic indicators",
                data=comprehensive_data,
                formatted_data=formatted_data,
                endpoint_type="integrated_comprehensive"
            )
        else:
            # Fallback to legacy comprehensive analysis
            comprehensive_data = get_comprehensive_analysis()
            return render_template(
                "market_data.html",
                title="Comprehensive Market Analysis",
                description="Complete market analysis combining all indicators and signals",
                data=comprehensive_data,
                endpoint_type="comprehensive"
            )
    except Exception as e:
        logger.error(f"Error generating comprehensive analysis: {str(e)}")
        return render_template(
            "market_data.html",
            title="Comprehensive Analysis",
            description="Error generating comprehensive analysis",
            data={"error": str(e), "timestamp": str(datetime.now())},
            endpoint_type="error"
        )

@app.route("/analyze", methods=["POST"])
def flask_analyze_market():
    """Flask endpoint for market analysis"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Validate the input data
        input_model = MarketInput(
            ticker_front=data.get("ticker_front", ""),
            ticker_next=data.get("ticker_next", ""),
            physical_demand=data.get("physical_demand", ""),
            price_breakout=data.get("price_breakout", False)
        )
        
        logger.debug(f"Received analysis request for tickers: {input_model.ticker_front} and {input_model.ticker_next}")
        result = analyze_futures_market(input_model)
        
        # Convert to dictionary for JSON serialization
        result_dict = result.dict()
        
        # Use json.dumps with our custom serializer for datetime objects
        return json.dumps(result_dict, default=json_serialize), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Error analyzing market: {str(e)}")
        return jsonify({"detail": f"Error analyzing market data: {str(e)}"}), 500

@app.route("/market/futures-curve")
def flask_futures_curve():
    """Display the gold futures yield curve and spread analysis with FRED macroeconomic data (Web UI)"""
    try:
        # Get data from the enhanced futures curve function with FRED data
        from gold_futures_curve import get_enhanced_gold_futures_curve
        curve_data = get_enhanced_gold_futures_curve()
        
        # Add timestamp if not present
        if 'timestamp' not in curve_data:
            curve_data['timestamp'] = str(datetime.now())
            
        return render_template(
            "gold_futures_curve.html",
            data=curve_data
        )
    except Exception as e:
        logger.error(f"Error analyzing gold futures curve: {str(e)}")
        return render_template(
            "gold_futures_curve.html",
            data={"error": str(e), "timestamp": str(datetime.now())}
        )

@app.route("/health")
def flask_health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api")
def flask_api_info():
    """API information page"""
    api_info = {
        "name": "Futures Market Analysis API",
        "version": "2.0.0",
        "description": "Comprehensive futures market analysis with focus on gold, interest rates, and market sentiment",
        "endpoints": [
            {
                "path": "/api/premarket",
                "method": "GET",
                "description": "Get premarket data for major futures contracts"
            },
            {
                "path": "/api/gold/term-structure",
                "method": "GET",
                "description": "Analyze gold futures term structure (GC1, GC2, GC3)"
            },
            {
                "path": "/api/interest-impact",
                "method": "GET",
                "description": "Analyze impact of interest rates on gold prices"
            },
            {
                "path": "/api/market-sentiment",
                "method": "GET",
                "description": "Analyze market sentiment and its impact on gold"
            },
            {
                "path": "/api/gold-cycle",
                "method": "GET",
                "description": "Detect potential gold cycle turning points"
            },
            {
                "path": "/api/economic-expectations",
                "method": "GET",
                "description": "Analyze current economic expectations for gold"
            },
            {
                "path": "/api/comprehensive",
                "method": "GET",
                "description": "Get comprehensive market analysis combining all indicators"
            },
            {
                "path": "/analyze",
                "method": "POST",
                "description": "Legacy endpoint for market exhaustion analysis"
            }
        ]
    }
    return jsonify(api_info)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)