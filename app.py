from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuración de tu base de datos (ajusta si usas otra ruta)
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
        
        # 1. Guardamos los datos de inmediato en la base de datos
        nuevo_puesto = Puesto(
            nombre=nombre, 
            whatsapp=whatsapp, 
            menu=menu, 
            estado='De baja'
        )
        db.session.add(nuevo_puesto)
        db.session.commit()
        
        # 2. Redirigimos al enlace de suscripción de Mercado Pago
        # (Reemplaza este enlace con tu link real de Mercado Pago)
        return redirect('https://www.mercadopago.com.mx/subscriptions/checkout?your_subscription_link...')
        
    return render_template('vendedor.html')

# Panel de administración oculto
@app.route('/admin')
def admin():
    puestos = Puesto.query.all()
    return render_template('admin.html', puestos=puestos)

# Ruta para cambiar el estado (Activo / De baja)
@app.route('/admin/cambiar/<int:id>')
def cambiar_estado(id):
    puesto = Puesto.query.get_or_404(id)
    if puesto.estado == 'Activo':
        puesto.estado = 'De baja'
    else:
        puesto.estado = 'Activo'
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
