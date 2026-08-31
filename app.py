from datetime import datetime, timedelta
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

# Tu link de Mercado Pago configurado
LINK_MERCADO_PAGO = "https://mpago.la/2sMGSE4"

# Base de datos completamente limpia (sin puestos falsos)
puestos_db = []


# 1. VISTA DE CLIENTES (Catálogo limpio y estatus automático por vencimiento de 7 días)
@app.route("/")
def index():
    hoy = datetime.now()
    # Si la semana de pago venció, pasa automáticamente el estado a 'De baja' (bloqueado)
    for puesto in puestos_db:
        if puesto["estado"] == "Activo" and puesto["vence"] < hoy:
            puesto["estado"] = "De baja"

    return render_template("index.html", puestos=puestos_db)


# 2. VISTA DE REGISTRO PARA VENDEDORES (Paso 1: Pagar y enviar datos)
@app.route("/vendedor", methods=["GET", "POST"])
def vendedor():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        detalle = request.form.get("detalle")
        telefono = request.form.get("telefono")

        # El nuevo puesto entra como "Pendiente" hasta que verifiques su pago en Mercado Pago
        nuevo_puesto = {
            "id": len(puestos_db) + 1,
            "nombre": nombre,
            "detalle": detalle,
            "telefono": telefono,
            "estado": "Pendiente",
            "vence": datetime.now()
            + timedelta(days=7),  # Se activará al aprobarse en el panel
        }
        puestos_db.append(nuevo_puesto)
        return redirect(url_for("pago_exitoso", nombre=nombre))

    return render_template("vendedor.html", link_mp=LINK_MERCADO_PAGO)


# 3. PÁGINA INTERMEDIA DE INSTRUCCIÓN DE PAGO
@app.route("/aviso-pago/<nombre>")
def pago_exitoso(nombre):
    return render_template(
        "aviso_pago.html", nombre=nombre, link_mp=LINK_MERCADO_PAGO
    )


# 4. PANEL DE ADMINISTRADOR (Para ti: aprobar pagos, renovar 7 días o bloquear cuentas)
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        puesto_id = int(request.form.get("puesto_id"))
        accion = request.form.get("accion")  # 'aprobar', 'renovar', o 'baja'

        for p in puestos_db:
            if p["id"] == puesto_id:
                if accion == "aprobar" or accion == "renovar":
                    p["estado"] = "Activo"
                    p["vence"] = (
                        datetime.now() + timedelta(days=7)
                    )  # Extiende 7 días más la vigencia
                elif accion == "baja":
                    p["estado"] = "De baja"

        return redirect(url_for("admin"))

    return render_template("admin.html", puestos=puestos_db)


if __name__ == "__main__":
    app.run(debug=True)