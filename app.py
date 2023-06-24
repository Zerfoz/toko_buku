from flask import Flask, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQL
import mysql.connector
from functools import wraps
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)

UPLOAD_FOLDER = 'static/images'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Konfigurasi database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'toko_buku'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Pengaturan kunci rahasia sesi
app.config['SECRET_KEY'] = 'secret_key'

# Membuat objek MySQL
mysql = MySQL(app)

# Decorator untuk memeriksa apakah pengguna telah login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE nama_pengguna = %s AND kata_sandi = %s", (username, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['logged_in'] = True
            if username == 'admin':
                return redirect('/dashboard_admin')
            else:
                return redirect('/dashboard_kasir')
        else:
            error = 'Invalid credentials. Please try again.'
            return render_template('login/login.html', error=error)

    return render_template('login/login.html', error=None)


@app.route('/dashboard_admin')
@login_required
def dashboard_admin():
    # Mendapatkan kursor database
    cur = mysql.connection.cursor()

    # Mengeksekusi query untuk mendapatkan data dari tabel populer_buku
    query1 = """
        SELECT b.Id_buku, b.Judul, b.Penulis, SUM(p.Jumlah_dibeli) AS jumlah_terjual, b.Images
        FROM buku b
        JOIN penjualan p ON b.Id_buku = p.Id_buku
        GROUP BY b.Id_buku, b.Judul, b.Penulis
        HAVING SUM(p.Jumlah_dibeli) = (
            SELECT MAX(jumlah_terjual)
            FROM (
                SELECT SUM(p.Jumlah_dibeli) AS jumlah_terjual
                FROM buku b
                JOIN penjualan p ON b.Id_buku = p.Id_buku
                GROUP BY b.Id_buku
            ) AS subquery
        );
    """
    cur.execute(query1)
    populer_buku = cur.fetchall()

    # Mengeksekusi query untuk mendapatkan data dari tabel unpopuler_buku
    query2 = """
        SELECT b.Id_buku, b.Judul, b.Penulis, SUM(p.Jumlah_dibeli) AS jumlah_terjual, b.Images
        FROM buku b
        JOIN penjualan p ON b.Id_buku = p.Id_buku
        GROUP BY b.Id_buku, b.Judul, b.Penulis
        HAVING SUM(p.Jumlah_dibeli) = (
            SELECT MIN(jumlah_terjual)
            FROM (
                SELECT SUM(p.Jumlah_dibeli) AS jumlah_terjual
                FROM buku b
                JOIN penjualan p ON b.Id_buku = p.Id_buku
                GROUP BY b.Id_buku
            ) AS subquery
        );
    """
    cur.execute(query2)
    unpopuler_buku = cur.fetchall()

    # Menutup kursor dan database
    cur.close()

    return render_template('admin/dashboard_admin.html', populer_buku=populer_buku, unpopuler_buku=unpopuler_buku)

@app.route('/dashboard_admin_databuku')
@login_required
def dashboard_admin_databuku():

    cur = mysql.connection.cursor()
    cur.execute("SELECT Id_buku, Judul, Penulis, Penerbit, Tahun_terbit, Harga, Jumlah_stok, Images FROM buku")
    data_buku = cur.fetchall()
    cur.close()

    return render_template('admin/dashboard_admin_databuku.html', data_buku=data_buku)

# Route untuk tambah data buku
@app.route('/tambah_data_buku', methods=['GET', 'POST'])
@login_required
def tambah_databuku():
    if request.method == 'POST':
        judul = request.form['judul']
        penulis = request.form['penulis']
        penerbit = request.form['penerbit']
        tahun_terbit = request.form['tahun_terbit']
        harga = request.form['harga']
        jumlah_stok = request.form['jumlah_stok']
        
        # Mengunggah file gambar
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None

        cur = mysql.connection.cursor()

        # Insert data buku ke tabel buku
        cur.execute("INSERT INTO buku (Judul, Penulis, Penerbit, Tahun_terbit, Harga, Jumlah_stok, Images) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (judul, penulis, penerbit, tahun_terbit, harga, jumlah_stok, filename))
        mysql.connection.commit()

        cur.close()

        return redirect(url_for('dashboard_admin_databuku'))

    return render_template('admin/tambah_data_buku.html')



# Route untuk halaman ubah data buku
@app.route('/ubah_data_buku/<int:id>', methods=['GET'])
@login_required
def ubah_databuku(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM buku WHERE Id_buku = %s", (id,))
    buku = cur.fetchone()
    cur.close()

    return render_template('admin/ubah_data_buku.html', buku=buku)

# Route untuk menyimpan perubahan data buku
@app.route('/simpan_perubahan_buku/<int:id>', methods=['POST'])
@login_required
def simpan_perubahan_buku(id):
    judul = request.form['judul']
    penulis = request.form['penulis']
    penerbit = request.form['penerbit']
    tahun_terbit = request.form['tahun_terbit']
    harga = request.form['harga']
    jumlah_stok = request.form['jumlah_stok']

    cur = mysql.connection.cursor()

    # Mengunggah file gambar
    image = request.files['image']
    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        filename = None

    # Update data buku di tabel buku
    cur.execute("UPDATE buku SET Judul=%s, Penulis=%s, Penerbit=%s, Tahun_terbit=%s, Harga=%s, Jumlah_stok=%s, Images=%s WHERE Id_buku=%s",
                (judul, penulis, penerbit, tahun_terbit, harga, jumlah_stok, filename, id))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('dashboard_admin_databuku'))


# Route untuk halaman hapus data buku
@app.route('/hapus_data_buku/<int:id>', methods=['GET'])
@login_required
def hapus_databuku(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM buku WHERE Id_buku = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('dashboard_admin_databuku'))


@app.route('/dashboard_kasir')
@login_required
def dashboard_kasir():
    # Mendapatkan kursor database
    cur = mysql.connection.cursor()

    # Mengeksekusi query untuk mendapatkan data dari tabel populer_buku
    query1 = """
        SELECT b.Id_buku, b.Judul, b.Penulis, SUM(p.Jumlah_dibeli) AS jumlah_terjual, b.Images
        FROM buku b
        JOIN penjualan p ON b.Id_buku = p.Id_buku
        GROUP BY b.Id_buku, b.Judul, b.Penulis
        HAVING SUM(p.Jumlah_dibeli) = (
            SELECT MAX(jumlah_terjual)
            FROM (
                SELECT SUM(p.Jumlah_dibeli) AS jumlah_terjual
                FROM buku b
                JOIN penjualan p ON b.Id_buku = p.Id_buku
                GROUP BY b.Id_buku
            ) AS subquery
        );
    """
    cur.execute(query1)
    populer_buku = cur.fetchall()

    # Mengeksekusi query untuk mendapatkan data dari tabel unpopuler_buku
    query2 = """
        SELECT b.Id_buku, b.Judul, b.Penulis, SUM(p.Jumlah_dibeli) AS jumlah_terjual, b.Images
        FROM buku b
        JOIN penjualan p ON b.Id_buku = p.Id_buku
        GROUP BY b.Id_buku, b.Judul, b.Penulis
        HAVING SUM(p.Jumlah_dibeli) = (
            SELECT MIN(jumlah_terjual)
            FROM (
                SELECT SUM(p.Jumlah_dibeli) AS jumlah_terjual
                FROM buku b
                JOIN penjualan p ON b.Id_buku = p.Id_buku
                GROUP BY b.Id_buku
            ) AS subquery
        );
    """
    cur.execute(query2)
    unpopuler_buku = cur.fetchall()

    # Menutup kursor dan database
    cur.close()

    return render_template('kasir/dashboard_kasir.html', populer_buku=populer_buku, unpopuler_buku=unpopuler_buku)


@app.route('/dashboard_kasir_databuku', methods=['GET', 'POST'])
@login_required
def dashboard_kasir_databuku():
    keyword = request.args.get('keyword', '')  # Mendapatkan nilai keyword dari parameter URL

    cur = mysql.connection.cursor()
    if keyword:
        # Jika ada keyword pencarian, lakukan pencarian berdasarkan judul atau penulis buku
        cur.execute("SELECT * FROM buku WHERE Judul LIKE %s OR Penulis LIKE %s", ('%' + keyword + '%', '%' + keyword + '%'))
    else:
        # Jika tidak ada keyword pencarian, tampilkan semua data buku
        cur.execute("SELECT * FROM buku")
    
    data_buku = cur.fetchall()
    cur.close()

    return render_template('kasir/dashboard_kasir_databuku.html', data_buku=data_buku, keyword=keyword)

@app.route('/penjualan', methods=['GET', 'POST'])
@login_required
def penjualan():
    if request.method == 'POST':
        id_buku = request.form['id_buku']
        jumlah_dibeli = int(request.form['jumlah_dibeli'])

        cur = mysql.connection.cursor()

        # Ambil data buku dari tabel buku berdasarkan ID buku
        cur.execute("SELECT * FROM buku WHERE Id_buku = %s", (id_buku,))
        buku = cur.fetchone()

        if not buku:
            error = 'Buku dengan ID tersebut tidak ditemukan.'
            return render_template('kasir/penjualan.html', error=error)

        harga_beli = buku['Harga'] * jumlah_dibeli

        # Insert data penjualan ke tabel penjualan
        cur.execute("INSERT INTO penjualan (Id_buku, Tanggal, Jumlah_dibeli, Harga_beli) VALUES (%s, CURDATE(), %s, %s)",
                    (id_buku, jumlah_dibeli, harga_beli))
        mysql.connection.commit()

        # Kurangi jumlah stok buku di tabel buku
        cur.execute("UPDATE buku SET Jumlah_stok = Jumlah_stok - %s WHERE Id_buku = %s", (jumlah_dibeli, id_buku))
        mysql.connection.commit()

        cur.close()

        return redirect(url_for('tabel_penjualan'))
        

    return render_template('kasir/penjualan.html')

@app.route('/tabel_penjualan', methods=['GET'])
@login_required
def tabel_penjualan():
    cur = mysql.connection.cursor()

    # Ambil data penjualan dari tabel penjualan
    cur.execute("SELECT * FROM penjualan")
    data_penjualan = cur.fetchall()
    cur.close()

    return render_template('kasir/penjualan.html', data_penjualan=data_penjualan)



@app.route('/logout')
@login_required
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
