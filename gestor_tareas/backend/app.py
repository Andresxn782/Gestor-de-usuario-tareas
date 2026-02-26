# Importamos las librerías necesarias
from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

# Creamos la aplicación Flask
app = Flask(__name__)

# Clave secreta necesaria para usar sesiones (session)
app.secret_key = "clave_super_secreta"


# -------------------------------------------------
# FUNCIÓN PARA CONECTARSE A LA BASE DE DATOS
# -------------------------------------------------
def get_db_connection():
    # Devuelve una nueva conexión a MySQL
    return mysql.connector.connect(
        host="localhost",          # Servidor de la base de datos
        user="gestor_user",        # Usuario de MySQL
        password="1234",           # Contraseña de MySQL
        database="gestor_tareas"   # Nombre de la base de datos
    )


# -------------------------------------------------
# LOGIN
# -------------------------------------------------
@app.route("/", methods=["GET", "POST"])  # Ruta principal
def login():

    # Si el usuario envía el formulario (POST)
    if request.method == "POST":
        # Capturamos los datos del formulario
        email = request.form["email"]
        password = request.form["password"]

        # Abrimos conexión a la base de datos
        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)
        # dictionary=True hace que los resultados sean diccionarios

        # Buscamos el usuario por su email
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()  # Obtenemos un solo resultado

        # Cerramos conexión
        cursor.close()
        conexion.close()

        # Verificamos que el usuario exista y que la contraseña sea correcta
        if usuario and check_password_hash(usuario["password"], password):

            # Guardamos datos del usuario en la sesión
            session["usuario_id"] = usuario["id_usuario"]
            session["rol"] = usuario["rol"]
            session["nombre"] = usuario["nombre"]

            # Redirigimos al panel
            return redirect("/panel")
        else:
            # Si falla el login
            return "Credenciales incorrectas"

    # Si es método GET, mostramos el formulario de login
    return render_template("login.html")


# -------------------------------------------------
# REGISTRO
# -------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    message = ''  # Mensaje para mostrar en el HTML
    error = False # Variable para indicar si hay error

    # Si el usuario envía el formulario
    if request.method == "POST":

        # Capturamos los datos del formulario
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        rol = request.form["rol"]  # Rol (administrador o trabajador)

        # Encriptamos la contraseña antes de guardarla
        password_encriptada = generate_password_hash(password)

        # Conectamos a la base de datos
        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)

        # Verificamos si el email ya está registrado
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Si ya existe, mostramos error
            message = "El correo ya está registrado"
            error = True
        else:
            # Insertamos el nuevo usuario en la base de datos
            cursor.execute(
                "INSERT INTO usuarios (nombre, email, rol, password) VALUES (%s, %s, %s, %s)",
                (nombre, email, rol, password_encriptada)
            )

            # Guardamos cambios
            conexion.commit()

            # Cerramos conexión
            cursor.close()
            conexion.close()

            # Redirigimos al login
            return redirect("/")

        # Cerramos conexión si hubo error
        cursor.close()
        conexion.close()

    # Mostramos el formulario de registro
    return render_template("register.html", message=message, error=error)


# -------------------------------------------------
# PANEL DE USUARIO
# -------------------------------------------------
@app.route("/panel")
def panel():

    # Verificamos que haya un usuario logueado
    if "usuario_id" not in session:
        return redirect("/")  # Si no hay sesión, vuelve al login

    # Conectamos a la base de datos
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    # Si el usuario es administrador
    if session["rol"] == "administrador":

        # Consulta para obtener todos los trabajadores
        cursor.execute(
            "SELECT id_usuario, nombre, email, rol FROM usuarios WHERE rol='trabajador'"
        )
        usuarios = cursor.fetchall()

        # Cerramos conexión
        cursor.close()
        conexion.close()

        # Mostramos el panel de administrador
        return render_template(
            "panel_admin.html",
            usuarios=usuarios,
            nombre=session["nombre"]
        )

    else:
        # Si es trabajador, mostramos solo sus tareas

        cursor.execute("""
            SELECT t.id_tarea, t.nombre, t.descripcion, t.estado
            FROM tareas t
            JOIN usuario_tarea ut ON t.id_tarea = ut.id_tarea
            WHERE ut.id_usuario = %s
        """, (session["usuario_id"],))

        tareas = cursor.fetchall()

        # Cerramos conexión
        cursor.close()
        conexion.close()

        # Mostramos el panel del trabajador
        return render_template(
            "panel_trabajador.html",
            tareas=tareas,
            nombre=session["nombre"]
        )


# -------------------------------------------------
# EJECUTAR LA APLICACIÓN
# -------------------------------------------------
if __name__ == "__main__":
    # debug=True recarga automáticamente y muestra errores detallados
    app.run(debug=True)
