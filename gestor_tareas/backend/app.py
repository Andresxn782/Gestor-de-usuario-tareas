from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

# -------------------------
# CONEXIÓN BASE DE DATOS
# -------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="gestor_user",
        password="1234",
        database="gestor_tareas"
    )

# -------------------------
# LOGIN
# -------------------------
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        cursor.close()
        conexion.close()

        if usuario and check_password_hash(usuario["password"], password):

            session["usuario_id"] = usuario["id_usuario"]
            session["rol"] = usuario["rol"]
            session["nombre"] = usuario["nombre"]

            return redirect("/panel")

        else:
            return "Credenciales incorrectas"

    return render_template("login.html")

# -------------------------
# REGISTRO
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    message = ''
    error = False

    if request.method == "POST":

        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        rol = request.form["rol"]

        password_encriptada = generate_password_hash(password)

        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:

            message = "El correo ya está registrado"
            error = True

        else:

            cursor.execute(
                "INSERT INTO usuarios (nombre, email, rol, password) VALUES (%s, %s, %s, %s)",
                (nombre, email, rol, password_encriptada)
            )

            conexion.commit()
            cursor.close()
            conexion.close()

            return redirect("/")

        cursor.close()
        conexion.close()

    return render_template("register.html", message=message, error=error)

# -------------------------
# PANEL USUARIO
# -------------------------
@app.route("/panel")
def panel():

    if "usuario_id" not in session:
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    if session["rol"] == "administrador":

        cursor.execute("""
        SELECT id_usuario, nombre, email
        FROM usuarios
        WHERE rol='trabajador'
        """)

        usuarios = cursor.fetchall()

        cursor.close()
        conexion.close()

        return render_template(
            "panel_admin.html",
            usuarios=usuarios,
            nombre=session["nombre"]
        )

    else:

        cursor.execute("""
        SELECT t.id_tarea, t.nombre, t.descripcion, t.estado
        FROM tareas t
        JOIN usuario_tarea ut ON t.id_tarea = ut.id_tarea
        WHERE ut.id_usuario = %s
        """, (session["usuario_id"],))

        tareas = cursor.fetchall()

        cursor.close()
        conexion.close()

        return render_template(
            "panel_trabajador.html",
            tareas=tareas,
            nombre=session["nombre"]
        )

# -------------------------
# PANEL ADMIN
# -------------------------
@app.route("/admin")
def admin_panel():

    if session.get("rol") != "administrador":
        return redirect("/")

    return render_template("admin_panel.html", nombre=session["nombre"])

# -------------------------
# TAREAS ADMIN
# -------------------------
@app.route("/admin/tareas")
def admin_tareas():

    if session.get("rol") != "administrador":
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM tareas")
    tareas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template("admin_tareas.html", tareas=tareas)

# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)