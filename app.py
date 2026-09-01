from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_valle_olivos'

# Conexión a Base de Datos
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
    puestos_activos = []
    try:
        puestos_activos = Puesto.query.filter_by(estado='Aprobado').all()
    except Exception:
        pass
    return render_template('index.html', puestos=puestos_activos)

@app.route('/vendedor', methods=['GET', 'POST'])
def vendedor():
    if request.method == 'POST':
        val_nombre = request.form.get('nombre') or request.form.get('negocio') or 'Sin Nombre'
        val_whatsapp = request.form.get('whatsapp') or request.form.get('telefono') or 'Sin Teléfono'
        val_menu = request.form.get('menu') or request.form.get('descripcion') or 'Sin Menú'

        try:
            nuevo_puesto = Puesto(
                nombre=val_nombre,
                whatsapp=val_whatsapp,
                menu=val_menu,
                estado='Pendiente'
            )
            db.session.add(nuevo_puesto)
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        return redirect(LINK_MERCADO_PAGO)
            
    return render_template('vendedor.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # Contraseña actualizada a Evelin22
        if request.form.get('password') == 'Evelin22':
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return '''
            <div style="font-family: Arial; text-align: center; margin-top: 50px;">
                <h2 style="color: red;">Contraseña Incorrecta</h2>
                <a href="/admin">Intentar de nuevo</a>
            </div>
            '''

    if session.get('admin_logged_in'):
        puestos = []
        try:
            puestos = Puesto.query.all()
        except Exception:
            puestos = []
            
        html_puestos = ""
        for p in puestos:
            html_puestos += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">{p.id}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{p.nombre}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{p.whatsapp}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{p.menu}</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: {'green' if p.estado == 'Aprobado' else 'orange'};">{p.estado}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">
                    <a href="/admin/aprobar/{p.id}" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; margin-right: 5px;">Aprobar</a>
                    <a href="/admin/eliminar/{p.id}" style="background: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px;" onclick="return confirm('¿Seguro que deseas eliminarlo?');">Eliminar</a>
                </td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Panel de Administración - Valle de los Olivos</title>
        </head>
        <body style="font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px;">
            <div style="max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                <h1 style="color: #333; text-align: center;">Panel de Administración</h1>
                <p style="text-align: right;"><a href="/admin/logout" style="color: red; text-decoration: none; font-weight: bold;">Cerrar Sesión</a></p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <h3 style="color: #555;">Registros de Vendedores / Puestos</h3>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <thead>
                        <tr style="background: #007bff; color: white;">
                            <th style="padding: 10px; border: 1px solid #ddd;">ID</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Nombre</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">WhatsApp</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Menú / Detalles</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Estado</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {html_puestos if html_puestos else '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #777;">No hay puestos registrados todavía.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
    
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head><title>Admin Login</title></head>
    <body style="font-family: Arial; background: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
        <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); width: 300px; text-align: center;">
            <h2 style="color: #333; margin-bottom: 20px;">Acceso Administrador</h2>
            <form method="POST">
                <input type="password" name="password" placeholder="Contraseña" required style="width: 90%; padding: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px;">
                <br>
                <button type="submit" style="width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer;">Entrar</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))

@app.route('/admin/aprobar/<int:id>')
def aprobar_puesto(id):
    if session.get('admin_logged_in'):
        try:
            puesto = Puesto.query.get(id)
            if puesto:
                puesto.estado = 'Aprobado'
                db.session.commit()
        except Exception:
            db.session.rollback()
    return redirect(url_for('admin'))

@app.route('/admin/eliminar/<int:id>')
def eliminar_puesto(id):
    if session.get('admin_logged_in'):
        try:
            puesto = Puesto.query.get(id)
            if puesto:
                db.session.delete(puesto)
                db.session.commit()
        except Exception:
            db.session.rollback()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
