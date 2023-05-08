pyInstaller ..\JsonServer.py --onedir --name NozzleAnalyzer --noconsole --noconfirm --noupx
xcopy "..\CamBeam.json" "dist\NozzleAnalyzer\" /Y
xcopy "..\CamNozzle.json" "dist\NozzleAnalyzer\" /Y
xcopy "..\CamGeneral.json" "dist\NozzleAnalyzer\" /Y
xcopy "..\laser2.png" "dist\NozzleAnalyzer\" /Y
xcopy "..\pngfind.com-not-allowed-symbol-png-5982091_256_inverted.png" "dist\NozzleAnalyzer\" /Y