from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("RDE_REFLEX_HOST", "127.0.0.1")
    port = int(os.getenv("RDE_REFLEX_PORT", "8787"))
    uvicorn.run("rde_reflex.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
