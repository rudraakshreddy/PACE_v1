import fitz

doc = fitz.open()
page = doc.new_page()
page.insert_text(fitz.Point(100, 100), "Hello World", color=(0, 0, 0))

try:
    page.insert_text(fitz.Point(100, 200), "Watermark", fontsize=50, color=(1, 0, 0), fill_opacity=0.3)
    print("Opacity supported in insert_text!")
except Exception as e:
    print(f"Opacity failed: {e}")
    try:
        page.insert_text(fitz.Point(100, 200), "Watermark", fontsize=50, color=(0.8, 0.8, 0.8))
        print("Fallback to light grey worked!")
    except Exception as e2:
        print(f"Fallback failed: {e2}")

doc.save("test_watermark.pdf")
doc.close()
