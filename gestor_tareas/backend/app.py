from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

# Conexión a la base de datos
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

            return redirect("/panel")  # redirige al panel según rol
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
        rol = request.form["rol"]  # capturamos el rol

        password_encriptada = generate_password_hash(password)

        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)

        # Verificar si el email ya existe
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
            return redirect("/")  # redirige al login

        cursor.close()
        conexion.close()

    return render_template("register.html", message=message, error=error)


# -------------------------
# PANEL DE USUARIO
# -------------------------
@app.route("/panel")
def panel():
    # Verificar si hay usuario logueado
    if "usuario_id" not in session:
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    if session["rol"] == "administrador":
        # Administrador ve todos los trabajadores
        cursor.execute("SELECT id_usuario, nombre, email, rol FROM usuarios WHERE rol='trabajador'")
        usuarios = cursor.fetchall()
        cursor.close()
        conexion.close()
        return render_template("panel_admin.html", usuarios=usuarios, nombre=session["nombre"])

    else:
        # Trabajador ve solo sus propias tareas
        cursor.execute("""
            SELECT t.id_tarea, t.nombre, t.descripcion, t.estado
            FROM tareas t
            JOIN usuario_tarea ut ON t.id_tarea = ut.id_tarea
            WHERE ut.id_usuario = %s
        """, (session["usuario_id"],))
        tareas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return render_template("panel_trabajador.html", tareas=tareas, nombre=session["nombre"])


if __name__ == "__main__":
    app.run(debug=True)