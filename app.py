# ======================================================================================
# IMPORTING REQUIRED LIBRARIES
# ======================================================================================
import time     # Used to measure time duration (latency) for incoming API requests
import random   # Used to securely pick random characters for password generation
import string   # Contains pre-defined character constants (letters, digits, symbols)
from flask import Flask, request, jsonify  # Flask framework to handle HTTP routing and JSON responses

# Prometheus libraries to define metric counters and expose them to the web server
from prometheus_client import make_wsgi_app, Counter, Histogram
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# ======================================================================================
# INITIALIZING THE FLASK APPLICATION
# ======================================================================================
# Standard initialization of a Flask web app context
app = Flask(__name__)

# ======================================================================================
# DEFINING PROMETHEUS METRIC TYPES
# ======================================================================================

# 1. COUNTER TYPE: A metric that can only increase (used to track total totals)
# We use labels: ['method', 'endpoint', 'http_status'] so we can filter metrics by these attributes later in Grafana
REQUEST_COUNT = Counter(
    'app_requests_total', 
    'Total number of HTTP requests handled by the password API',
    ['method', 'endpoint', 'http_status']
)

# 2. HISTOGRAM TYPE: Measures the duration (latency) or sizes of events and puts them into brackets/buckets
# Perfect for calculating average response times and checking if the application is getting slow
REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds', 
    'Time spent processing HTTP requests in seconds',
    ['endpoint']
)

# 3. CUSTOM COUNTER: Tracks custom business logic (how many strong vs weak passwords users create)
PASSWORD_STRENGTH_COUNT = Counter(
    'app_passwords_generated_total',
    'Total number of passwords generated, labeled by strength level',
    ['strength']
)

# ======================================================================================
# DEFINING APPLICATION ROUTES (BUSINESS LOGIC)
# ======================================================================================

# Route 1: Password Generation API - accessible via HTTP GET at http://localhost:5000/generate
@app.route('/generate', methods=['GET'])
def generate_password():
    # Capture the exact timestamp when the request hits the server
    start_time = time.time()
    
    # Read the query parameter 'length' from the URL (e.g., /generate?length=16)
    # request.args.get() reads URL parameters. '12' is the default fallback if empty.
    # int() converts the text parameter into an integer number.
    length = int(request.args.get('length', 12))
    
    # Combine lowercase, uppercase letters, numeric digits, and punctuation characters
    characters = string.ascii_letters + string.digits + string.punctuation
    
    # Python List Comprehension: Loops 'length' times, picks a random character, and merges them into one string
    password = ''.join(random.choice(characters) for _ in range(length))
    
    # Simple business logic conditional check to classify password strength
    if length < 8:
        strength = "weak"
    elif length < 14:
        strength = "medium"
    else:
        strength = "strong"
    
    # ----------------------------------------------------------------------------------
    # RECORDING METRICS (DEVOPS GROUNDWORK)
    # ----------------------------------------------------------------------------------
    # .labels() injects the custom tag. .inc() increases the numerical counter by 1
    PASSWORD_STRENGTH_COUNT.labels(strength=strength).inc()
    
    # Calculate exactly how many fractions of a second it took python to process the logic
    duration = time.time() - start_time
    
    # Feed the processing duration into our latency histogram bucket
    REQUEST_LATENCY.labels(endpoint='/generate').observe(duration)
    
    # Log the successful 200 HTTP code request into our global request counter
    REQUEST_COUNT.labels(method='GET', endpoint='/generate', http_status='200').inc()
    
    # Return a structured JSON response back to the client browser with status code 200 (Success)
    return jsonify({
        'password': password,
        'length': length,
        'strength': strength
    }), 200


# Route 2: Basic Application Health Check - accessible at http://localhost:5000/health
@app.route('/health', methods=['GET'])
def health_check():
    # Increment total requests counter for this endpoint
    REQUEST_COUNT.labels(method='GET', endpoint='/health', http_status='200').inc()
    # Returns a simple healthy heartbeat json object
    return jsonify({'status': 'healthy'}), 200


# ======================================================================================
# ATTACHING PROMETHEUS EXPORTER MIDDLEWARE
# ======================================================================================
# DispatcherMiddleware intercepting requests and introducing the '/metrics' sub-path
# When Prometheus hits http://localhost:5000/metrics, this WSGI application will translate
# our Python variables (REQUEST_COUNT, etc.) into a text format that Prometheus scrapes seamlessly.
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# ======================================================================================
# SERVER RUN COMMAND
# ======================================================================================
# Standard entry point structure ensuring code runs only when executed directly (not when imported)
if __name__ == '__main__':
    # host='0.0.0.0' binds the server to listen to internal networks (allowing Docker communication)
    # port=5000 hosts the web server on network port 5000
    app.run(host='0.0.0.0', port=5000)
