"""
Service stubs for business logic implementation
Each service corresponds to a specific business domain
"""

# Auth Service (auth_service.py)
# - register_user(nombre, email, password, cedula)
# - verify_email(email, code)
# - login(email, password)
# - refresh_token(refresh_token)
# - logout(user_id)
# - get_user(user_id)

# Category Service (category_service.py)
# - create_category(nombre, subcategorias)
# - get_categories()
# - get_category(categoria_id)
# - update_category(categoria_id, nombre)
# - delete_category(categoria_id)
# - add_subcategory(categoria_id, nombre)

# Product Service (product_service.py)
# - create_product(product_data)
# - list_products(filters)
# - get_product(producto_id)
# - update_product(producto_id, data)
# - delete_product(producto_id)
# - upload_image(producto_id, file)
# - delete_image(imagen_id)

# Inventory Service (inventory_service.py)
# - restock_product(producto_id, cantidad, referencia, usuario_id)
# - get_inventory_history(producto_id)
# - get_stock(producto_id)
# - decrease_stock(producto_id, cantidad) [called when order placed]
# - increase_stock(producto_id, cantidad) [called when order cancelled]

# Carousel Service (carousel_service.py)
# - add_image(orden, link_url, file)
# - list_images()
# - update_image(imagen_id, orden, link_url)
# - delete_image(imagen_id)
# - reorder_images(imagen_id, nueva_orden)

# Order Service (order_service.py)
# - create_order(usuario_id, items, direccion, telefono, nota)
# - list_orders(filters)
# - get_order(pedido_id)
# - update_order_status(pedido_id, estado, nota, usuario_id)
# - get_order_history(pedido_id)
# - get_user_orders(usuario_id)

# User Service (user_service.py)
# - list_users(filters)
# - get_user(usuario_id)
# - get_user_orders(usuario_id)
# - get_user_stats(usuario_id)

# Cart Service (cart_service.py)
# - get_cart(user_id or session_id)
# - add_to_cart(user_id or session_id, producto_id, cantidad)
# - update_item(cart_id, item_id, cantidad)
# - remove_item(cart_id, item_id)
# - clear_cart(cart_id)
# - merge_carts(anonymous_session_id, user_id) [called on login]
# - calculate_total(cart_id)
