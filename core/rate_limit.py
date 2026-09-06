from slowapi import Limiter
from slowapi.util import get_remote_address

# Gunakan get_forwarded_for jika di belakang proxy (NGINX/Heroku/Render)
# Atau ganti dengan get_remote_address untuk direkt langsung
def get_forwarded_for():
    """Ambil IP dari header X-Forwarded-For jika ada."""
    def _get_remote_address(request):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return get_remote_address(request)
    return _get_remote_address

limiter = Limiter(key_func=get_forwarded_for())
