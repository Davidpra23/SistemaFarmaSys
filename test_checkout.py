from app import app, INVENTORY, RECEIPTS
with app.test_client() as c:
    # Simular sesión autenticada
    with c.session_transaction() as sess:
        sess['user'] = {'username': 'admin'}

    # Elegir un producto válido del inventario
    if not INVENTORY:
        print('No hay productos en INVENTORY')
    else:
        p = INVENTORY[0]
        items = [{'id': p['id'], 'name': p['name'], 'price': p['price'], 'qty': 1}]

        # Crear primera venta
        rv1 = c.post('/api/checkout', json={'items': items})
        print('Checkout1 Status:', rv1.status_code)
        print('Checkout1 Response:', rv1.get_data(as_text=True))

        # Crear segunda venta
        rv2 = c.post('/api/checkout', json={'items': items})
        print('Checkout2 Status:', rv2.status_code)
        print('Checkout2 Response:', rv2.get_data(as_text=True))

        print('Receipts count:', len(RECEIPTS))
        # List receipts page
        rlist = c.get('/receipts')
        print('/receipts status:', rlist.status_code)
        html = rlist.get_data(as_text=True)
        print('/receipts snippet:')
        print(html[:800])

        if RECEIPTS:
            rid = RECEIPTS[0]['id']
            print('Last receipt id:', rid)
            # Now request the receipt page for last receipt
            r2 = c.get(f'/receipt/{rid}')
            print('/receipt status:', r2.status_code)
            data = r2.get_data(as_text=True)
            print('/receipt snippet:')
            print(data[:1000])
