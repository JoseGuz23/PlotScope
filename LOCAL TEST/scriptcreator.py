import os
from PIL import Image, ImageDraw, ImageFont

def create_favicon(size, filename):
    # Colores
    bg_color = "#F5F1E8"
    primary_color = "#0A5850"
    
    # Crear lienzo
    img = Image.new('RGB', (size, size), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Cálculos proporcionales
    center = size / 2
    outer_radius = size * 0.38
    outer_width = max(1, int(size * 0.06))
    inner_radius = size * 0.32
    inner_width = max(1, int(size * 0.02))
    
    # Dibujar anillos
    # Anillo exterior
    draw.ellipse([center - outer_radius, center - outer_radius, 
                  center + outer_radius, center + outer_radius], 
                 outline=primary_color, width=outer_width)
    
    # Anillo interior
    draw.ellipse([center - inner_radius, center - inner_radius, 
                  center + inner_radius, center + inner_radius], 
                 outline=primary_color, width=inner_width)
    
    # Fuente
    # Intenta usar Georgia, sino usa defecto
    try:
        font_size = int(size * 0.5)
        # Ajusta la ruta de la fuente según tu OS si es necesario
        font = ImageFont.truetype("georgia.ttf", font_size)
    except IOError:
        try:
             # Fallback para Windows
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

    # Dibujar Letra L
    text = "L"
    # Obtener dimensiones del texto para centrar (bbox)
    left, top, right, bottom = font.getbbox(text)
    text_width = right - left
    text_height = bottom - top
    
    draw.text((center - text_width/2, center - text_height/1.5), text, fill=primary_color, font=font)

    # Estrellas (Simplificadas como puntos si es muy pequeño)
    if size > 32:
        star_font_size = int(size * 0.1)
        try:
            star_font = ImageFont.truetype("seguiemj.ttf", star_font_size) # Windows emoji font
        except:
            star_font = font
            
        draw.text((center - outer_radius * 1.2, center - star_font_size/2), "*", fill=primary_color, font=star_font)
        draw.text((center + outer_radius * 0.9, center - star_font_size/2), "*", fill=primary_color, font=star_font)

    # Guardar
    img.save(filename)
    print(f"Generado: {filename}")

# Generar todos los tamaños necesarios
sizes = {
    16: "favicon-16.png",
    32: "favicon-32.png",
    180: "apple-touch-icon.png",
    192: "favicon-192.png",
    512: "favicon-512.png"
}

if __name__ == "__main__":
    print("Generando favicons...")
    for size, name in sizes.items():
        create_favicon(size, name)
    print("Proceso finalizado.")