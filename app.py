from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_valle_olivos'

# Conexión inteligente a Supabase (Pooler Puerto 6543)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Tu enlace oficial de suscripción de Mercado Pago
LINK_MERCADO_PAGO = "https://www.mercadopago.com.mx/subscriptions/checkout?preapproval_plan_id=79fd4dccfd394703b326586a6463c923"

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
    try:
        db.create_all()
    except Exception:
        pass

@app.route('/')
def index():
    try:
        puestos_activos = Puesto.query.filter_by(estado='Aprobado').all()
    except Exception:
        puestos_activos = []
    return render_template('index.html', puestos=puestos_activos)

@app.route('/vendedor', methods=['GET', 'POST'])
def vendedor():
    if request.method == 'POST':
        try:
            # Captura flexible para asegurar que agarre cualquier nombre de input
            val_nombre = request.form.get('nombre') or request.form.get('negocio') or request.form.get('titulo') or 'Sin Nombre'
            val_whatsapp = request.form.get('whatsapp') or request.form.get('telefono') or request.form.get('celular') or 'Sin Teléfono'
            val_menu = request.form.get('menu') or request.form.get('descripcion') or request.form.get('detalles') or 'Sin Menú'

            # 1. Se registra en la base de datos AL INSTANTE de hacer clic
            nuevo_puesto = Puesto(
                nombre=val_nombre,
                whatsapp=val_whatsapp,
                menu=val_menu,
                estado='Pendiente'
            )
            db.session.add(nuevo_puesto)
            db.session.commit()
            
            # 2. Redirige de inmediato al enlace de pago de Mercado Pago
            return redirect(LINK_MERCADO_PAGO)
        except Exception as e:
            db.session.rollback()
            return f"Error al registrar: {e}", 500
            
    return render_template('vendedor.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('Admin_login.html', error="Contraseña incorrecta")

    if session.get('admin_logged_in'):
        try:
            puestos = Puesto.query.all()
        except Exception as e:
            puestos = []
        return render_template('admin.html', puestos=puestos)
    
    return render_template('Admin_login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    return redirect(url_for('admin'))

@app.route('/admin/aprobar/<int:id>')
def aprobar_puesto(id):
    if session.get('admin_logged_in'):
        try:
            puesto = Puesto.query.get_or_404(id)
            puesto.estado = 'Aprobado'
            db.session.commit()
        except Exception:
            db.session.rollback()
    return redirect(url_for('admin'))

@app.route('/admin/eliminar/<int:id>')
def eliminar_puesto(id):
    if session.get('admin_logged_in'):
        try:
            puesto = Puesto.query.get_or_404(id)
            db.session.delete(puesto)
            db.session.commit()
        except Exception:
            db.session.rollback()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
