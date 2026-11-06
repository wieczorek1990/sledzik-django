from django.http import HttpResponse
from django.utils.cache import patch_vary_headers


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse(status=200)
            self.add_cors_headers(request, response)
            return response

        response = self.get_response(request)
        self.add_cors_headers(request, response)
        return response

    def add_cors_headers(self, request, response):
        origin = request.headers.get("Origin")
        if origin:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            patch_vary_headers(response, ["Origin"])
        else:
            response["Access-Control-Allow-Origin"] = "*"

        req_headers = request.headers.get("Access-Control-Request-Headers")
        if req_headers:
            response["Access-Control-Allow-Headers"] = req_headers
        else:
            response["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type, X-Requested-With, Accept, Origin, User-Agent"
            )

        response["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
        )
        response["Access-Control-Max-Age"] = "86400"
