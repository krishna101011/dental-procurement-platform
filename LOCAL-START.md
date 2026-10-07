# Local startup

Open PowerShell in the repository root and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force; .\START-LOCAL.ps1
```

The launcher forces SQLite for local use, installs backend/frontend dependencies, seeds the demo database, waits for FastAPI health before opening the frontend, and uses `127.0.0.1` consistently to avoid Windows localhost IPv4/IPv6 connection issues.

Frontend: http://127.0.0.1:5174/
Backend: http://127.0.0.1:8000/
Swagger: http://127.0.0.1:8000/docs

Demo customer: doctor@example.com / Demo@12345
Admin: admin@example.com / Admin@12345
Supplier: supplier@example.com / Supplier@12345
