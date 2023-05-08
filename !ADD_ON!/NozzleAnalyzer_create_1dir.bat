pyInstaller ..\JsonServer.py --onedir --name NozzleAnalyzer --noconsole --noconfirm
xcopy "..\config.json" "dist\NozzleAnalyzer\" /Y
xcopy "..\laser2.png" "dist\NozzleAnalyzer\" /Y
xcopy "..\no_camera-512-white.png" "dist\NozzleAnalyzer\" /Y