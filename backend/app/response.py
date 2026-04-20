from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def success_response(message: str, data=None, status_code: int = 200) -> JSONResponse:
    content = jsonable_encoder(
        {
            "success": True,
            "message": message,
            "data": data,
        }
    )
    return JSONResponse(
        status_code=status_code,
        content=content,
    )


def error_response(message: str, status_code: int = 400, error=None) -> JSONResponse:
    content = jsonable_encoder(
        {
            "success": False,
            "message": message,
            "error": error if error is not None else {},
        }
    )
    return JSONResponse(
        status_code=status_code,
        content=content,
    )
