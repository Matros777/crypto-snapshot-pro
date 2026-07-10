app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/app")
async def web_app():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Web interface not found</h1>", status_code=404)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "crypto-snapshot-pro", "proxy_enabled": USE_PROXY}

# ============================================================
# ГЛАВНАЯ СТРАНИЦА — РЕДИРЕКТ НА /app (ПЕРВЫЙ!)
# ============================================================
@app.get("/")
async def root():
    return RedirectResponse(url="/app")

# ============================================================
# ЯНДЕКС ФАЙЛ ДЛЯ ВЕРИФИКАЦИИ
# ============================================================
@app.get("/yandex_d100e212bdd18c7b.html")
async def yandex_verify():
    return HTMLResponse("""
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        </head>
        <body>Verification: d100e212bdd18c7b</body>
    </html>
    """)
