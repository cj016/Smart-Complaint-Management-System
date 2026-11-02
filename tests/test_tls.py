import ssl

from app.tls import make_ssl_context


def test_ssl_context_minimum_is_tls12(tmp_path):
    from cryptography import x509  # noqa: F401  (ensures cryptography is installed)
    import subprocess
    import sys
    subprocess.run([sys.executable, "scripts/make_dev_cert.py"], check=True)
    ctx = make_ssl_context()
    assert ctx.minimum_version == ssl.TLSVersion.TLSv1_2