import requests
import json
import time

def test_mvp_pipeline():
    """
    Test MVP con visualización mejorada de TAXONOMÍA DE PERSONAJES.
    """
    base_url = "https://sylphrena-orchestrator-ece2a4epbdbrfbgk.westus3-01.azurewebsites.net"
    function_key = "D3mx0F0bcrf533OYNdyujs8spwrH6ePpHB1HyxaMth4fAzFuWBPktA==" 
    
    print("=" * 70)
    print("📚 PRUEBA MVP SYLPHRENA - Análisis Completo")
    print("=" * 70)
    
    # 1. Iniciar
    print("\n🚀 1. Iniciando procesamiento...")
    dummy_payload = "EJECUTAR_MODO_HARDCODED"
    try:
        start_response = requests.post(
            f"{base_url}/api/HttpStart",
            headers={"x-functions-key": function_key},
            json=dummy_payload,
            timeout=10
        )
    except Exception as e:
        print(f"❌ ERROR de conexión: {e}")
        return

    if start_response.status_code != 202:
        print(f"❌ ERROR. Código: {start_response.status_code}")
        print(f"Respuesta: {start_response.text}")
        return
    
    status_url = start_response.json()['statusQueryGetUri']
    instance_id = start_response.json()['id']
    print(f"✅ Proceso iniciado. ID: {instance_id}")
    print(f"🔗 Monitoreo: {status_url}\n")
    
    # 2. Monitorear
    print("⏳ 2. Monitoreando progreso...")
    print("-" * 70)
    
    max_attempts = 360  # 60 minutos
    attempt = 0
    last_status = ""
    start_time = time.time()
    
    while attempt < max_attempts:
        time.sleep(10)
        
        try:
            status_response = requests.get(status_url)
            
            if status_response.status_code not in [200, 202]:
                print(f"⚠️ Error consultando estado... reintentando.")
                attempt += 1
                continue

            status_data = status_response.json()
            runtime_status = status_data.get('runtimeStatus', 'Unknown')
            
            elapsed = int(time.time() - start_time)
            status_line = f"[{elapsed}s] Estado: {runtime_status}"
            
            if status_line != last_status or elapsed % 60 == 0:
                print(f"   👉 {status_line}")
                last_status = status_line
            
            if runtime_status == 'Completed':
                print("-" * 70)
                print("✅ 3. PROCESO COMPLETADO")
                print("-" * 70)
                
                output = status_data.get('output', {})
                
                # Guardar resultado completo
                with open('mvp_results.json', 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                
                # VISUALIZACIÓN MEJORADA
                print("\n📊 RESUMEN EJECUTIVO:\n")
                
                try:
                    if isinstance(output, dict):
                        bible = output.get('bible', {})
                        if isinstance(bible, str):
                            try: 
                                bible = json.loads(bible)
                            except: 
                                pass
                        
                        print(f"📘 Capítulos Procesados: {output.get('chapters_processed', 'N/A')}")
                        
                        if isinstance(bible, dict):
                            # REPARTO ORGANIZADO (TAXONOMÍA)
                            reparto = bible.get('reparto_organizado', {})
                            
                            print("\n👥 PERSONAJES DETECTADOS:\n")
                            
                            # PROTAGONISTAS
                            protagonistas = reparto.get('protagonistas', [])
                            if protagonistas:
                                print(f"  🌟 PROTAGONISTAS ({len(protagonistas)}):")
                                for p in protagonistas:
                                    nombre = p.get('nombre', 'N/A')
                                    rol = p.get('rol_clave', 'N/A')
                                    print(f"     {nombre} - {rol}")
                            
                            # ANTAGONISTAS
                            antagonistas = reparto.get('antagonistas', [])
                            if antagonistas:
                                print(f"\n  ⚔️  ANTAGONISTAS ({len(antagonistas)}):")
                                for a in antagonistas:
                                    nombre = a.get('nombre', 'N/A')
                                    amenaza = a.get('amenaza_que_representa', 'N/A')
                                    print(f"     {nombre} - {amenaza}")
                            
                            # SECUNDARIOS
                            secundarios = reparto.get('secundarios', [])
                            if secundarios:
                                print(f"\n  👤 SECUNDARIOS ({len(secundarios)}):")
                                for s in secundarios[:5]:  # Mostrar solo primeros 5
                                    nombre = s.get('nombre', 'N/A')
                                    funcion = s.get('funcion', 'N/A')
                                    print(f"     {nombre} - {funcion}")
                                if len(secundarios) > 5:
                                    print(f"     ... y {len(secundarios) - 5} más")
                            
                            # INCONSISTENCIAS
                            inconsistencias = bible.get('inconsistencias_criticas', [])
                            print(f"\n⚠️  Inconsistencias Detectadas: {len(inconsistencias)}")
                            if inconsistencias:
                                for inc in inconsistencias[:3]:
                                    print(f"   - {inc.get('tipo', 'N/A')}: {inc.get('descripcion', 'N/A')}")
                        
                        print(f"\n💾 Resultado completo: mvp_results.json")
                        
                except Exception as parse_err:
                    print(f"⚠️ Error parseando resumen: {parse_err}")
                    print("Revisa el archivo JSON guardado.")

                return output
                
            elif runtime_status == 'Failed':
                print("\n❌ ERROR: Proceso falló.")
                print(f"Detalles: {status_data.get('output', 'Sin detalles')}")
                return None
                
        except Exception as e:
            print(f"⚠️ Excepción: {e}")
            
        attempt += 1
    
    print("\n⏰ TIMEOUT: El script se detuvo, pero Azure puede seguir trabajando.")
    print(f"Revisa: {status_url}")
    return None

if __name__ == "__main__":
    test_mvp_pipeline()