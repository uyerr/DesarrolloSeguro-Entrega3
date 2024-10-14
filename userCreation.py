import hashlib
import re
import getpass
import mysql.connector
import configparser
import time

# Variable global para la sesión activa
sesion_activa = None

def hashPassword(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validar_usuario(usuario):
    # Eliminar caracteres no alfanuméricos
    usuario = re.sub(r'\W+', '', usuario)
    # Verificar longitud del usuario
    if len(usuario) < 3 or len(usuario) > 15:
        print("Error: El nombre de usuario debe tener entre 3 y 15 caracteres.")
        return None  
    return usuario

def validar_password(password):
    if len(password) < 8:
        print("Error: La contraseña debe tener al menos 8 caracteres.")
        return False
    if not re.search(r'[A-Z]', password):
        print("Error: La contraseña debe contener al menos una letra mayúscula.")
        return False
    if not re.search(r'[a-z]', password):
        print("Error: La contraseña debe contener al menos una letra minúscula.")
        return False
    if not re.search(r'[0-9]', password):
        print("Error: La contraseña debe contener al menos un número.")
        return False
    if not re.search(r'[\W_]', password):  # Cualquier carácter que no sea alfanumérico
        print("Error: La contraseña debe contener al menos un carácter especial.")
        return False
    return True

def registrar():
    usuario = input("Ingrese el nombre de usuario: ")
    usuario = usuario.lower()
    usuario = validar_usuario(usuario)
    
    if not usuario:
        return
    
    user_exists = cursor.execute(f"SELECT EXISTS(SELECT 1 FROM usuarios.credenciales WHERE username = '{usuario}')")
    user_exists = cursor.fetchone()[0]
    if user_exists == 1:
        print("Error: El usuario ya existe.")
        return
    
    while True:
        password = getpass.getpass("Ingrese la contraseña: ")
        password_confirm = getpass.getpass("Confirme la contraseña: ")

        if password != password_confirm:
            print("Error: Las contraseñas no coinciden.")
            continue

        if validar_password(password):
            break
            
    password_hash = hashPassword(password)
    cursor.execute(f"INSERT INTO usuarios.credenciales(username, passwordHash) VALUES (%s,%s)", (usuario, password_hash))
    dbusuarios.commit()
    print(f"Usuario {usuario} creado exitosamente.")

def login():
    global sesion_activa
    if sesion_activa:
        print(f"Ya has iniciado sesión como {sesion_activa}. Debes cerrar sesión primero.")
        return
    
    usuario = input("Ingrese su nombre de usuario: ")
    password = getpass.getpass("Ingrese su contraseña: ")
    usuario = usuario.lower()
    usuario = validar_usuario(usuario)
    
    if not usuario:
        return
    
    user_exists = cursor.execute(f"SELECT EXISTS(SELECT 1 FROM usuarios.credenciales WHERE username = '{usuario}')")
    user_exists = cursor.fetchone()[0]
    if user_exists == 0:
        print(f"Credenciales Incorrectas")
        time.sleep(2)
        return
    
    password_hash = hashPassword(password)
    
    cursor.execute("SELECT * FROM usuarios.credenciales WHERE username = %s AND passwordHash = %s", (usuario, password_hash,))
    account = cursor.fetchone()
    if account and account[1] == password_hash:
        sesion_activa = usuario  # Guardar el usuario en la sesión activa
        print(f"Sesión iniciada con éxito. Bienvenido, {usuario}!")
    else:
        print("Credenciales Incorrectas")
        time.sleep(2)

def logout():
    global sesion_activa
    if sesion_activa:
        print(f"Sesión de {sesion_activa} cerrada.")
        sesion_activa = None  # Cerrar sesión
    else:
        print("No hay ninguna sesión activa.")

def mostrar_usuarios():
    global sesion_activa
    if not sesion_activa:
        print("Error: Debes iniciar sesión para ver los usuarios.")
        return
    
    cursor.execute("SELECT username FROM usuarios.credenciales")
    users = cursor.fetchall()
    if not users:
        print("No hay usuarios registrados")
    else:
        for user in users:
            print(user[0])

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    DB_HOST = config['database']['host']
    DB_USER = config['database']['user']
    DB_PASS = config['database']['password']
    dbusuarios = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASS,
        )
    cursor = dbusuarios.cursor(buffered=True)
        
    db_name = "usuarios"
    db_exists = cursor.execute("SHOW DATABASES")
    db_exists = cursor.fetchall()
    if db_name in [db[0] for db in db_exists]:
        print(f"La base de datos '{db_name}' existe.")
    else:
        print(f"La base de datos '{db_name}' no existe. Creando base de datos '{db_name}'")
        cursor.execute("CREATE DATABASE usuarios")
        dbusuarios = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASS,
        database="usuarios"
    )
        cursor = dbusuarios.cursor(buffered=True)
        cursor.execute("CREATE TABLE credenciales (username VARCHAR(50), passwordHash CHAR(64), userID int PRIMARY KEY AUTO_INCREMENT)")
    
    while True:
        print(f"\nUsuario: {sesion_activa}")
        print("Opciones:")
        print("1. Crear un nuevo usuario")
        print("2. Iniciar sesión")
        print("3. Cerrar sesión")
        print("4. Mostrar usuarios registrados")
        print("5. Salir")
        
        opcion = input("Seleccione una opción: ")
        
        if opcion == '1':
            registrar()
        elif opcion == '2':
            login()
        elif opcion == '3':
            logout()
        elif opcion == '4':
            mostrar_usuarios()
        elif opcion == '5':
            print("Saliendo del programa...")
            break
        else:
            print(f"Opción {opcion} inválida.")
