import glob
import os
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTText
from PIL import Image
import base64
from io import BytesIO

# Print a label (meant for 5x7 envelopes). The label contains a return address and destination address. Only intended
# for hand sorted letter mail.
PRINT_LABEL = True
# The last line on the address is the country name, which is likely not necessary for sending in the mail. You may
# remove the last line if you wish.
LABEL_REMOVE_LAST_LINE = True

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
            has_discount = get_next_element() == "Shop discount"
            next(page_iter)
            order_data["has_discount"] = False
            # Additionally, skip two more if there's a discount
            if has_discount:
                order_data["has_discount"] = True
                next(page_iter)
                next(page_iter)
            next(page_iter)
            order_data["item_total"] = get_next_element()
            if has_discount:
                order_data["shop_discount"] = get_next_element()
                order_data["subtotal"] = get_next_element()
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
        elif text.startswith("Tracking\n"):
            tracking_data = text.split("\n")
            order_data["has_shipping_info"] = True
            order_data["tracking_number"] = tracking_data[1]
            order_data["tracking_via"] = tracking_data[2]

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
    items_html += use_component("item", {"name": item["name"], "quantity": item["quantity"], "img_b64": img_str})

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
