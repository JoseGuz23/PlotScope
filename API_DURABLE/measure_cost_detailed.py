# measure_costs_detailed.py
"""
Script de análisis detallado de costos para Sylphrena MVP
"""

def calculate_detailed_costs(book_words=50000, chapters=30):
    """
    Calcula costos detallados por fase del proceso
    """
    print("=== CALCULADORA DE COSTOS SYLPHRENA ===\n")
    print(f"Libro de {book_words:,} palabras en {chapters} capítulos\n")
    
    # Factor de conversión palabras a tokens
    WORD_TO_TOKEN = 1.33
    total_tokens = book_words * WORD_TO_TOKEN
    tokens_per_chapter = total_tokens / chapters
    
    costs = {}
    
    # 1. SEGMENTACIÓN (Gemini Flash)
    costs['segmentation'] = {
        'model': 'Gemini 1.5 Flash',
        'input_tokens': total_tokens,
        'output_tokens': 500,  # JSON con índice de capítulos
        'price_per_million_in': 0.10,
        'price_per_million_out': 0.10,
        'cost': (total_tokens * 0.10 / 1_000_000) + (500 * 0.10 / 1_000_000)
    }
    
    # 2. ANÁLISIS PARALELO (Gemini Flash con Batch API)
    costs['analysis'] = {
        'model': 'Gemini 1.5 Flash (Batch)',
        'input_tokens': total_tokens,
        'output_tokens': chapters * 300,  # ~300 tokens de análisis por capítulo
        'price_per_million_in': 0.05,  # 50% descuento con Batch API
        'price_per_million_out': 0.05,
        'cost': (total_tokens * 0.05 / 1_000_000) + (chapters * 300 * 0.05 / 1_000_000)
    }
    
    # 3. CREACIÓN DE BIBLIA (Gemini Pro)
    bible_input = chapters * 300  # Todos los análisis JSON
    bible_output = 5000  # Biblia detallada
    costs['bible'] = {
        'model': 'Gemini 1.5 Pro',
        'input_tokens': bible_input,
        'output_tokens': bible_output,
        'price_per_million_in': 3.50,
        'price_per_million_out': 10.50,
        'cost': (bible_input * 3.50 / 1_000_000) + (bible_output * 10.50 / 1_000_000)
    }
    
    # 4. EDICIÓN CON CLAUDE (Sonnet 3.5)
    # Cada capítulo recibe: texto + biblia relevante
    claude_input_per_chapter = tokens_per_chapter + 2000  # Capítulo + contexto de biblia
    claude_output_per_chapter = tokens_per_chapter * 1.1  # Capítulo editado (10% más largo)
    
    costs['editing'] = {
        'model': 'Claude 3.5 Sonnet',
        'input_tokens': claude_input_per_chapter * chapters,
        'output_tokens': claude_output_per_chapter * chapters,
        'price_per_million_in': 3.00,
        'price_per_million_out': 15.00,
        'cost': (claude_input_per_chapter * chapters * 3.00 / 1_000_000) + 
                (claude_output_per_chapter * chapters * 15.00 / 1_000_000)
    }
    
    # 5. INFRAESTRUCTURA AZURE
    costs['infrastructure'] = {
        'model': 'Azure Serverless',
        'functions_executions': chapters * 4,  # 4 funciones por capítulo
        'storage_gb': 0.01,  # ~10MB por libro
        'cosmos_db_rus': 100,  # Request Units mínimas
        'cost': 0.15  # Estimado fijo para MVP
    }
    
    # CALCULAR TOTAL
    total_cost = sum(phase['cost'] for phase in costs.values())
    
    # IMPRIMIR DESGLOSE
    print("DESGLOSE DE COSTOS POR FASE:")
    print("-" * 60)
    
    for phase_name, details in costs.items():
        print(f"\n{phase_name.upper()}:")
        print(f"  Modelo: {details['model']}")
        if 'input_tokens' in details:
            print(f"  Tokens entrada: {details['input_tokens']:,.0f}")
            print(f"  Tokens salida: {details.get('output_tokens', 0):,.0f}")
        print(f"  💰 Costo: ${details['cost']:.4f}")
    
    print("\n" + "=" * 60)
    print(f"COSTO TOTAL POR LIBRO: ${total_cost:.2f}")
    print(f"Margen (vendiendo a $49): {((49 - total_cost) / 49 * 100):.1f}%")
    print(f"Ganancia por libro: ${49 - total_cost:.2f}")
    
    # ANÁLISIS DE ESCENARIOS
    print("\n" + "=" * 60)
    print("ANÁLISIS DE ESCENARIOS:")
    print("-" * 60)
    
    scenarios = [
        ("Novela corta", 30000, 15),
        ("Novela estándar", 80000, 40),
        ("Novela larga", 120000, 60),
        ("Épica", 200000, 100)
    ]
    
    for name, words, chaps in scenarios:
        scenario_cost = calculate_scenario_cost(words, chaps)
        print(f"\n{name} ({words:,} palabras, {chaps} capítulos):")
        print(f"  Costo: ${scenario_cost:.2f}")
        print(f"  Precio sugerido: ${scenario_cost * 15:.0f}")
        print(f"  Ganancia (a $49): ${max(0, 49 - scenario_cost):.2f}")
    
    return total_cost

def calculate_scenario_cost(words, chapters):
    """Calcula costo para un escenario específico"""
    tokens = words * 1.33
    
    # Simplificado para cálculo rápido
    cost = 0
    cost += tokens * 0.10 / 1_000_000  # Segmentación
    cost += tokens * 0.05 / 1_000_000  # Análisis
    cost += chapters * 300 * 3.50 / 1_000_000  # Biblia input
    cost += 5000 * 10.50 / 1_000_000  # Biblia output
    cost += (tokens + chapters * 2000) * 3.00 / 1_000_000  # Claude input
    cost += tokens * 1.1 * 15.00 / 1_000_000  # Claude output
    cost += 0.15  # Infraestructura
    
    return cost

if __name__ == "__main__":
    # Calcular para libro estándar
    total = calculate_detailed_costs(50000, 25)
    
    print("\n" + "=" * 60)
    print("RECOMENDACIONES DE OPTIMIZACIÓN:")
    print("-" * 60)
    print("1. Usar Batch API de Gemini reduce costos 50%")
    print("2. Limitar re-inyección de Biblia (usar solo partes relevantes)")
    print("3. Implementar caché para libros re-procesados")
    print("4. Considerar Gemini Flash para edición simple vs Claude")