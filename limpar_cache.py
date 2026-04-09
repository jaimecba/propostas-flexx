import os
import shutil

def limpar_cache():
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            caminho = os.path.join(root, '__pycache__')
            print(f"Removendo: {caminho}")
            shutil.rmtree(caminho)
    print("✅ Cache limpo com sucesso!")

if __name__ == "__main__":
    limpar_cache()