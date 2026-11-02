import ssl


def make_ssl_context(cert="certs/dev-cert.pem", key="certs/dev-key.pem"):
    """TLS 1.2 minimum. TLS 1.0/1.1 and SSL are refused (SCMS-SR-001)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(cert, key)
    return ctx