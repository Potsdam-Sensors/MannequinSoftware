IF EXIST "%USERPROFILE%\MannequinSQLMount" (
    echo 0 > nul
) ELSE (
    mkdir "%USERPROFILE%\MannequinSQLMount"
)
icacls "%USERPROFILE%\MannequinSQLMount" /grant "Everyone:(OI)(CI)F"

IF EXIST "%USERPROFILE%\Desktop\mannequin_software_assets" (
    echo 0 > nul
) ELSE (
    mkdir "%USERPROFILE%\Desktop\mannequin_software_assets"
)

IF EXIST "%USERPROFILE%\Desktop\mannequin_software_assets\placements.csv" (
    echo 0 > nul
) ELSE (
    echo serial_number,sensor,x,y> "%USERPROFILE%\Desktop\mannequin_software_assets\placements.csv"
)