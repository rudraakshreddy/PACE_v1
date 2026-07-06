import fitz

def create_watermark_image():
    temp_doc = fitz.open()
    fontsize = 80
    text = "PERMIONICS"
    
    # Calculate exact text width
    text_w = fitz.get_text_length(text, fontname="helv", fontsize=fontsize)
    
    padding = 30
    w = int(text_w + 2 * padding)
    h = int(fontsize * 1.5)
    
    page = temp_doc.new_page(width=w, height=h)
    
    # Draw text with opacity, starting exactly at the padding x-coordinate
    page.insert_text(
        fitz.Point(padding, h * 0.70), 
        text, 
        fontname="helv", 
        fontsize=fontsize, 
        color=(0.6, 0.6, 0.6), 
        fill_opacity=0.15
    )
    
    # Rasterize with alpha and rotate by 45 degrees
    matrix = fitz.Matrix(45)
    pix = page.get_pixmap(alpha=True, matrix=matrix)
    temp_doc.close()
    return pix, pix.width, pix.height

doc = fitz.open()
target_page = doc.new_page()
# Draw some text that the watermark will overlap
for i in range(20):
    target_page.insert_text(fitz.Point(100, 50 + i*20), f"This is some background text {i}.", color=(0, 0, 0))

pix, w, h = create_watermark_image()

rect = target_page.rect
x0 = (rect.width - w) / 2
y0 = (rect.height - h) / 2
image_rect = fitz.Rect(x0, y0, x0 + w, y0 + h)

# Insert the rasterized image
target_page.insert_image(image_rect, pixmap=pix)

doc.save("test_watermark_image.pdf")
doc.close()
print("Success! Created test_watermark_image.pdf")

