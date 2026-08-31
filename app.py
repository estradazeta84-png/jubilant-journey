from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# CONFIGURACIÓN IMPORTANTE PARA LAS CONTRASEÑAS (SESSION)
app.secret_key = 'tu_clave_secreta_super_segura' # Puedes cambiar este texto por el que quieras

# Configuración de tu base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo del Puesto
class Puesto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
    menu = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), default='De baja')

with app.app_context():
    db.create_all()

ADMIN_PASSWORD = "Evelin22"

# Página principal (Catálogo para los clientes)
@app.route('/')
def index():
    puestos = Puesto.query.all()
    return render_template('index.html', puestos=puestos)

# Ruta de registro y salto a Mercado Pago
@app.route('/vendedor', methods=['GET', 'POST'])
def vendedor():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        whatsapp = request.form.get('whatsapp')
        menu = request.form.get('menu')
        
        nuevo_puesto = Puesto(
            nombre=nombre, 
            whatsapp=whatsapp, 
            menu=menu, 
            estado='De baja'
        )
        db.session.add(nuevo_puesto)
        db.session.commit()
        
        # Redirigimos al enlace de suscripción de Mercado Pago
        return redirect('https://www.mercadopago.com.mx/subscriptions/checkout?your_subscription_link...')
        
    return render_template('vendedor.html')

# Ruta para iniciar sesión en el Admin
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = "Contraseña incorrecta. Inténtalo de nuevo."
    return render_template('admin_login.html', error=error)

# Panel de administración (Protegido con contraseña)
@app.route('/admin')
def admin():
    # Si no ha iniciado sesión, lo mandamos al login a fuerzas
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
        
    puestos = Puesto.query.all()
    return render_template('admin.html', puestos=puestos)

# Ruta para cerrar sesión del Admin
@app.route('/admin-logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

# Ruta para cambiar el estado (Activo / De baja)
@app.route('/admin/cambiar/<int:id>')
def cambiar_estado(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
        
    puesto = Puesto.query.get_or_404(id)
    if puesto.estado == 'Activo':
        puesto.estado = 'De baja'
    else:
        puesto.estado = 'Activo'
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
