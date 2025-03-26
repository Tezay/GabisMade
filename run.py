from app import create_app

# Crée l'application Flask
app = create_app()

if __name__ == '__main__':
    # Lance l'application
    app.run(debug=True)
