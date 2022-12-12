from pdfminer.high_level import extract_pages
from extract_page import extract_page_data
from page_builder import page_builder, template_values, html_out

pages = extract_pages("in.pdf")
html_data = ""

for page in pages:
    order_data, images = extract_page_data(page)
    print(order_data)
    slip_html, label_html = page_builder(order_data, images)
    with open(f"./out/{order_data['buyer_name']}_slip.html", "w", encoding="utf-16") as f:
        f.write(template_values(html_out, {"body": slip_html}))
    with open(f"./out/{order_data['buyer_name']}_label.html", "w", encoding="utf-16") as f:
        f.write(template_values(html_out, {"body": label_html}))

with open("out.html", "w", encoding="utf-16") as f:
    f.write(template_values(html_out, {"body": html_data}))
