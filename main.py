import glob
import os
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTText
from PIL import Image
import base64
from io import BytesIO
from extract_page import extract_page_data

# Print a label (meant for 5x7 envelopes). The label contains a return address and destination address. Only intended
# for hand sorted letter mail.
PRINT_LABEL = True
# The last line on the address is the country name, which is likely not necessary for sending in the mail. You may
# remove the last line if you wish.
LABEL_REMOVE_LAST_LINE = True

page_layout = next(extract_pages("in.pdf"))

order_data, images = extract_page_data(page_layout)

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


def remove_last_line(s):
    return s[:s.rfind('\n')]


left_content = ""
right_content = ""
items_html = ""
bottom_content = ""

left_content += use_component("value", {"title": "Ship to", "value": order_data["ship_to"]})
left_content += use_component("value", {"title": "Scheduled to ship by", "value": order_data["ship_by"]})
left_content += use_component("value", {"title": "Order", "value": order_data["order_number"]})
left_content += use_component("value_with_bold", {"title": "Buyer", "value": order_data["buyer_name"], "bolded_value": order_data["buyer_id"]})

right_content += use_component("value", {"title": "From", "value": order_data["ship_from"]})
right_content += use_component("value", {"title": "Order date", "value": order_data["order_date"]})
right_content += use_component("value", {"title": "Payment method", "value": order_data["payment_method"]})
if order_data.get("has_shipping_info"):
    right_content += use_component("value_with_bold", {"title": "Tracking", "value": order_data["tracking_number"], "bolded_value": order_data["tracking_via"]})

bottom_content += use_component("summaryItem", {"title": "Item total", "value": order_data["item_total"]})
if order_data["has_discount"]:
    bottom_content += use_component("summaryItem", {"title": "Shop discount", "value": order_data["shop_discount"]})
    bottom_content += use_component("summaryItem", {"title": "Subtotal", "value": order_data["subtotal"]})
bottom_content += use_component("summaryItem", {"title": "Tax", "value": order_data["tax"]})
bottom_content += use_component("summaryItem", {"title": "Shipping total", "value": order_data["shipping_total"]})
bottom_content += use_component("summaryItem", {"title": "Order total", "value": order_data["order_total"]})

label = ""
if PRINT_LABEL:
    return_addr = order_data["ship_from"]
    send_addr = order_data["ship_to"]
    if LABEL_REMOVE_LAST_LINE:
        return_addr = remove_last_line(return_addr)
        send_addr = remove_last_line(send_addr)
    label = use_component("label", {"return_addr": return_addr, "send_addr": send_addr})

for item_num, item in enumerate(order_data["items"]):
    img_str = img_to_str(images[item_num+1])
    items_html += use_component("item", {
        "name": item["name"],
        "quantity": item["quantity"],
        "item_message": item["personalization"],
        "img_b64": img_str
    })

html_out = template_values(html_out, {
    "left_content": left_content,
    "right_content": right_content,
    "item_amount_str": f"{len(order_data['items'])} items",
    "items": items_html,
    "bottom_content": bottom_content,
    "logo_b64": img_to_str(images[0]),
    "name": order_data["shop_name"],
    "url": order_data["shop_url"],
    "label": label
})

with open("out.html", "w", encoding="utf-8") as f:
    f.write(html_out)
