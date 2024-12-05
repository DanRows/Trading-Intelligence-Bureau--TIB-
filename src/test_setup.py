import sys
import pkg_resources

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas correctamente"""
    required = {
        'pybit': '5.5.0',
        'pandas': '2.2.1',
        'numpy': '1.26.4',
        'plotly': '5.19.0',
        'streamlit': '1.31.1',
        'python-dotenv': '1.0.1'
    }
    
    print("Verificando dependencias...")
    
    for package, version in required.items():
        try:
            dist = pkg_resources.get_distribution(package)
            print(f"{package}=={dist.version} ✓")
        except pkg_resources.DistributionNotFound:
            print(f"{package} no está instalado ✗")
            
    print("\nVersión de Python:", sys.version)

if __name__ == "__main__":
    check_dependencies() 