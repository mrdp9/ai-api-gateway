@echo off
REM ============================================================================
REM AI API Gateway - One-Command Deployment Script (Windows)
REM ============================================================================
REM This script automates the entire deployment process:
REM 1. Check prerequisites (Docker, Docker Compose)
REM 2. Create .env file if missing
REM 3. Validate configuration
REM 4. Build Docker images
REM 5. Start services (API, Tunnel, Notifier)
REM 6. Monitor deployment progress
REM 7. Display access URLs and next steps
REM
REM Usage: deploy.bat
REM ============================================================================

setlocal enabledelayedexpansion

REM Color codes (Note: Windows cmd has limited color support)
set ERROR=[91m
set SUCCESS=[92m
set WARNING=[93m
set INFO=[94m
set NORMAL=[0m

cls

echo ================================================================================
echo   AI API Gateway - One-Command Deployment Script
echo ================================================================================
echo.

REM ============================================================================
REM STEP 1: Check Prerequisites
REM ============================================================================

echo [1/6] Checking Prerequisites...
echo.

set /a MISSING=0

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo         Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    set /a MISSING+=1
) else (
    for /f "tokens=*" %%i in ('docker --version') do set DOCKER_VERSION=%%i
    echo [OK] Docker installed: !DOCKER_VERSION!
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed
    echo         Please install Docker Compose or use 'docker compose'
    set /a MISSING+=1
) else (
    for /f "tokens=*" %%i in ('docker-compose --version') do set COMPOSE_VERSION=%%i
    echo [OK] Docker Compose installed: !COMPOSE_VERSION!
)

REM Check Docker daemon
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running
    echo         Please start Docker Desktop
    set /a MISSING+=1
) else (
    echo [OK] Docker daemon is running
)

if !MISSING! gtr 0 (
    echo.
    echo [ERROR] Missing !MISSING! prerequisite(s). Please install and try again.
    pause
    exit /b 1
)

echo [OK] All prerequisites met!
echo.

REM ============================================================================
REM STEP 2: Configure Environment
REM ============================================================================

echo [2/6] Configuring Environment...
echo.

if exist .env (
    echo [INFO] .env file already exists
    set /p UPDATE="Do you want to update it? (y/n): "
    if /i not "!UPDATE!"=="y" (
        echo [INFO] Keeping existing .env file
        goto :skip_env_copy
    )
)

if not exist .env.example (
    echo [ERROR] .env.example not found
    pause
    exit /b 1
)

copy .env.example .env >nul
echo [OK] Created .env file from .env.example
echo.

REM Auto-generate SECRET_KEY if empty
findstr /r "^SECRET_KEY=$" .env >nul
if !errorlevel! equ 0 (
    echo [INFO] Auto-generating SECRET_KEY...
    
    REM Try Python
    python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >key_temp.txt 2>nul
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%i in (key_temp.txt) do (
            set SECRET_LINE=%%i
        )
        
        REM Replace in .env
        for /f "usebackq tokens=*" %%i in ("key_temp.txt") do (
            set SECRET_LINE=%%i
            goto :found_secret
        )
        :found_secret
        
        REM Update .env using PowerShell
        powershell -Command "(Get-Content .env) -replace '^SECRET_KEY=.*$', '!SECRET_LINE!' | Set-Content .env" 2>nul
        del key_temp.txt >nul
        echo [OK] Generated SECRET_KEY
    )
)

:skip_env_copy

echo [WARNING] Please edit .env file with your configuration:
echo.
echo   Required:
echo   - TUNNEL_TOKEN (from CloudFlare dashboard)
echo   - SMTP_USER (your Gmail address)
echo   - SMTP_PASSWORD (Gmail app password - 16 char)
echo.
echo   Optional (has defaults):
echo   - ADMIN_PASS (admin dashboard password)
echo.

set /p EDIT_ENV="Do you want to edit .env now? (y/n): "
if /i "!EDIT_ENV!"=="y" (
    if exist "%PROGRAMFILES%\Git\usr\bin\nano.exe" (
        "%PROGRAMFILES%\Git\usr\bin\nano.exe" .env
    ) else if exist "%WINDIR%\notepad.exe" (
        "%WINDIR%\notepad.exe" .env
        echo.
        pause
    )
)
echo.

REM ============================================================================
REM STEP 3: Validate Configuration
REM ============================================================================

echo [3/6] Validating Configuration...
echo.

set /a ERRORS=0

REM Check .env exists
if not exist .env (
    echo [ERROR] .env file not found
    set /a ERRORS+=1
)

REM Check TUNNEL_TOKEN
for /f "usebackq tokens=2 delims==" %%i in (`findstr "^TUNNEL_TOKEN=" .env`) do set TUNNEL_TOKEN=%%i
if "!TUNNEL_TOKEN!"=="" (
    echo [ERROR] TUNNEL_TOKEN not configured in .env
    set /a ERRORS+=1
) else (
    echo [OK] TUNNEL_TOKEN configured
)

REM Check SMTP
for /f "usebackq tokens=2 delims==" %%i in (`findstr "^SMTP_USER=" .env`) do set SMTP_USER=%%i
if "!SMTP_USER!"=="" (
    echo [WARNING] SMTP_USER not configured (email will be logged only)
) else (
    echo [OK] SMTP_USER configured
)

REM Check docker-compose.yml
if not exist docker-compose.yml (
    echo [ERROR] docker-compose.yml not found
    set /a ERRORS+=1
) else (
    echo [OK] docker-compose.yml found
)

if !ERRORS! gtr 0 (
    echo.
    echo [ERROR] Configuration validation failed!
    pause
    exit /b 1
)

echo [OK] Configuration validated!
echo.

REM ============================================================================
REM STEP 4: Build & Start Services
REM ============================================================================

echo [4/6] Building and Starting Services...
echo.

echo [INFO] Building Docker images (this may take a few minutes)...
docker-compose build
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Docker images
    pause
    exit /b 1
)
echo [OK] Docker images built successfully
echo.

echo [INFO] Starting services...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services
    docker-compose logs
    pause
    exit /b 1
)
echo [OK] Services started
echo.

echo [INFO] Started services:
echo   - API service (FastAPI on port 3001)
echo   - Tunnel service (CloudFlare)
echo   - Notifier service (URL registration)
echo.

REM ============================================================================
REM STEP 5: Wait for Tunnel
REM ============================================================================

echo [5/6] Waiting for Tunnel to Establish (30-60 seconds)...
echo.

set TUNNEL_FOUND=0
for /l %%i in (1,1,60) do (
    REM Try to find tunnel URL in logs
    docker-compose logs 2>nul | findstr "trycloudflare.com" >nul
    if !errorlevel! equ 0 (
        set TUNNEL_FOUND=1
        echo [OK] Tunnel URL detected!
        goto :tunnel_done
    )
    
    REM Check if tunnel is running
    docker-compose logs tunnel 2>nul | findstr "Tunnel is running" >nul
    if !errorlevel! equ 0 (
        echo [INFO] Tunnel is connected (%%i/60 seconds)
    ) else (
        echo [INFO] Connecting to CloudFlare (%%i/60 seconds)
    )
    
    timeout /t 1 /nobreak >nul
)

:tunnel_done

if !TUNNEL_FOUND! equ 0 (
    echo [WARNING] Tunnel URL not found in logs
    echo           It may have been sent via email
    echo.
)

REM ============================================================================
REM STEP 6: Display Status
REM ============================================================================

echo [6/6] Deployment Complete!
echo.

cls

echo ================================================================================
echo   Deployment Complete!
echo ================================================================================
echo.

echo Service Status:
docker-compose ps
echo.

echo ================================================================================
echo   ACCESS URLS
echo ================================================================================
echo.
echo Local (No Tunnel Required):
echo   http://localhost:3001/
echo.
echo Internet (Via CloudFlare Tunnel):
echo   Check your email at: prjctxno@gmail.com
echo   Subject: "Your AI API Gateway Tunnel URL"
echo.

echo ================================================================================
echo   LOGIN CREDENTIALS
echo ================================================================================
echo.
echo Username: admin
echo Password: (from ADMIN_PASS in .env)
echo.

echo ================================================================================
echo   NEXT STEPS
echo ================================================================================
echo.
echo 1. Access the dashboard:
echo    http://localhost:3001/
echo.
echo 2. Create API Keys:
echo    - Click "Create New Key"
echo    - Set expiration (1-365 days)
echo    - Copy the key (shown only once!)
echo.
echo 3. Use Your API:
echo    curl -X GET http://localhost:3001/health ^
echo      -H "x-api-key: YOUR-KEY-HERE"
echo.

echo ================================================================================
echo   USEFUL COMMANDS
echo ================================================================================
echo.
echo View Logs:
echo   docker-compose logs -f api              (API logs)
echo   docker-compose logs -f tunnel           (Tunnel logs)
echo   docker-compose logs -f                  (All logs)
echo.
echo Manage Services:
echo   docker-compose restart                  (Restart all)
echo   docker-compose stop                     (Stop all)
echo   docker-compose down                     (Remove services)
echo   docker-compose up -d                    (Start in background)
echo.
echo Testing:
echo   curl http://localhost:3001/health       (Health check)
echo.

echo ================================================================================
echo.
echo [OK] Your AI API Gateway is now running!
echo.
echo For more information, read QUICK_START.md or SETUP_GUIDE.md
echo.

pause
