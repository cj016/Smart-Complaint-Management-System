from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    if app.config.get("USE_TLS"):
        from app.tls import make_ssl_context
        app.run(debug=True, ssl_context=make_ssl_context())
    else:
        app.run(debug=True)
