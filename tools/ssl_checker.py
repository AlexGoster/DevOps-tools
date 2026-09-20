"""SSL certificate checker.

Validates SSL certificates, checks expiry dates,
verifies certificate chains, and provides renewal recommendations.
"""

import socket
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class SSLResult:
    """SSL certificate check result."""

    hostname: str
    port: int = 443
    valid: bool = False
    issuer: str = ""
    subject: str = ""
    serial_number: str = ""
    not_before: Optional[datetime] = None
    not_after: Optional[datetime] = None
    days_until_expiry: Optional[int] = None
    is_expired: bool = False
    is_self_signed: bool = False
    subject_alternative_names: list[str] = field(default_factory=list)
    protocol_version: str = ""
    cipher: str = ""
    chain_length: int = 0
    chain_valid: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "hostname": self.hostname,
            "port": self.port,
            "valid": self.valid,
            "issuer": self.issuer,
            "subject": self.subject,
            "serial_number": self.serial_number,
            "not_before": self.not_before.isoformat() if self.not_before else None,
            "not_after": self.not_after.isoformat() if self.not_after else None,
            "days_until_expiry": self.days_until_expiry,
            "is_expired": self.is_expired,
            "is_self_signed": self.is_self_signed,
            "subject_alternative_names": self.subject_alternative_names,
            "protocol_version": self.protocol_version,
            "cipher": self.cipher,
            "chain_length": self.chain_length,
            "chain_valid": self.chain_valid,
            "warnings": self.warnings,
            "errors": self.errors,
        }


class SSLChecker:
    """Checks SSL certificate status and validity."""

    WARNING_DAYS = [30, 14, 7]

    def __init__(self, timeout: int = 10):
        """Initialize SSL checker.

        Args:
            timeout: Connection timeout in seconds.
        """
        self.timeout = timeout

    def _format_name(self, name_tuple: tuple) -> str:
        """Format X509 name tuple to string."""
        parts = []
        for rdn in name_tuple:
            for attr_type, attr_value in rdn:
                parts.append(f"{attr_type}={attr_value}")
        return ", ".join(parts)

    def _extract_sans(self, cert: dict) -> list[str]:
        """Extract Subject Alternative Names from certificate."""
        sans = []
        for ext in cert.get("subjectAltName", ()):
            if ext[0] == "DNS":
                sans.append(ext[1])
        return sans

    def check(
        self,
        hostname: str,
        port: int = 443,
        verify: bool = True,
    ) -> SSLResult:
        """Check SSL certificate for a host.

        Args:
            hostname: Hostname to check.
            port: Port to connect to (default 443).
            verify: Whether to verify the certificate chain.

        Returns:
            SSLResult with check results.
        """
        result = SSLResult(hostname=hostname, port=port)

        try:
            context = ssl.create_default_context()
            if not verify:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher_info = ssock.cipher()
                    protocol = ssock.version()

                    # Certificate details
                    result.valid = True
                    result.issuer = self._format_name(cert.get("issuer", ()))
                    result.subject = self._format_name(cert.get("subject", ()))
                    result.serial_number = cert.get("serialNumber", "")
                    result.subject_alternative_names = self._extract_sans(cert)
                    result.protocol_version = protocol
                    result.cipher = cipher_info[0] if cipher_info else ""

                    # Parse dates
                    not_before = cert.get("notBefore", "")
                    not_after = cert.get("notAfter", "")

                    if not_before:
                        result.not_before = datetime.strptime(not_before, "%b %d %H:%M:%S %Y %Z")
                    if not_after:
                        result.not_after = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        result.days_until_expiry = (result.not_after - datetime.utcnow()).days
                        result.is_expired = result.days_until_expiry < 0

                    # Check if self-signed
                    result.is_self_signed = result.issuer == result.subject

                    # Validate chain
                    result.chain_valid = self._validate_chain(hostname, port)

        except ssl.SSLCertVerificationError as exc:
            result.errors.append(f"Certificate verification failed: {exc}")
            # Still try to get cert info without verification
            return self._check_unverified(hostname, port)
        except socket.timeout:
            result.errors.append(f"Connection timed out after {self.timeout}s")
        except socket.gaierror as exc:
            result.errors.append(f"DNS resolution failed: {exc}")
        except ConnectionRefusedError:
            result.errors.append(f"Connection refused on port {port}")
        except Exception as exc:
            result.errors.append(f"Check failed: {exc}")

        # Generate warnings
        self._check_warnings(result)

        return result

    def _check_unverified(self, hostname: str, port: int) -> SSLResult:
        """Check certificate without verification (for gathering info)."""
        result = SSLResult(hostname=hostname, port=port)

        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # DER-encoded certificate
                    der_cert = ssock.getpeercert(binary_form=True)
                    if der_cert:
                        result.valid = True
                        result.chain_valid = False

        except Exception as exc:
            result.errors.append(f"Info gathering failed: {exc}")

        return result

    def _validate_chain(self, hostname: str, port: int) -> bool:
        """Validate the certificate chain."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # If we get here without error, chain is valid
                    return True
        except Exception:
            return False

    def _check_warnings(self, result: SSLResult) -> None:
        """Generate warnings based on certificate state."""
        if result.is_expired:
            result.warnings.append(f"Certificate expired {abs(result.days_until_expiry)} days ago")
        elif result.days_until_expiry is not None:
            for days in self.WARNING_DAYS:
                if result.days_until_expiry <= days:
                    result.warnings.append(f"Certificate expires in {result.days_until_expiry} days")
                    break

        if result.is_self_signed:
            result.warnings.append("Certificate is self-signed")

        if not result.chain_valid:
            result.warnings.append("Certificate chain validation failed")

        # Check weak protocol
        if result.protocol_version in ("TLSv1", "TLSv1.1", "SSLv3"):
            result.warnings.append(f"Weak protocol: {result.protocol_version}")

    def check_multiple(
        self,
        hosts: list[tuple[str, int]],
        verify: bool = True,
    ) -> list[SSLResult]:
        """Check SSL certificates for multiple hosts.

        Args:
            hosts: List of (hostname, port) tuples.
            verify: Whether to verify certificates.

        Returns:
            List of SSLResult objects.
        """
        results = []
        for hostname, port in hosts:
            results.append(self.check(hostname, port, verify))
        return results

    def get_expiry_report(
        self,
        hosts: list[tuple[str, int]],
        warning_days: int = 30,
    ) -> dict:
        """Generate expiry report for multiple hosts.

        Args:
            hosts: List of (hostname, port) tuples.
            warning_days: Days threshold for warnings.

        Returns:
            Report dict with expiry information.
        """
        results = self.check_multiple(hosts)
        expiring_soon = []
        expired = []
        valid = []

        for r in results:
            if r.is_expired:
                expired.append(r)
            elif r.days_until_expiry is not None and r.days_until_expiry <= warning_days:
                expiring_soon.append(r)
            else:
                valid.append(r)

        return {
            "total_checked": len(results),
            "valid": len(valid),
            "expiring_soon": len(expiring_soon),
            "expired": len(expired),
            "details": [r.to_dict() for r in results],
            "expiring_hosts": [
                {"hostname": r.hostname, "days_left": r.days_until_expiry}
                for r in expiring_soon
            ],
            "expired_hosts": [
                {"hostname": r.hostname, "days_expired": abs(r.days_until_expiry or 0)}
                for r in expired
            ],
        }
