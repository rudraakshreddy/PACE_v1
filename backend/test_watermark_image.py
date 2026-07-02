import fitz

def create_watermark_image():
    temp_doc = fitz.open()
    fontsize = 60
    text = "PERMIONICS"
    
    # Calculate exact text width
    text_w = fitz.get_text_length(text, fontname="helv", fontsize=fontsize)
    
    # Define padding on both sides to prevent cutting off any letters
    padding = 20
    w = int(text_w + 2 * padding)
    h = 100
    
    page = temp_doc.new_page(width=w, height=h)
    
    # Draw text with opacity, starting exactly at the padding x-coordinate
    page.insert_text(
        fitz.Point(padding, 70), 
        text, 
        fontname="helv", 
        fontsize=fontsize, 
        color=(0.8, 0.8, 0.8), 
        fill_opacity=0.3
    )
    
    # Rasterize with alpha
    pix = page.get_pixmap(alpha=True)
    temp_doc.close()
    return pix, w, h

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

