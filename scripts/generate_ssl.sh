#!/bin/bash
# Twitter Bot v2.0 - SSL Certificate Generation Script
# Generates self-signed SSL certificates for HTTPS

set -e

SSL_DIR="${1:-ssl}"
DAYS_VALID="${2:-365}"
KEY_SIZE="${3:-4096}"

echo "=== Twitter Bot SSL Certificate Generator ==="
echo "Output directory: $SSL_DIR"
echo "Certificate validity: $DAYS_VALID days"
echo "Key size: $KEY_SIZE bits"
echo ""

# Create SSL directory
mkdir -p "$SSL_DIR"

# Generate private key and certificate
echo "Generating self-signed certificate..."
openssl req -x509 -newkey "rsa:$KEY_SIZE" \
    -keyout "$SSL_DIR/key.pem" \
    -out "$SSL_DIR/cert.pem" \
    -days "$DAYS_VALID" \
    -nodes \
    -subj "/CN=twitterbot/O=Private/C=XX" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:10.8.0.1"

# Set permissions
chmod 600 "$SSL_DIR/key.pem"
chmod 644 "$SSL_DIR/cert.pem"

echo ""
echo "=== SSL Certificates Generated ==="
echo "Private key: $SSL_DIR/key.pem"
echo "Certificate: $SSL_DIR/cert.pem"
echo ""
echo "To use with the backend, set these environment variables:"
echo "  SSL_CERTFILE=$SSL_DIR/cert.pem"
echo "  SSL_KEYFILE=$SSL_DIR/key.pem"
echo ""
echo "Or run uvicorn with:"
echo "  uvicorn main:app --ssl-keyfile $SSL_DIR/key.pem --ssl-certfile $SSL_DIR/cert.pem"
