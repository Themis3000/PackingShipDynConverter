import re
from io import BytesIO
from PIL import Image
from pdfminer.layout import LTText, LTFigure


def extract_page_data(page):
    page_list = list(page)
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
                name = page_list[index - 1].get_text()[:-1].replace("\n", " ")
                personalization = page_list[index + 1].get_text().replace("\n", " ")
                if not personalization.startswith("Personalization: "):
                    personalization = ""
                order_data["items"].append({"name": name, "quantity": quantity, "personalization": personalization})

    # Data extraction loop
    for element in page_iter:
        if isinstance(element, LTFigure):
            img_element = next(iter(element))
            img = Image.open(BytesIO(img_element.stream.rawdata))
            images.append(img)
        if isinstance(element, LTText):
            text = element.get_text()[:-1]
            if text.startswith("Deliver to\n"):
                order_data["ship_to"] = text[11:]
            elif text.startswith("Ship to\n"):
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
                order_data["buyer_id"] = buyer_identity[2] if len(buyer_identity) >= 3 else ""
            elif text.startswith("Payment method\n"):
                order_data["payment_method"] = text[15:]
            elif text.startswith("Scheduled to dispatch by\n"):
                order_data["ship_by"] = text[25:]
            elif text.startswith("Scheduled to ship by\n"):
                order_data["ship_by"] = text[21:]
            elif text.startswith("Tracking\n"):
                tracking_data = text.split("\n")
                order_data["has_shipping_info"] = True
                order_data["tracking_number"] = tracking_data[1]
                order_data["tracking_via"] = tracking_data[2]

    return order_data, images
