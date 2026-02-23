"""
Security-hardening middleware for ExileQuest.

Adds Content-Security-Policy, Permissions-Policy, and other
defense-in-depth headers that Django doesn't provide out of the box.
"""

from django.conf import settings


class SecurityHeadersMiddleware:
    """Inject additional security headers into every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # ── Content-Security-Policy ──────────────────────────────────
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "object-src 'none'",
        ]
        response["Content-Security-Policy"] = "; ".join(csp_directives)

        # ── Permissions-Policy ───────────────────────────────────────
        permissions = [
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()",
            "interest-cohort=()",
        ]
        response["Permissions-Policy"] = ", ".join(permissions)

        # ── Additional headers ───────────────────────────────────────
        response["X-Permitted-Cross-Domain-Policies"] = "none"
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        response["Cross-Origin-Resource-Policy"] = "same-origin"
        response["Cross-Origin-Embedder-Policy"] = "require-corp"

        return response
