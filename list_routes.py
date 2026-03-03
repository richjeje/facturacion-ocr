from backend.api.main import app

for route in app.routes:
    # Check if it has methods
    if hasattr(route, "methods"):
        print(f"{route.methods} {route.path}")
    else:
        print(f"WS/Static {route.path}")
