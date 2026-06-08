from flask import Flask

app = Flask(__name__)

@app.route('/api/v1/status')
def status():
    """Provides a simple status endpoint for the worker."""
    return {"status": "ok", "service": "Claw-Worker-01"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
