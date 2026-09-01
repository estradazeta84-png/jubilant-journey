from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_valle_olivos'

# Configuración inteligente para conectar con Supabase (Puerto 6543 Pooler)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Tu enlace oficial de Mercado Pago
LINK_MERCADO_PAGO = "https://link.mercadopago.com.mx/valledelosolivos"  # (O pon tu link exacto aquí si cambia)

# Modelo de Puestos actualizado con soporte completo para PostgreSQL
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

# 1. Página Principal
@app.route('/')
def index():
    try:
        puestos_activos = Puesto.query.filter_by(estado='Aprobado').all()
    except Exception:
        puestos_activos = []
    return render_template('index.html', puestos=puestos_activos)

# 2. Página de Vendedor: Guarda el registro y redirige directo a Mercado Pago
@app.route('/vendedor', methods=['GET', 'POST'])
def vendedor():
    if request.method == 'POST':
        try:
            nuevo_puesto = Puesto(
                nombre=request.form['nombre'],
                whatsapp=request.form['whatsapp'],
                menu=request.form['menu'],
                estado='Pendiente'
            )
            db.session.add(nuevo_puesto)
            db.session.commit()
            # Redirige al usuario al enlace de pago de Mercado Pago
            return redirect(LINK_MERCADO_PAGO)
        except Exception as e:
            db.session.rollback()
            return f"Hubo un error al registrar: {e}", 500
            
    return render_template('vendedor.html')

# 3. Panel de Administración (Soporta plantilla admin.html)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('admin_logged_in'):
        try:
            puestos = Puesto.query.all()
        except Exception:
            puestos = []
        return render_template('admin.html', puestos=puestos)
    
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin123':  # Puedes cambiar tu contraseña de admin aquí
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('Admin_login.html', error="Contraseña incorrecta")
            
    return render_template('Admin_login.html')

# Ruta por si entran con minúsculas
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    return redirect(url_for('admin'))

# Aprobar Puesto desde Admin
@app.route('/admin/aprobar/<int:id>')
def aprobar_puesto(id):
    if session.get('admin_logged_in'):
        puesto = Puesto.query.get_or_404(id)
        puesto.estado = 'Aprobado'
        db.session.commit()
    return redirect(url_for('admin'))

# Eliminar Puesto desde Admin
@app.route('/admin/eliminar/<int:id>')
def eliminar_puesto(id):
    if session.get('admin_logged_in'):
        puesto = Puesto.query.get_or_404(id)
        db.session.delete(puesto)
        db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
