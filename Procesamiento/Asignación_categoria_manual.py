import pandas as pd

# Cargar tu archivo
df = pd.read_csv("./Datos_extraidos\Datos_procesados/amazon_con_categorias.csv")  # Cambia por tu archivo

# Lista de categorías generales a asignar (puedes ampliar)
categorias = [
    "Aves", "Caballos", "Conejos", "Correas para Mascotas", "Gatos", "Jaulas para Mascotas", 
    "Peces", "Perros", "Reptiles y Anfibios", "Roedores", "Otros"
]

# Agregar una columna vacía para la categoría
if 'category' not in df.columns:
    print("❌ La columna 'category' no existe.")
    exit()

if 'categoria_ml' not in df.columns:
    df["categoria_ml"] = df["category"]  # Copiamos la original como punto de partida

# Filtrar solo los que están en categoría "Otros"
otros_df = df[df['categoria_ml'].str.lower() == 'otros'].copy()

print(f"\n🔍 Se encontraron {len(otros_df)} productos categorizados como 'Otros'.\n")

# Reetiquetar uno por uno
for i in otros_df.index:
    print("\nTítulo:", df.at[i, 'title'])
    print("Precio:", df.at[i, 'price'], "| Rating:", df.at[i, 'rating'])

    for idx, cat in enumerate(categorias):
        print(f"{idx+1}. {cat}")
    
    while True:
        try:
            opcion = int(input("Selecciona la nueva categoría (número): "))
            if 1 <= opcion <= len(categorias):
                df.at[i, "categoria_ml"] = categorias[opcion - 1]
                break
            else:
                print("Número fuera de rango.")
        except ValueError:
            print("Entrada inválida. Ingresa un número.")

# Guardar resultado
df.to_csv("amazon_categorizado.csv", index=False)
print("\n✅ Categorización actualizada y guardada en 'amazon_categorizado.csv'")