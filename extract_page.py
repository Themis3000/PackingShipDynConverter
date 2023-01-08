import re
from io import BytesIO
from PIL import Image
from pdfminer.layout import LTText, LTFigure


def extract_page_data(page):
    page_list = list(page)
    page_iter = iter(page_list)

    # creates a list of all prices
    prices = []
    discount = {"readable": "0.00", "number": 0}
    price_pattern = re.compile(r"^(- )?[$£]\d*\.\d{2}$")
    for element in page_list:
        if not isinstance(element, LTText):
            continue
        text = element.get_text()
        if not re.match(price_pattern, text):
            continue
        # Handles discounts
        if text.startswith("-"):
            price_readable = f"- {text[2:-1]}"
            price_number = float(f"-{text[3:-1]}")
            discount = {"readable": price_readable, "number": price_number}
            continue
        # Handles all other prices found
        price_readable = text[:-1]
        price_number = float(text[1:-1])
        prices.append({"readable": price_readable, "number": price_number})

    order_data = {}
    prices_iter = iter(prices)

    order_data["item_total"] = next(prices_iter)["readable"]
    order_data["has_discount"] = discount["number"] != 0
    if order_data["has_discount"]:
        order_data["shop_discount"] = discount["readable"]
        order_data["subtotal"] = next(prices_iter)["readable"]
    # Some states don't have tax, skip the tax field if they don't have enough fields to indicate that there's a tax.
    if len(prices) >= (6 if order_data["has_discount"] else 4):
        order_data["tax"] = next(prices_iter)["readable"]
    order_data["shipping_total"] = next(prices_iter)["readable"]
    order_data["order_total"] = next(prices_iter)["readable"]

    images = []

    def get_next_element():
        return next(page_iter).get_text()[:-1]

    # Item extraction
    order_data["items"] = []
    quantity_pattern = re.compile(r"\d* x [$£]\d*\.\d{2}")
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
