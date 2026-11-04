import bcrypt
import hashlib
import base64

class Hash:
    @staticmethod
    def _prepare(password: str) -> bytes:
        digest = hashlib.sha256(password.encode()).digest()
        return base64.b64encode(digest)

    @staticmethod
    def bcrypt(password: str) -> str:
        return bcrypt.hashpw(Hash._prepare(password), bcrypt.gensalt()).decode()

    @staticmethod
    def verify(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(Hash._prepare(password), hashed_password.encode())
