import asyncio
import os
from dotenv import load_dotenv
from connector import BybitConnector

async def test_connection():
    print("Iniciando prueba de conexión...")
    
    # Cargar variables de entorno
    load_dotenv()
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    try:
        # Inicializar conector
        connector = BybitConnector(api_key, api_secret)
        
        # Probar obtención de datos
        print("Obteniendo datos de mercado...")
        market_data = await connector.get_market_data()
        
        # Verificar datos recibidos
        for pair, data in market_data.items():
            print(f"\nDatos para {pair}:")
            print(f"Filas obtenidas: {len(data)}")
            print(f"Último precio: {data['close'].iloc[-1]}")
            print(f"Último volumen: {data['volume'].iloc[-1]}")
            print("-" * 50)
            
        print("\nPrueba completada exitosamente!")
        
    except Exception as e:
        print(f"\nError durante la prueba: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 