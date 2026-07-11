@echo off
setlocal

echo Generating SSH key...
"D:\Git\usr\bin\ssh-keygen.exe" -t ed25519 -C "litchi1058@gmail.com" -f "%USERPROFILE%\.ssh\id_ed25519_github" -N ""

echo.
echo Key generated at: %USERPROFILE%\.ssh\id_ed25519_github
echo.
echo Public key content:
type "%USERPROFILE%\.ssh\id_ed25519_github.pub"

endlocal