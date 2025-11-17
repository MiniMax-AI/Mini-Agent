@echo off
REM 初始化共享环境脚本 (Windows)

echo 🚀 开始初始化 Mini-Agent 共享环境...

REM 进入后端目录
cd /d "%~dp0.."

REM 创建目录
echo 📁 创建目录结构...
if not exist "data\shared_env" mkdir "data\shared_env"
if not exist "data\workspaces" mkdir "data\workspaces"
if not exist "data\database" mkdir "data\database"

REM 检查 Python
echo 🐍 检查 Python 版本...
python --version
if errorlevel 1 (
    echo ❌ Python 未安装或不在 PATH 中
    exit /b 1
)

REM 创建虚拟环境
set VENV_DIR=data\shared_env\base.venv
if exist "%VENV_DIR%" (
    echo ⚠️  虚拟环境已存在，跳过创建
) else (
    echo 🔨 创建虚拟环境: %VENV_DIR%
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ❌ 创建虚拟环境失败
        exit /b 1
    )
)

REM 激活虚拟环境
echo ✨ 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo ❌ 激活虚拟环境失败
    exit /b 1
)

REM 升级 pip
echo 📦 升级 pip...
python -m pip install --upgrade pip

REM 安装允许的包
set PACKAGES_FILE=data\shared_env\allowed_packages.txt
if exist "%PACKAGES_FILE%" (
    echo 📚 安装允许的包...
    for /f "usebackq tokens=*" %%i in ("%PACKAGES_FILE%") do (
        echo   📦 安装: %%i
        pip install "%%i" || echo   ⚠️  安装 %%i 失败，继续...
    )
) else (
    echo ⚠️  找不到 allowed_packages.txt，跳过包安装
)

echo.
echo ✅ 共享环境初始化完成！
echo 📍 虚拟环境路径: %VENV_DIR%
echo.

pause
