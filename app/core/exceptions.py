class ErrorNegocio(Exception):
    """Error controlado: lleva el mensaje y el código HTTP que se debe devolver."""

    def __init__(self, mensaje: str, codigo_http: int = 400, data=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_http = codigo_http
        self.data = data