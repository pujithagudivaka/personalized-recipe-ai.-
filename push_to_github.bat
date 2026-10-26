@echo off
echo ============================================================
echo Pushing Personalized Recipe AI to GitHub Repository:
echo https://github.com/pujithagudivaka/personalized-recipe-ai.-.git
echo ============================================================
cd /d "%~dp0"
git push -u origin main
echo ============================================================
echo Push complete! Press any key to exit.
echo ============================================================
pause
