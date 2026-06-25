from flask import Flask, render_template, request, redirect, session, flash
from firebase_config import db

app = Flask(__name__)
app.secret_key = "reservalab123"
# ==========================
# LOGIN
# ==========================

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/iniciar_sesion", methods=["POST"])
def iniciar_sesion():

    correo = request.form["correo"]
    password = request.form["password"]

    usuarios = db.collection("usuarios").stream()

    for u in usuarios:

        usuario = u.to_dict()

        if (
            usuario["correo"] == correo
            and usuario["password"] == password
        ):

            session["correo"] = usuario["correo"]
            session["nombre"] = usuario["nombre"]
            session["rol"] = usuario["rol"]

            flash("Bienvenido " + usuario["nombre"])

            return redirect("/dashboard")
        
    return "Correo o contraseña incorrectos"

# ==========================
# REGISTRO
# ==========================

@app.route("/registro")
def registro():
    return render_template("registro.html")


@app.route("/registrar", methods=["POST"])
def registrar():

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    password = request.form["password"]
    rol = request.form["rol"]

    usuarios = db.collection("usuarios").stream()

    for u in usuarios:
        usuario = u.to_dict()

        if usuario["correo"] == correo:
            return "Este correo ya está registrado"

    db.collection("usuarios").add({
        "nombre": nombre,
        "correo": correo,
        "password": password,
        "rol": rol
    })

    flash("Usuario registrado correctamente")

    return redirect("/")


# ==========================
# DASHBOARD
# ==========================

@app.route("/dashboard")
def dashboard():

    if "correo" not in session:
        return redirect("/")

    total_recursos = len(list(db.collection("recursos").stream()))
    total_reservas = len(list(db.collection("reservas").stream()))
    total_usuarios = len(list(db.collection("usuarios").stream()))

    return render_template(
        "dashboard.html",
        total_recursos=total_recursos,
        total_reservas=total_reservas,
        total_usuarios=total_usuarios,
        rol=session.get("rol"),
        nombre=session.get("nombre")
    )


# ==========================
# RECURSOS
# ==========================

@app.route("/recursos")
def recursos():

    if session.get("rol") != "admin":
      return "Acceso denegado"

    texto_busqueda = request.args.get("buscar", "").lower()

    docs = db.collection("recursos").stream()

    recursos = []

    for d in docs:

        recurso = {
            "id": d.id,
            **d.to_dict()
        }

        if texto_busqueda:

            if texto_busqueda in recurso["nombre"].lower():
                recursos.append(recurso)

        else:
            recursos.append(recurso)

    return render_template(
        "recursos.html",
        recursos=recursos
    )


@app.route("/crear", methods=["POST"])
def crear():

    if session.get("rol") != "admin":
       return "Acceso denegado"

    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    estado = request.form["estado"]

    db.collection("recursos").add({
        "nombre": nombre,
        "descripcion": descripcion,
        "estado": estado
    })

    flash("Recurso creado correctamente")
    return redirect("/recursos")


@app.route("/eliminar/<id>")
def eliminar(id):

    if session.get("rol") != "admin":
       return "Acceso denegado"

    db.collection("recursos").document(id).delete()

    flash("Recurso eliminado correctamente")
    return redirect("/recursos")


@app.route("/editar/<id>")
def editar(id):

    if session.get("rol") != "admin":
       return "Acceso denegado"

    doc = db.collection("recursos").document(id).get()

    return render_template(
        "editar.html",
        recurso=doc.to_dict(),
        id=id
    )


@app.route("/actualizar/<id>", methods=["POST"])
def actualizar(id):

    db.collection("recursos").document(id).update({
        "nombre": request.form["nombre"],
        "descripcion": request.form["descripcion"],
        "estado": request.form["estado"]
    })

    return redirect("/recursos")


# ==========================
# RESERVAS
# ==========================

@app.route("/reservas")
def reservas():

    docs = db.collection("reservas").stream()

    reservas = []

    for d in docs:
        reservas.append({
            "id": d.id,
            **d.to_dict()
        })

    return render_template(
        "reservas.html",
        reservas=reservas
    )


@app.route("/crear_reserva", methods=["POST"])
def crear_reserva():

    usuario = session.get("nombre")

    recurso = request.form["recurso"]
    fecha = request.form["fecha"]
    hora = request.form["hora"]

    reservas = db.collection("reservas").stream()

    for r in reservas:

        reserva = r.to_dict()

        if (
            reserva["recurso"] == recurso
            and reserva["fecha"] == fecha
            and reserva["hora"] == hora
        ):
            return "ERROR: Ese recurso ya está reservado en esa fecha y hora."

    db.collection("reservas").add({
        "usuario": usuario,
        "recurso": recurso,
        "fecha": fecha,
        "hora": hora,
        "estado": "Activa"
    })

    flash("Reserva creada correctamente")
    return redirect("/reservas")


@app.route("/editar_reserva/<id>")
def editar_reserva(id):

    doc = db.collection("reservas").document(id).get()

    return render_template(
        "editar_reserva.html",
        reserva=doc.to_dict(),
        id=id
    )


@app.route("/actualizar_reserva/<id>", methods=["POST"])
def actualizar_reserva(id):

    db.collection("reservas").document(id).update({
        "usuario": request.form["usuario"],
        "recurso": request.form["recurso"],
        "fecha": request.form["fecha"],
        "hora": request.form["hora"]
    })

    return redirect("/reservas")

@app.route("/cancelar_reserva/<id>")
def cancelar_reserva(id):

    db.collection("reservas").document(id).update({
        "estado": "Cancelada"
    })

    flash("Reserva cancelada correctamente")
    return redirect("/reservas")


@app.route("/mis_reservas")
def mis_reservas():

    nombre = session.get("nombre")

    docs = db.collection("reservas").stream()

    reservas = []

    for d in docs:

        reserva = d.to_dict()

        if reserva["usuario"] == nombre:

            reservas.append({
                "id": d.id,
                **reserva
            })

    return render_template(
        "mis_reservas.html",
        reservas=reservas
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/registro")

# ==========================
# EJECUTAR APP
# ==========================

if __name__ == "__main__":
    app.run(debug=True)