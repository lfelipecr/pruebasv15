class Voucher:
    TYPE_TO_CODE = {
        "normal": "1",
        "contingencia": "2",
        "sininternet": "3",
    }


class Sequence:
    @staticmethod
    def valid(sequence):
        return sequence.isdigit() and len(sequence) == 10


class Environment:
    class STAGING:
        client_id = "api-stag"
        token_endpoint = "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token"
        reception_endpoint = "https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1/recepcion"
        #reception_endpoint = "https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/recepcion"

    class PRODUCTION:
        client_id = "api-prod"
        token_endpoint = "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token"
        reception_endpoint = "https://api.comprobanteselectronicos.go.cr/recepcion/v1/recepcion"

    _client_id_to_class = {
        "api-stag": STAGING,
        "api-prod": PRODUCTION,
    }

    @staticmethod
    def get(client_id):
        return Environment._client_id_to_class[client_id]
