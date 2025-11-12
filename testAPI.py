import stripe

stripe.api_key = "sk_test_51SRCVt0RNCB3m8QSaIRumhWoMmjlrilyhdXjaG0p7E8yLpEyjp6pR8e6HNpG0V72OJA9Ki2I6JklwiFF0BgIuss900WNlkVK7o"

# Fetch all products (Stripe returns up to 100 per page)
products = stripe.Product.list(limit=100)

print("=== PRODUCTS FOUND ===")
for product in products.data:
    print(product)
