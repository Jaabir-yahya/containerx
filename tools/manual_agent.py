def collect_retail_input():
    customer = input("Customer name: ")

    items = []
    while True:
        sku = input("SKU (or enter to finish): ")
        if not sku:
            break
        name = input("Item name: ")
        qty = int(input("Quantity: "))
        price = float(input("Unit price: "))
        items.append({
            "sku": sku,
            "name": name,
            "qty": qty,
            "price": price
        })

    payment = float(input("Payment amount: "))

    return customer, items, payment