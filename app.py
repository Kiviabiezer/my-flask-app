from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os

# Çalışma dizinini ayarla
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("Çalışma dizini:", os.getcwd())

app = Flask(__name__)

# Veritabanı bağlantısı
def get_db_connection():
    conn = sqlite3.connect('dictionary.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ana sayfa - Arama formu, Kelime Ekleme formu ve Kelime Silme formu
@app.route('/')
def home():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Online Sözlük</title>
            <!-- Bootstrap CSS -->
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {
                    padding: 20px;
                    background-color: #f8f9fa;
                }
                .container {
                    max-width: 600px;
                    margin: auto;
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                h1, h2 {
                    text-align: center;
                    color: #0d6efd;
                }
                form {
                    margin-bottom: 20px;
                }
                .result {
                    margin-top: 10px;
                    padding: 10px;
                    border-radius: 5px;
                }
                .success {
                    background-color: #d4edda;
                    color: #155724;
                }
                .error {
                    background-color: #f8d7da;
                    color: #721c24;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Online Verinti Kelime Sözlüğü</h1>

                <!-- Kelime Arama Formu -->
                <form id="searchForm" class="mb-4">
                    <div class="input-group">
                        <input type="text" id="wordInput" class="form-control" placeholder="Kelime ara..." required>
                        <button type="submit" class="btn btn-primary">Ara</button>
                    </div>
                </form>
                <div id="result" class="result"></div>

                <hr>

                <!-- Kelime Ekleme Formu -->
                <h2>Yeni Kelime Ekle</h2>
                <form id="addWordForm" class="mb-4">
                    <div class="mb-3">
                        <input type="text" id="newWord" class="form-control" placeholder="Kelime" required>
                    </div>
                    <div class="mb-3">
                        <textarea id="newDefinition" class="form-control" placeholder="Tanım" rows="3" required></textarea>
                    </div>
                    <button type="submit" class="btn btn-success">Ekle</button>
                </form>
                <div id="addResult" class="result"></div>

                <hr>

                <!-- Kelime Silme Formu -->
                <h2>Kelime Sil</h2>
                <form id="deleteWordForm" class="mb-4">
                    <div class="mb-3">
                        <input type="text" id="deleteWord" class="form-control" placeholder="Silinecek kelime" required>
                    </div>
                    <button type="submit" class="btn btn-danger">Sil</button>
                </form>
                <div id="deleteResult" class="result"></div>
            </div>

            <script>
                // Kelime Arama Formu
                document.getElementById('searchForm').addEventListener('submit', function(event) {
                    event.preventDefault();
                    const word = document.getElementById('wordInput').value;

                    fetch(`/search?word=${encodeURIComponent(word)}`)
                        .then(response => response.text())
                        .then(data => {
                            document.getElementById('result').innerHTML = data;
                        })
                        .catch(error => {
                            console.error('Hata:', error);
                            document.getElementById('result').innerHTML = '<p class="error">Bir hata oluştu.</p>';
                        });
                });

                // Kelime Ekleme Formu
                document.getElementById('addWordForm').addEventListener('submit', function(event) {
                    event.preventDefault();
                    const word = document.getElementById('newWord').value;
                    const definition = document.getElementById('newDefinition').value;

                    fetch('/add_word', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ word, definition })
                    })
                    .then(response => response.json())
                    .then(data => {
                        const addResultDiv = document.getElementById('addResult');
                        if (data.message) {
                            addResultDiv.innerHTML = `<p class="success">${data.message}</p>`;
                        } else {
                            addResultDiv.innerHTML = `<p class="error">${data.error}</p>`;
                        }
                    })
                    .catch(error => console.error('Hata:', error));
                });

                // Kelime Silme Formu
                document.getElementById('deleteWordForm').addEventListener('submit', function(event) {
                    event.preventDefault();
                    const word = document.getElementById('deleteWord').value;

                    fetch('/delete_word', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ word })
                    })
                    .then(response => response.json())
                    .then(data => {
                        const deleteResultDiv = document.getElementById('deleteResult');
                        if (data.message) {
                            deleteResultDiv.innerHTML = `<p class="success">${data.message}</p>`;
                        } else {
                            deleteResultDiv.innerHTML = `<p class="error">${data.error}</p>`;
                        }
                    })
                    .catch(error => console.error('Hata:', error));
                });
            </script>
        </body>
        </html>
    ''')

# Kelime arama endpoint'i
@app.route('/search', methods=['GET'])
def search():
    word = request.args.get('word')
    if not word:
        return "Lütfen bir kelime girin.", 400

    conn = get_db_connection()
    result = conn.execute("SELECT * FROM dictionary WHERE word=?", (word,)).fetchone()
    conn.close()

    if result:
        return f'<strong>{result["word"]}:</strong> {result["definition"]}'
    else:
        return f'<p class="error">"{word}" kelimesi sözlükte bulunamadı.</p>', 404

# Kelime ekleme endpoint'i
@app.route('/add_word', methods=['POST'])
def add_word():
    data = request.get_json()
    word = data.get('word')
    definition = data.get('definition')

    if not word or not definition:
        return jsonify({"error": "Kelime ve tanım gerekli"}), 400

    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO dictionary (word, definition) VALUES (?, ?)", (word, definition))
        conn.commit()
        conn.close()
        return jsonify({"message": f"'{word}' kelimesi başarıyla eklendi."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": f"'{word}' kelimesi zaten sözlükte var."}), 409

# Kelime silme endpoint'i
@app.route('/delete_word', methods=['POST'])
def delete_word():
    data = request.get_json()
    word = data.get('word')

    if not word:
        return jsonify({"error": "Silinecek kelime gerekli"}), 400

    conn = get_db_connection()
    result = conn.execute("DELETE FROM dictionary WHERE word=?", (word,))
    conn.commit()
    conn.close()

    if result.rowcount > 0:
        return jsonify({"message": f"'{word}' kelimesi başarıyla silindi."}), 200
    else:
        return jsonify({"error": f"'{word}' kelimesi sözlükte bulunamadı."}), 404

if __name__ == '__main__':
    app.run(debug=True)
