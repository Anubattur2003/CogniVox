#!/usr/bin/env python3
"""
HTTPS Development Server for Django
Creates self-signed certificates using Python's built-in SSL and runs Django with HTTPS support
"""

import os
import sys
import subprocess
import ssl
import ipaddress
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime

def create_ssl_certificates():
    """
    Create self-signed SSL certificates for development using Python cryptography library
    """
    ssl_dir = Path(__file__).parent / 'ssl_certs'
    ssl_dir.mkdir(exist_ok=True)
    
    cert_file = ssl_dir / 'cert.pem'
    key_file = ssl_dir / 'key.pem'
    
    # Check if certificates already exist
    if cert_file.exists() and key_file.exists():
        print("SSL certificates already exist.")
        return str(cert_file), str(key_file)
    
    print("Creating self-signed SSL certificate using Python cryptography...")
    
    try:
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv4Address("192.168.0.90")),  # Network IP from terminal
                x509.DNSName("192.168.0.90"),
                x509.IPAddress(ipaddress.IPv4Address("57.159.29.51")),  # Server public IP
                x509.DNSName("57.159.29.51"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print(f"SSL certificate created: {cert_file}")
        print(f"SSL key created: {key_file}")
        return str(cert_file), str(key_file)
        
    except Exception as e:
        print(f"Error creating SSL certificate: {e}")
        print("Please install cryptography library: pip install cryptography")
        return None, None

def run_https_server():
    """
    Run Django development server with HTTPS support
    """
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agentic_django.settings')
    
    cert_file, key_file = create_ssl_certificates()
    
    if not cert_file or not key_file:
        print("Failed to create SSL certificates. Falling back to HTTP.")
        print("Running: python manage.py runserver 0.0.0.0:8000")
        os.system("python manage.py runserver 0.0.0.0:8000")
        return
    
    # Run Django with HTTPS using runserver_plus from django-extensions
    try:
        print("Starting HTTPS development server...")
        print("Server will be available at: https://localhost:8000")
        print("Admin panel: https://localhost:8000/admin/")
        print("Note: You may need to accept the self-signed certificate in your browser")
        
        subprocess.run([
            sys.executable, 'manage.py', 'runserver_plus',
            '--cert-file', cert_file,
            '--key-file', key_file,
            '0.0.0.0:8000'
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running HTTPS server: {e}")
        print("Falling back to HTTP server...")
        print("Running: python manage.py runserver 0.0.0.0:8000")
        os.system("python manage.py runserver 0.0.0.0:8000")
    except FileNotFoundError:
        print("django-extensions not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'django-extensions'])
        print("Please run this script again after installation.")
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    run_https_server()