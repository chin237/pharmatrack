from flask import Flask, render_template
import webview
import threading
from database.queries import get_product_list

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html', active_page='dashboard')

@app.route('/products')
def product_list():
    products = get_product_list()
    return render_template('product_list.html', active_page='inventory', products=products)

@app.route('/products/<product_id>')
def product_details(product_id):
    return render_template('product_details.html', active_page='inventory', product_id=product_id)

@app.route('/movements/new')
def record_movement():
    return render_template('record_movement.html', active_page='movements')

@app.route('/loss-reports')
def loss_reports():
    return render_template('loss_reports.html', active_page='loss_reports')

def start_flask():
    app.run(port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=start_flask, daemon=True).start()
    webview.create_window('PharmaTrack', 'http://127.0.0.1:5000')
    webview.start()