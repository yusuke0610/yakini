import io

from fastapi.responses import StreamingResponse


def stream_pdf(data: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


def stream_markdown(text: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
