from app import app

if __name__ == "__main__":
    # Bind to port 3001 as required; host 0.0.0.0 to be reachable from outside container
    app.run(host="0.0.0.0", port=3001)
