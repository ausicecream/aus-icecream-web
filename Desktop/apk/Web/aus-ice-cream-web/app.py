from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
# Path database (sama macam APK, letak di folder project)
DB_PATH = 'aus.db'

# Fungsi sambung DB
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/pesanan', methods=['GET', 'POST'])
def pesanan():
    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        # Ambil data dari form
        nama = request.form.get('nama')
        tel_no = request.form.get('tel_no')
        tarikh = request.form.get('tarikh')
        alamat = request.form.get('alamat')
        package = request.form.get('package')
        qty = int(request.form.get('qty') or 0)
        discount = float(request.form.get('discount') or 0)
        transport = float(request.form.get('transport') or 0)
        deposit = float(request.form.get('deposit') or 0)

        # Kira harga
        harga_unit = 0.60 if package == 'MINI' else 1.00
        total_price = qty * harga_unit
        balance = total_price - discount + transport - deposit

        # Simpan ke DB
        c.execute('''
            INSERT INTO pesanan (nama, tel_no, tarikh, alamat, package, qty, total_price, discount, transport, deposit, balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nama, tel_no, tarikh, alamat, package, qty, total_price, discount, transport, deposit, balance))
        conn.commit()

        # Dapat bil_no terbaru
        bil_no = c.lastrowid

        conn.close()

        # Generate PDF resit
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="AUS ICE CREAM CATERING", ln=1, align="C")
        pdf.cell(200, 10, txt="Resit Pesanan", ln=1, align="C")
        pdf.cell(200, 10, txt=f"Bil No: {bil_no}", ln=1)
        pdf.cell(200, 10, txt=f"Tarikh: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
        pdf.ln(10)

        pdf.cell(200, 10, txt="Maklumat Pelanggan", ln=1)
        pdf.cell(200, 10, txt=f"Nama: {nama}", ln=1)
        pdf.cell(200, 10, txt=f"Tel: {tel_no}", ln=1)
        pdf.cell(200, 10, txt=f"Tarikh Event: {tarikh}", ln=1)
        pdf.multi_cell(200, 10, txt=f"Alamat: {alamat}")
        pdf.ln(10)

        pdf.cell(200, 10, txt="Butiran Pesanan", ln=1)
        pdf.cell(60, 10, txt="Package", border=1)
        pdf.cell(30, 10, txt="Qty", border=1)
        pdf.cell(50, 10, txt="Harga Unit", border=1)
        pdf.cell(50, 10, txt="Jumlah", border=1, ln=1)

        pdf.cell(60, 10, txt=package, border=1)
        pdf.cell(30, 10, txt=str(qty), border=1)
        pdf.cell(50, 10, txt=f"RM{harga_unit:.2f}", border=1)
        pdf.cell(50, 10, txt=f"RM{total_price:.2f}", border=1, ln=1)

        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Baki Bayaran: RM{balance:.2f}", ln=1)

        # Simpan PDF ke memory (tak simpan di server)
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        return send_file(
            pdf_output,
            as_attachment=True,
            download_name=f"Resit_Bil{bil_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )

    # GET: papar senarai pesanan
    c.execute("SELECT * FROM pesanan ORDER BY bil_no DESC LIMIT 10")
    pesanan_list = c.fetchall()
    conn.close()

    return render_template('pesanan.html', pesanan_list=pesanan_list, title="Pesanan")
if __name__ == '__main__':
    app.run(debug=True)