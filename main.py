from pdfminer.high_level import extract_pages
from extract_page import extract_page_data
from page_builder import page_builder, template_values, html_out

page_layout = next(extract_pages("in.pdf"))

order_data, images = extract_page_data(page_layout)
print(order_data)
html_data = page_builder(order_data, images)

with open("out.html", "w", encoding="utf-8") as f:
    f.write(template_values(html_out, {"body": html_data}))
