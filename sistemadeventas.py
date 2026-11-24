import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
DB_NOMBRE = "sistema_ventas.db"


def conectar_db(nombre_db=DB_NOMBRE):
    """Abre (o crea, si no existe) la base de datos SQLite y devuelve la conexión."""
    return sqlite3.connect(nombre_db)


def crear_tablas(conn):
    """Crea las tablas Productos y Ventas si todavía no existen."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Productos (
            id_producto     INTEGER PRIMARY KEY,
            nombre          TEXT NOT NULL,
            categoria       TEXT NOT NULL,
            precio_unitario REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ventas (
            id_venta    INTEGER PRIMARY KEY,
            id_producto INTEGER NOT NULL,
            cantidad    INTEGER NOT NULL,
            fecha       TEXT NOT NULL,
            FOREIGN KEY (id_producto) REFERENCES Productos (id_producto)
        )
    """)

    conn.commit()


def cargar_datos_iniciales(conn):
    """Inserta 15 productos y 18 ventas de prueba.
    INSERT OR IGNORE evita duplicados si el script se ejecuta más de una vez
    (los ids explícitos ya existen y se omiten)."""
    productos = [
        (1,  "Notebook",          "Electrónica", 850000.0),
        (2,  "Mouse inalámbrico", "Electrónica", 15000.0),
        (3,  "Teclado mecánico",  "Electrónica", 45000.0),
        (4,  "Auriculares",       "Electrónica", 38000.0),
        (5,  "Monitor 24 pulgadas", "Electrónica", 210000.0),
        (6,  "Escritorio",        "Muebles",     120000.0),
        (7,  "Silla ergonómica",  "Muebles",     180000.0),
        (8,  "Estantería",        "Muebles",     75000.0),
        (9,  "Cuaderno A4",       "Papelería",   3500.0),
        (10, "Birome (pack x10)", "Papelería",   2800.0),
        (11, "Resma de papel",    "Papelería",   9500.0),
        (12, "Agenda 2026",       "Papelería",   6200.0),
        (13, "Mochila",           "Accesorios",  32000.0),
        (14, "Botella térmica",   "Accesorios",  18000.0),
        (15, "Lámpara de escritorio", "Accesorios", 22000.0),
    ]

    ventas = [
        (1,  1,  1, "2026-09-01"),
        (2,  2,  5, "2026-09-02"),
        (3,  3,  2, "2026-09-03"),
        (4,  4,  3, "2026-09-05"),
        (5,  5,  2, "2026-09-07"),
        (6,  6,  1, "2026-09-08"),
        (7,  7,  2, "2026-09-10"),
        (8,  8,  4, "2026-09-12"),
        (9,  9,  20, "2026-09-14"),
        (10, 10, 15, "2026-09-15"),
        (11, 11, 10, "2026-09-18"),
        (12, 12, 8, "2026-09-20"),
        (13, 13, 6, "2026-09-22"),
        (14, 14, 9, "2026-09-25"),
        (15, 15, 4, "2026-09-27"),
        (16, 2,  3, "2026-10-01"),
        (17, 9,  12, "2026-10-03"),
        (18, 13, 5, "2026-10-05"),
    ]

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT OR IGNORE INTO Productos VALUES (?, ?, ?, ?)", productos
    )
    cursor.executemany(
        "INSERT OR IGNORE INTO Ventas VALUES (?, ?, ?, ?)", ventas
    )
    conn.commit()

def cargar_dataframes(conn):
    """Lee las tablas de la base y las devuelve como DataFrames."""
    df_productos = pd.read_sql_query("SELECT * FROM Productos", conn)
    df_ventas = pd.read_sql_query("SELECT * FROM Ventas", conn)
    return df_productos, df_ventas


def crear_df_maestro(df_productos, df_ventas):
    """Une ventas y productos, limpia los datos y calcula total_venta."""
    # 1. merge por id_producto
    df_maestro = pd.merge(
        df_productos,
        df_ventas,
        on="id_producto",
        how="inner"
    )

    # 2. eliminar duplicados
    df_maestro = df_maestro.drop_duplicates()

    # 3. verificar nulos (mostrar cuántos hay por columna) y eliminarlos
    print("Valores nulos por columna:")
    print(df_maestro.isnull().sum())
    df_maestro = df_maestro.dropna()

    # 4. nueva columna: cantidad * precio_unitario
    df_maestro["total_venta"] = df_maestro["cantidad"] * df_maestro["precio_unitario"]

    return df_maestro

def calcular_estadisticas(df_maestro):
    """Calcula el ingreso total y las estadísticas de las cantidades vendidas."""
    # Ingreso total de la tienda
    ingreso_total = np.sum(df_maestro["total_venta"])

    # Promedio de cantidades vendidas
    promedio_cantidad = np.mean(df_maestro["cantidad"])

    # Mediana de cantidades vendidas
    mediana_cantidad = np.median(df_maestro["cantidad"])

    # Desviación estándar (poblacional, que es el valor por defecto de NumPy)
    desviacion_cantidad = np.std(df_maestro["cantidad"])

    # Mostrar los resultados
    print("Ingreso total:", ingreso_total)
    print("Promedio de cantidades vendidas:", promedio_cantidad)
    print("Mediana de cantidades vendidas:", mediana_cantidad)
    print("Desviación estándar:", desviacion_cantidad)

def graficar_facturacion(df_maestro):
    # Agrupar las ventas y sumar el importe por categoría
    facturacion = df_maestro.groupby("categoria")["total_venta"].sum()

    # Crear el gráfico de barras
    plt.bar(facturacion.index, facturacion.values, color="skyblue")

    # Agregar título y nombres a los ejes
    plt.title("Facturación total por categoría")
    plt.xlabel("Categoría de producto")
    plt.ylabel("Total facturado")

    # Mejorar la lectura de los nombres de las categorías
    plt.xticks(rotation=45)

    # Ajustar los espacios para evitar que se corten las etiquetas
    plt.tight_layout()

    # Guardar el gráfico como imagen PNG
    plt.savefig("facturacion_por_categoria.png")

    # Cerrar la figura
    plt.close()




def main():
    conn = conectar_db()
    try:
        crear_tablas(conn)
        cargar_datos_iniciales(conn)

        df_productos, df_ventas = cargar_dataframes(conn)
        df_maestro = crear_df_maestro(df_productos, df_ventas)
        print(df_maestro)
        calcular_estadisticas(df_maestro)
        graficar_facturacion(df_maestro)
    
    
        cursor = conn.cursor()
    finally:
        conn.close()


if __name__ == "__main__":
    main()