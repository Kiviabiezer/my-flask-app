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
    return '''
        <h1>Online Sözlük</h1>

        <!-- Kelime Arama Formu -->
        <form id="searchForm">
            <input type="text" id="wordInput" placeholder="Kelime ara..." required>
            <button type="submit">Ara</button>
        </form>
        <div id="result"></div>

        <hr>

        <!-- Kelime Ekleme Formu -->
        <h2>Yeni Kelime Ekle</h2>
        <form id="addWordForm">
            <input type="text" id="newWord" placeholder="Kelime" required>
            <textarea id="newDefinition" placeholder="Tanım" required></textarea>
            <button type="submit">Ekle</button>
        </form>
        <div id="addResult"></div>

        <hr>

        <!-- Kelime Silme Formu -->
        <h2>Kelime Sil</h2>
        <form id="deleteWordForm">
            <input type="text" id="deleteWord" placeholder="Silinecek kelime" required>
            <button type="submit">Sil</button>
        </form>
        <div id="deleteResult"></div>

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
                        document.getElementById('result').innerHTML = '<p style="color: red;">Bir hata oluştu.</p>';
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
                        addResultDiv.innerHTML = `<p style="color: green;">${data.message}</p>`;
                    } else {
                        addResultDiv.innerHTML = `<p style="color: red;">${data.error}</p>`;
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
                        deleteResultDiv.innerHTML = `<p style="color: green;">${data.message}</p>`;
                    } else {
                        deleteResultDiv.innerHTML = `<p style="color: red;">${data.error}</p>`;
                    }
                })
                .catch(error => console.error('Hata:', error));
            });
        </script>
    '''

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
        return f'<p style="color: red;">"{word}" kelimesi sözlükte bulunamadı.</p>', 404

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
