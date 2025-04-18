from flask import Flask, render_template, request, send_file, redirect, url_for
import csv
import sqlite3
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['DATABASE'] = 'output.db'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            table_name = convert_csv_to_db(filepath, app.config['DATABASE'])
            db_content = fetch_db_content(table_name)
            return render_template('download.html', db_file=app.config['DATABASE'], table_name=table_name, db_content=db_content)
    return render_template('index.html')


@app.route('/download')
def download():
    table_name = request.args.get('table_name')
    db_content = fetch_db_content(table_name)
    return render_template('download.html', db_file=app.config['DATABASE'], table_name=table_name, db_content=db_content)

@app.route('/download_db')
def download_db():
    return send_file(app.config['DATABASE'], as_attachment=True)

def convert_csv_to_db(csv_filepath, db_filepath):
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()
    table_name = os.path.splitext(os.path.basename(csv_filepath))[0]
    
    # Sanitize table name to avoid SQL injection or invalid characters
    table_name = table_name.replace(" ", "_").replace("-", "_")
    
    with open(csv_filepath, 'r') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)
        
        # Sanitize headers and assign TEXT type
        sanitized_headers = [f'"{header.replace(" ", "_").replace("-", "_")}" TEXT' for header in headers]
        columns = ", ".join(sanitized_headers)
        
        # Drop table if it exists
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Create table with sanitized headers and TEXT type
        cursor.execute(f"CREATE TABLE {table_name} ({columns})")
        
        # Insert rows
        for row in csv_reader:
            cursor.execute(f"INSERT INTO {table_name} VALUES ({', '.join(['?']*len(row))})", row)
    
    conn.commit()
    conn.close()
    return table_name

def fetch_db_content(table_name):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    conn.close()

    # Get first 5 rows, a separator, and last 5 rows
    if len(rows) > 10:
        content = rows[:5] + [("----",) * len(rows[0])] + rows[-5:]
    else:
        content = rows  # If there are 10 or fewer rows, display all
    return content

if __name__ == '__main__':
    app.run(debug=True)
