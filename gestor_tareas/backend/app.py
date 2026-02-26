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

            return "Login correcto"

        else:
            return "Credenciales incorrectas"

    return render_template("login.html")


# -------------------------
# REGISTRO
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]

        password_encriptada = generate_password_hash(password)

        conexion = get_db_connection()
        cursor = conexion.cursor()

        try:
            cursor.execute(
                "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)",
                (nombre, email, password_encriptada)
            )
            conexion.commit()
        except:
            return "El email ya existe"

        cursor.close()
        conexion.close()

        return redirect("/")

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)