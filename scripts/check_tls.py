import socket
import ssl

HOST, PORT = "127.0.0.1", 5000


def try_version(version):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_ciphers("ALL:@SECLEVEL=0")
    try:
        ctx.minimum_version = ctx.maximum_version = version
    except ValueError:
        return "not supported by this Python/OpenSSL (cannot be tested)"
    try:
        with socket.create_connection((HOST, PORT), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=HOST) as s:
                return f"ACCEPTED ({s.version()})"
    except (ssl.SSLError, OSError) as exc:
        return f"REFUSED ({exc.__class__.__name__})"


for v in (ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1_1,
          ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3):
    print(f"{v.name:8} -> {try_version(v)}")