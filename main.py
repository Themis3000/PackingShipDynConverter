import glob
import os
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTText
from PIL import Image
import base64
from io import BytesIO

page_layout = next(extract_pages("in.pdf"))
page_list = list(page_layout)
page_iter = iter(page_list)

images = []
order_data = {}


def get_next_element():
    return next(page_iter).get_text()[:-1]


# Item extraction
order_data["items"] = []
quantity_pattern = re.compile(r"\d* x \$\d*\.\d{2}")
for index, element in enumerate(page_list):
    if isinstance(element, LTText):
        text = element.get_text()[:-1]
        if quantity_pattern.match(text):
            quantity = text
            name = page_list[index-1].get_text()[:-1]
            order_data["items"].append({"name": name, "quantity": quantity})

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
        elif text == "Item total":
            # Skips the item total, tax, shipping total, and order total
            next(page_iter)
            next(page_iter)
            next(page_iter)
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
        elif text.startswith("Scheduled to ship by\n"):
            order_data["ship_by"] = text[21:]

print(order_data)

# html builder
with open("template.html", "r") as f:
    html_out = f.read().replace("\n", "")

components = {}
for file_path in glob.glob("./components/*.html"):
    with open(file_path, "r") as f:
        components[os.path.basename(file_path)] = f.read().replace("\n", "")


def template_values(template, values):
    for key, value in values.items():
        html_value = value.replace("\n", "<br>")
        template = template.replace("{" + key + "}", html_value)
    return template


def use_component(component, values):
    template = components[f"{component}.html"]
    return template_values(template, values)


def img_to_str(img):
    img_buffer = BytesIO()
    img.save(img_buffer, format="JPEG")
    img_str = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
    return img_str


left_content = ""
right_content = ""
items_html = ""

left_content += use_component("value", {"title": "Ship to", "value": order_data["ship_to"]})
left_content += use_component("value", {"title": "Scheduled to ship by", "value": order_data["ship_by"]})
left_content += use_component("value", {"title": "Order", "value": order_data["order_number"]})
left_content += use_component("value_with_bold", {"title": "Buyer", "value": order_data["buyer_name"], "bolded_value": order_data["buyer_id"]})
# add shipping method here

right_content += use_component("value", {"title": "From", "value": order_data["ship_from"]})
right_content += use_component("value", {"title": "Order date", "value": order_data["order_date"]})
right_content += use_component("value", {"title": "Payment method", "value": order_data["payment_method"]})
# add tracking here

for item_num, item in enumerate(order_data["items"]):
    img_str = img_to_str(images[item_num+1])
    items_html += use_component("item", {"name": item["name"], "quantity": item["quantity"], "img_b64": img_str})

html_out = template_values(html_out, {
    "left_content": left_content,
    "right_content": right_content,
    "item_amount_str": f"{len(order_data['items'])} items",
    "items": items_html,
    "item_total": order_data["item_total"],
    "tax": order_data["tax"],
    "shipping_total": order_data["shipping_total"],
    "order_total": order_data["order_total"],
    "logo_b64": img_to_str(images[0]),
    "name": order_data["shop_name"],
    "url": order_data["shop_url"]
})

with open("out.html", "w") as f:
    f.write(html_out)
