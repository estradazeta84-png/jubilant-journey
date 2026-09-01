from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_valle_olivos'

# Configuración inteligente para conectar con Supabase desde Render
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Puestos para el Directorio Valle de los Olivos
class Puesto(db.Model):
    __tablename__ = 'puesto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
    menu = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')
    puntuacion_total = db.Column(db.Integer, default=0)
    total_votos = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

# Ruta Principal
@app.route('/')
def index():
    puestos_activos = Puesto.query.filter_by(estado='Aprobado').all()
    return render_template('index.html', puestos=puestos_activos)

# Ruta para registro de nuevos puestos
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nuevo_puesto = Puesto(
            nombre=request.form['nombre'],
            whatsapp=request.form['whatsapp'],
            menu=request.form['menu'],
            estado='Pendiente'
        )
        db.session.add(nuevo_puesto)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('registrar.html')

# Panel de Administración (Contraseña: admin123)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('admin_logged_in'):
        puestos = Puesto.query.all()
        return render_template('admin.html', puestos=puestos)
    
    if request.method == 'POST':
        if request.form.get('password') == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
    return render_template('login_admin.html')

@app.route('/admin/aprobar/<int:id>')
def aprobar_puesto(id):
    if session.get('admin_logged_in'):
        puesto = Puesto.query.get_or_404(id)
        puesto.estado = 'Aprobado'
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/eliminar/<int:id>')
def eliminar_puesto(id):
    if session.get('admin_logged_in'):
        puesto = Puesto.query.get_or_404(id)
        db.session.delete(puesto)
        db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
