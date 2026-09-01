from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_valle_olivos'

# Configuración de la base de datos SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Puestos
class Puesto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
    menu = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), default='Pendiente') # Pendiente, Activo o Pausa
    puntuacion_total = db.Column(db.Integer, default=0)
    total_votos = db.Column(db.Integer, default=0)

# Crear la base de datos automáticamente al iniciar
with app.app_context():
    db.create_all()

# Ruta Principal (Catálogo)
@app.route('/')
def index():
    puestos = Puesto.query.all()
    return render_template('index.html', puestos=puestos)

# Ruta para Registro de Nuevos Vendedores (Redirige a Mercado Pago)
@app.route('/vendedor', methods=['GET', 'POST'])
def vendedor():
    if request.method == 'POST':
        nombre = request.form['nombre']
        whatsapp = request.form['whatsapp']
        menu = request.form['menu']
        
        # Se registra como 'Pendiente' hasta que efectúe el pago
        nuevo_puesto = Puesto(nombre=nombre, whatsapp=whatsapp, menu=menu, estado='Pendiente')
        db.session.add(nuevo_puesto)
        db.session.commit()
        
        # Redirección directa al link de Mercado Pago configurado
        return redirect('https://mpago.la/2a5y92U')
        
    return render_template('vendedor.html')

# Ruta para Calificar un Puesto con Estrellas
@app.route('/calificar/<int:id>', methods=['POST'])
def calificar(id):
    puesto = Puesto.query.get_or_404(id)
    estrellas = int(request.form['estrellas'])
    
    puesto.puntuacion_total += estrellas
    puesto.total_votos += 1
    db.session.commit()
    
    return redirect(url_for('index'))

# Login de Administrador
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form['password']
        if password == 'Evelin22':
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = 'Contraseña incorrecta'
    return render_template('admin_login.html', error=error)

# Panel de Administración
@app.route('/admin')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    puestos = Puesto.query.all()
    return render_template('admin.html', puestos=puestos)

# Cambiar Estado de Puesto (Activar / Pausar)
@app.route('/admin/cambiar/<int:id>')
def cambiar_estado(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    puesto = Puesto.query.get_or_404(id)
    if puesto.estado == 'Activo':
        puesto.estado = 'Pausa'
    else:
        puesto.estado = 'Activo'
    
    db.session.commit()
    return redirect(url_for('admin_panel'))

# Cerrar Sesión Admin
@app.route('/admin-logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
