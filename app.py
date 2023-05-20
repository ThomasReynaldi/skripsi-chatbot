from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import mysql.connector
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import string

app = Flask(__name__)
app.debug = True
app.secret_key = 'your_secret_key'


# Koneksi ke database
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="faq_pusdiklat"
)
# Fungsi untuk mengambil data corpus dan jawaban dari database


# Fungsi untuk memeriksa keberadaan pengguna dalam database
def check_user(username, password):
    mycursor = mydb.cursor()
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    values = (username, password)
    mycursor.execute(query, values)
    user = mycursor.fetchone()

    if user is not None:
        return True

    return False

#Menggambil data 
def get_data_from_database():
    cursor = mydb.cursor()
    query = "SELECT pertanyaan, jawaban FROM faq"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data

def run_text_similarity(user_input, data):
    corpus = [d[0] for d in data] + [user_input]

    # Membangun vektor TF-IDF dari corpus
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Menghitung similarity scores menggunakan cosine similarity
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])

    # Mendapatkan indeks pertanyaan yang paling mirip
    most_similar_index = similarity_scores.argmax()

    # Mendapatkan jawaban yang paling sesuai dengan pertanyaan
    response = data[most_similar_index][1] if similarity_scores[0][most_similar_index] > 0 else "Maaf, saya tidak mengerti pertanyaan Anda."

    return response

@app.route('/get_response', methods=['POST'])
def get_chatbot_response():
    user_input = request.form['user_input']

    # Mengambil data corpus dan jawaban dari database
    data = get_data_from_database()

    # Menjalankan text similarity untuk mendapatkan jawaban
    bot_response = run_text_similarity(user_input, data)

    # Mengembalikan respons chatbot dalam format JSON
    return jsonify({'message': bot_response})

#Route Utama Disini

@app.route('/')
def main():return render_template('website/index.html')
                    

                    

# Rute untuk halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if check_user(username, password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Rute untuk halaman home setelah login
@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        return render_template('dashboard/index.html', username=username)
    else:
        return redirect(url_for('login'))
    
#Rute Data
@app.route('/data')
def show_data():
    if 'username' not in session:
        return redirect(url_for('login'))
    # Mendapatkan data dari database
    cursor = mydb.cursor()
    query = "SELECT * FROM faq"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()

    return render_template('pertanyaan/index.html', data=data)

#Create 
@app.route('/add_data', methods=['POST'])
def add_data():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Retrieve the data from the form
    pertanyaan = request.form['pertanyaan']
    jawaban = request.form['jawaban']

    # Insert the data into the database
    cursor = mydb.cursor()
    query = "INSERT INTO faq (pertanyaan, jawaban) VALUES (%s, %s)"
    values = (pertanyaan, jawaban)
    cursor.execute(query, values)
    mydb.commit()
    cursor.close()

    return redirect(url_for('show_data'))


#Edit
@app.route('/edit_data/<int:id>', methods=['POST'])
def edit_data(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    pertanyaan = request.form['pertanyaan']
    jawaban = request.form['jawaban']

    # Lakukan proses update data ke database menggunakan id
    cursor = mydb.cursor()
    query = "UPDATE faq SET pertanyaan = %s, jawaban = %s WHERE id = %s"
    values = (pertanyaan, jawaban, id)
    cursor.execute(query, values)
    mydb.commit()
    cursor.close()

    return redirect(url_for('show_data'))

#route Delete
def delete_data(data_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Hapus data dari database berdasarkan ID
    cursor = mydb.cursor()
    query = "DELETE FROM faq WHERE id = %s"
    values = (data_id,)
    cursor.execute(query, values)
    mydb.commit()
    cursor.close()

    return redirect(url_for('show_data'))



# Rute untuk logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
