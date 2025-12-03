#!/usr/bin/env python3
"""
Test local para el generador DOCX de Sylphrena 4.0

Uso:
    python test_docx_generator.py
    
Resultado:
    Genera test_output.docx en el directorio actual
"""

import sys
import os
from datetime import datetime

# Simular imports de Azure (para testing local)
class MockDocument:
    pass

# Importar generador
try:
    from API_DURABLE.SaveOutputs.docx_generator import generate_manuscript_docx
    print("✅ Módulo docx_generator importado correctamente")
except ImportError as e:
    print(f"❌ Error importando docx_generator: {e}")
    print("\nAsegúrate de que docx_generator.py está en el mismo directorio")
    sys.exit(1)

# Datos de prueba que simulan la salida de ReconstructManuscript
test_chapters = [
    {
        'chapter_id': 0,
        'display_title': 'PRÓLOGO',
        'contenido_original': '''Juan Moreno afinó su guitarra bajo la sombra del laurel que dominaba la plaza de San Guzmán. Era sábado por la noche, y el pueblo había cobrado vida después de una semana de trabajo bajo el sol de finales de agosto del 43.

La fiesta seguía con emoción. La gente, poco a poco, se soltaba más, por obra de la música y el alcohol. Los gritos de felicidad, las risas y el zapateo incesante de la gente inundaban San Guzmán con alegría.

La celebración se vio interrumpida cuando, entre murmullos, la gente se abrió paso para dejar pasar a la bella y joven Fernanda. Hija de Juan Herrera, quien llegó gritando por auxilio.''',
        'contenido_editado': '''Juan Moreno afinó su guitarra bajo la sombra del laurel que dominaba la plaza de San Guzmán. Era sábado por la noche, y el pueblo había cobrado vida después de una semana de trabajo bajo el sol de finales de agosto del 43.

La gente, poco a poco, se soltaba más, por obra de la música y el alcohol. Los gritos de felicidad, las risas y el zapateo incesante inundaban San Guzmán con alegría.

La celebración se vio interrumpida cuando, entre murmullos, la gente se abrió paso para dejar pasar a Fernanda. La joven llegó gritando por auxilio.''',
        'cambios_realizados': [
            {
                'tipo': 'redundancia',
                'original': 'La fiesta seguía con emoción. La gente, poco a poco, se soltaba más, por obra de la música y el alcohol. Los gritos de felicidad, las risas y el zapateo incesante de la gente inundaban',
                'editado': 'La gente, poco a poco, se soltaba más, por obra de la música y el alcohol. Los gritos de felicidad, las risas y el zapateo incesante inundaban',
                'justificacion': "Eliminé 'La fiesta seguía con emoción' porque es redundante con la descripción inmediata de gritos, risas y zapateo que ya muestra la emoción. También eliminé 'de la gente' en la segunda mención para evitar repetición.",
                'impacto_narrativo': 'Mejora el flujo'
            },
            {
                'tipo': 'show_tell',
                'original': 'la bella y joven Fernanda. Hija de Juan Herrera, quien llegó gritando por auxilio',
                'editado': 'Fernanda. La joven llegó gritando por auxilio',
                'justificacion': "Eliminé 'bella y joven' (tell innecesario) y 'Hija de Juan Herrera' que interrumpe el flujo de la acción urgente. La información de parentesco no es relevante en este momento de tensión.",
                'impacto_narrativo': 'Mejora el ritmo'
            },
            {
                'tipo': 'redundancia',
                'original': 'Juan no dudó un segundo y se puso en pie con firmeza',
                'editado': 'Juan se puso en pie con firmeza',
                'justificacion': "Eliminé 'no dudó un segundo' porque 'se puso en pie con firmeza' ya muestra la inmediatez y determinación de su acción.",
                'impacto_narrativo': 'Fortalece la acción'
            }
        ],
        'elementos_preservados': [
            'Ritmo costumbrista intencional al inicio',
            'Descripción atmosférica de la plaza',
            'Voz del narrador en tercera persona'
        ],
        'notas_editor': 'El prólogo tiene una estructura sólida y cumple efectivamente con su función de establecer el tono costumbrista antes de la irrupción violenta. Los cambios se enfocaron en eliminar redundancias y algunos momentos de tell innecesario que ralentizaban la acción.',
        'word_count': 2947,
        'metadata': {
            'costo_total_usd': 0.1371
        }
    },
    {
        'chapter_id': 1,
        'display_title': 'Capítulo 1: Las tres fuerzas',
        'contenido_original': '''Ángel Moreno había subido a la torre de la iglesia con su libro, como cada sábado. Desde ahí podía escuchar la guitarra de Juan sin tener que bajar a saludar a la gente del pueblo.

Estaba perdido entre las páginas cuando el bullicio y la emoción se desvanecieron de golpe. La gente había dejado de bailar y su hermano había dejado de tocar.''',
        'contenido_editado': '''Ángel Moreno había subido a la torre de la iglesia con su libro, como cada sábado. Desde ahí podía escuchar la guitarra de Juan sin tener que bajar a saludar a la gente del pueblo.

Estaba perdido entre las páginas cuando el bullicio se desvaneció de golpe. La gente había dejado de bailar y su hermano había dejado de tocar.''',
        'cambios_realizados': [
            {
                'tipo': 'redundancia',
                'original': 'el bullicio y la emoción se desvanecieron de golpe',
                'editado': 'el bullicio se desvaneció de golpe',
                'justificacion': 'La emoción está implícita en el bullicio; eliminar redundancia mantiene el ritmo',
                'impacto_narrativo': 'Fortalece el momento'
            }
        ],
        'elementos_preservados': [],
        'notas_editor': 'Capítulo sólido con buen equilibrio entre acción y reflexión. Se eliminaron redundancias menores para mantener el ritmo.',
        'word_count': 1845,
        'metadata': {
            'costo_total_usd': 0.0892
        }
    }
]

def main():
    print("\n" + "="*60)
    print("🧪 TEST GENERADOR DOCX - SYLPHRENA 4.0")
    print("="*60 + "\n")
    
    # Test 1: Verificar python-docx
    print("1️⃣ Verificando dependencias...")
    try:
        import docx
        print("   ✅ python-docx instalado")
    except ImportError:
        print("   ❌ python-docx NO instalado")
        print("   Instalar con: pip install python-docx --break-system-packages")
        sys.exit(1)
    
    # Test 2: Generar DOCX
    print("\n2️⃣ Generando documento DOCX...")
    try:
        docx_buffer = generate_manuscript_docx(
            test_chapters,
            'PIEL MORENA',
            style='simple'
        )
        print("   ✅ Documento generado en memoria")
    except Exception as e:
        print(f"   ❌ Error generando documento: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Test 3: Guardar archivo
    print("\n3️⃣ Guardando archivo...")
    output_file = 'test_output.docx'
    try:
        with open(output_file, 'wb') as f:
            f.write(docx_buffer.read())
        
        file_size = os.path.getsize(output_file)
        print(f"   ✅ Archivo guardado: {output_file}")
        print(f"   📊 Tamaño: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    except Exception as e:
        print(f"   ❌ Error guardando archivo: {e}")
        sys.exit(1)
    
    # Resumen
    print("\n" + "="*60)
    print("✅ TEST COMPLETADO EXITOSAMENTE")
    print("="*60)
    print(f"\n📄 Archivo generado: {output_file}")
    print("\n📋 Contenido del documento:")
    print("   • Portada con instrucciones")
    print("   • 2 capítulos de prueba")
    print(f"   • {len(test_chapters[0]['cambios_realizados'])} cambios en Prólogo")
    print(f"   • {len(test_chapters[1]['cambios_realizados'])} cambio en Capítulo 1")
    print("\n💡 Abre el archivo con:")
    print("   • Microsoft Word")
    print("   • Google Docs")
    print("   • LibreOffice Writer")
    print("\n🎯 Si se ve bien, ¡ya puedes integrarlo en SaveOutputs!")
    print()

if __name__ == '__main__':
    main()