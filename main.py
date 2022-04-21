import glob
import os

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTText
from PIL import Image
import base64
from io import BytesIO

page_layout = next(extract_pages("in.pdf"))
page_iter = iter(page_layout)

images = []
order_data = {}


def get_next_element():
    return next(page_iter).get_text()[:-1]


# Data extraction loop
for element in page_iter:
    if isinstance(element, LTFigure):
        img_element = next(iter(element))
        img = Image.open(BytesIO(img_element.stream.rawdata))
        images.append(img)
    if isinstance(element, LTText):
        text = element.get_text()[:-1]
        if text.startswith("Ship to\n"):
            order_data["ship_to"] = text[8:]
        elif text.endswith(".etsy.com"):
            shop_info = text.split("\n")
            order_data["shop_name"] = shop_info[0]
            order_data["shop_url"] = shop_info[1]
        elif text.endswith(" item"):
            order_data["total_quantity"] = text[:-5]
            order_data["items"] = []
            while True:
                item_name = get_next_element().replace("\n", "")
                if item_name == "Item total":
                    # Skips the item total, tax, shipping total, and order total boxes before breaking
                    next(page_iter)
                    next(page_iter)
                    next(page_iter)
                    break
                order_data["items"].append({"name": item_name, "quantity": get_next_element()})
            order_data["item_total"] = get_next_element()
            order_data["tax"] = get_next_element()
            order_data["shipping_total"] = get_next_element()
            order_data["order_total"] = get_next_element()
        elif text.startswith("From\n"):
            order_data["ship_from"] = text[5:]
        elif text.startswith("Order\n"):
            order_data["order_number"] = text[6:]
        elif text.startswith("Order date\n"):
            order_data["order_date"] = text[11:]
        elif text.startswith("Buyer\n"):
            buyer_identity = text.split("\n")
            order_data["buyer_name"] = buyer_identity[1]
            order_data["buyer_id"] = buyer_identity[2]
        elif text.startswith("Payment method\n"):
            order_data["payment_method"] = text[15:]

# html builder
with open("template.html", "w") as f:
    html_out = f.read()

components = {}
for file_path in glob.glob("/components/*.html"):
    with open(file_path, "r") as f:
        components[os.path.basename(file_path)] = f.read()


def template_value(template, key, value):
    return template.replace("{" + key + "}", value)


left_content = ""
right_content
