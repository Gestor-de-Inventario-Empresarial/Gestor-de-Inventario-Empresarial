def respuesta(success: bool, data, message: str) -> dict:
    """Estructura estándar de TODAS las respuestas: success, data y message."""
    return {"success": success, "data": data, "message": message}