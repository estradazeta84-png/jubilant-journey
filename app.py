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
    puestos = []
    try:
        todos = Puesto.query.all()
        puestos = [p for p in todos if p.estado and p.estado.strip().lower() == 'aprobado']
    except Exception:
        puestos = []

    html_tarjetas = ""
    for p in puestos:
        tel_limpio = "".join(filter(str.isdigit, p.whatsapp))
        mensaje_wa = f"Hola, me interesa información sobre su menú: {p.menu}"
        link_whatsapp = f"https://wa.me/52{tel_limpio}?text={mensaje_wa}" if len(tel_limpio) >= 10 else f"https://wa.me/{tel_limpio}"

        promedio = 0.0
        if p.total_votos and p.total_votos > 0:
            promedio = round(p.puntuacion_total / p.total_votos, 1)

        html_tarjetas += f"""
        <div style="background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid #28a745;">
            <h3 style="margin: 0 0 10px 0; color: #333;">{p.nombre}</h3>
            <p style="margin: 5px 0; color: #666;"><strong>Menú / Detalles:</strong> {p.menu}</p>
            
            <div style="background: #fdf8e2; padding: 10px; border-radius: 5px; margin: 15px 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="font-size: 18px; font-weight: bold; color: #f39c12;">⭐ {promedio} / 5.0</span>
                    <span style="color: #666; font-size: 13px; margin-left: 5px;">({p.total_votos} votos)</span>
                </div>
                <form action="/votar/{p.id}" method="POST" style="display: flex; gap: 5px; align-items: center; margin-top: 5px;">
                    <select name="estrellas" style="padding: 5px; border-radius: 4px; border: 1px solid #ccc;">
                        <option value="5">⭐⭐⭐⭐⭐ (5)</option>
                        <option value="4">⭐⭐⭐⭐ (4)</option>
                        <option value="3">⭐⭐⭐ (3)</option>
                        <option value="2">⭐⭐ (2)</option>
                        <option value="1">⭐ (1)</option>
                    </select>
                    <button type="submit" style="background: #f39c12; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; cursor: pointer;">Calificar</button>
                </form>
            </div>

            <div>
                <a href="{link_whatsapp}" target="_blank" style="background: #25d366; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                    Pedir por WhatsApp 📱
                </a>
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Valle de los Olivos - Directorio</title>
    </head>
    <body style="font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px;">
        <div style="max-width: 800px; margin: auto;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #333;">🍽️ Valle de los Olivos</h1>
                <p style="color: #666;">Descubre los mejores puestos de comida calificados por la comunidad.</p>
                <a href="/vendedor" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 10px;">Registrar mi Puesto 🚀</a>
            </div>
            
            <h2 style="color: #444; border-bottom: 2px solid #ddd; padding-bottom: 5px;">Puestos Disponibles</h2>
            <div style="margin-top: 20px;">
                {html_tarjetas if html_tarjetas else '<p style="text-align: center; color: #777; background: white; padding: 30px; border-radius: 8px;">No hay puestos aprobados en este momento. Vuelve pronto o registra el tuyo.</p>'}
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/votar/<int:id>', methods=['POST'])
def votar(id):
    try:
        estrellas = int(request.form.get('estrellas', 5))
        if 1 <= estrellas <= 5:
            puesto = Puesto.query.get(id)
            if puesto:
                puesto.puntuacion_total = (puesto.puntuacion_total or 0) + estrellas
                puesto.total_votos = (puesto.total_votos or 0) + 1
                db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_for('index'))

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
            estado_color = 'green' if p.estado and p.estado.strip().lower() == 'aprobado' else 'orange'
            promedio = round(p.puntuacion_total / p.total_votos, 1) if p.total_votos > 0 else 0.0
            html_puestos += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">{p.id}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{p.nombre}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{p.whatsapp}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{p.menu}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">⭐ {promedio} ({p.total_votos} votos)</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: {estado_color};">{p.estado}</td>
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
                            <th style="padding: 10px; border: 1px solid #ddd;">Menú</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Calificación</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Estado</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {html_puestos if html_puestos else '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #777;">No hay puestos registrados todavía.</td></tr>'}
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
