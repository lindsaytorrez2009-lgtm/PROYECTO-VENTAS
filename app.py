from flask import Flask, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from conexion import conexion, cursor

app = Flask(__name__)
app.secret_key = "123456"

@app.route("/")
def inicio():
    if "correo" not in session:
        return redirect("/login")
    
    cursor.execute("SELECT * FROM productos")
    productos_guardados = cursor.fetchall()
    return render_template("index.html", productos=productos_guardados)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        clave = request.form["clave"]

        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        usuario_encontrado = cursor.fetchone()

        if usuario_encontrado:
            clave_bd = usuario_encontrado[2]
            if check_password_hash(clave_bd, clave):
                session["id_usuario"] = usuario_encontrado[0]
                session["correo"] = usuario_encontrado[1]
                session["rol"] = usuario_encontrado[3]
                return redirect("/")

        flash("Correo o contraseña incorrectos")
        return redirect("/login")

    return render_template("login.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        correo = request.form.get("correo")
        clave = request.form.get("clave")
        
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        if cursor.fetchone():
            flash("Este correo ya está registrado")
            return redirect("/registro")
        
        clave_encriptada = generate_password_hash(clave)
        sql = "INSERT INTO usuarios(correo, clave, rol) VALUES(%s, %s, %s)"
        
        try:
            cursor.execute(sql, (correo, clave_encriptada, "Cliente"))
            conexion.commit()
            session["correo"] = correo
            return redirect("/")
        except Exception as e:
            flash(f"Error al registrar: {str(e)}")
            return redirect("/registro")
            
    return render_template("registro.html")

@app.route("/registrar-producto")
def registrar_producto():
    if "correo" not in session:
        return redirect("/login")
    return render_template("ver_productos.html")

@app.route("/guardar", methods=["POST"])
def guardar():
    if "correo" not in session:
        return redirect("/login")

    nombre = request.form["nombre"]
    precio = request.form["precio"]
    stock = request.form["stock"]
    imagen_url = request.form["imagen_url"]

    sql = "INSERT INTO productos(nombre, precio, stock, imagen) VALUES(%s, %s, %s, %s)"
    cursor.execute(sql, (nombre, precio, stock, imagen_url))
    conexion.commit()
    
    flash("Producto guardado correctamente")
    return redirect("/")

@app.route("/eliminar/<int:id>")
def eliminar(id):
    if "correo" not in session:
        return redirect("/login")
        
    try:
        sql = "DELETE FROM productos WHERE id_producto = %s"
        cursor.execute(sql, (id,))
    except Exception:
        sql = "DELETE FROM productos WHERE id = %s"
        cursor.execute(sql, (id,))
        
    conexion.commit()
    flash("Producto eliminado correctamente")
    return redirect("/")

@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    if "correo" not in session:
        return redirect("/login")
        
    nuevo_nombre = request.form["nombre"]
    nuevo_precio = request.form["precio"]
    
    try:
        sql = "UPDATE productos SET nombre = %s, precio = %s WHERE id_producto = %s"
        cursor.execute(sql, (nuevo_nombre, nuevo_precio, id))
    except Exception:
        sql = "UPDATE productos SET nombre = %s, precio = %s WHERE id = %s"
        cursor.execute(sql, (nuevo_nombre, nuevo_precio, id))
        
    conexion.commit()
    flash("Producto actualizado correctamente")
    return redirect("/")

# 🌟 RUTA ULTRA BLINDADA PARA DETECTAR ERRORES DE IMAGEN EN LA BD 🌟
@app.route("/editar-imagen/<int:id>", methods=["POST"])
def editar_imagen(id):
    if "correo" not in session:
        return redirect("/login")
        
    nueva_url = request.form["imagen_url"].strip()
    print(f"\n[SISTEMA] Intentando cambiar la imagen del producto {id} a: {nueva_url}")
    
    # Intento 1: usando id_producto
    try:
        sql = "UPDATE productos SET imagen = %s WHERE id_producto = %s"
        cursor.execute(sql, (nueva_url, id))
        conexion.commit()
        print("[SISTEMA] Éxito: Se actualizó usando la columna 'id_producto'")
        flash("Imagen del producto actualizada")
        return redirect("/")
    except Exception as e:
        print(f"[SISTEMA] Falló 'id_producto'. Error: {str(e)}. Intentando con columna 'id'...")

    # Intento 2 de emergencia: usando id
    try:
        sql = "UPDATE productos SET imagen = %s WHERE id = %s"
        cursor.execute(sql, (nueva_url, id))
        conexion.commit()
        print("[SISTEMA] Éxito: Se actualizó usando la columna 'id'")
        flash("Imagen del producto actualizada")
    except Exception as e2:
        print(f"[SISTEMA] ¡ERROR CRÍTICO! Ninguna columna funcionó. Detalle: {str(e2)}")
        flash("Error al actualizar la imagen en la base de datos")
        
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__=="__main__":
    app.run(debug=True)