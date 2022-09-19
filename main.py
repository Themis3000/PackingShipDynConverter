from pdfminer.high_level import extract_pages
from extract_page import extract_page_data
from page_builder import page_builder

page_layout = next(extract_pages("in.pdf"))

order_data, images = extract_page_data(page_layout)
print(order_data)
html_data = page_builder(order_data, images)

with open("out.html", "w", encoding="utf-8") as f:
    f.write(html_data)
