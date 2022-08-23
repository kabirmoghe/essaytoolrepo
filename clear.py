import os
import shutil

def clear():
	files = os.listdir()
	needed = ["__pycache__", ".DS_Store", "clear.py", "creds.json", "modDriveConnect.py", "produceStudentSents.py", "requirements.txt", "functioningProdSents.py", "app", "runScript.cron", "test.py", "errors.txt", "logs.txt"]

	for f in files:
		if f not in needed:
			shutil.rmtree(f)


if __name__ == "__main__":
	clear()
