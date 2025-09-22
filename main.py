from fastapi import FastAPI
import subprocess
import json
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI()

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/ui", StaticFiles(directory=FRONTEND_DIR), name="ui")


@app.get("/")
def read_root():
    return RedirectResponse(url="/ui/index.html")


@app.get("/disks")
def get_disks():
    try:
        result = subprocess.run(
            ["lsblk", "-o", "NAME,SIZE,MOUNTPOINT", "-J"],
            capture_output=True, text=True, check=True
        )
        disks_data = json.loads(result.stdout)

        disks = []

        def parse_device(dev, level=0):
            disks.append({
                "name": dev["name"],
                "size": dev["size"],
                "mountpoint": dev.get("mountpoint") or "",
                "level": level,
                "has_children": "children" in dev and len(dev["children"]) > 0
            })
            for child in dev.get("children", []):
                parse_device(child, level + 1)

        for d in disks_data["blockdevices"]:
            if d["name"].startswith("loop") or d["name"] in ["sr0"]:
                continue
            parse_device(d)

        return disks
    except Exception as e:
        return {"error": f"Не удалось получить список дисков: {str(e)}"}


@app.get("/mountpoints")
def list_mountpoints():
    try:
        dirs = [d for d in os.listdir("/mnt") if os.path.isdir(os.path.join("/mnt", d))]
        return {"mountpoints": dirs}
    except Exception as e:
        return {"error": str(e)}


@app.post("/mount")
def mount_disk(name: str, path: str):
    try:
        result = subprocess.run(["sudo", "-n", "mount", f"/dev/{name}", path], capture_output=True, text=True)
        if result.returncode != 0:
            return {"error": result.stderr.strip() or "Ошибка монтирования"}
        return {"message": f"Диск {name} примонтирован в {path}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/umount")
def umount_disk(name: str):
    try:
        result = subprocess.run(["sudo", "-n", "umount", f"/dev/{name}"], capture_output=True, text=True)
        if result.returncode != 0:
            return {"error": result.stderr.strip() or "Ошибка отмонтирования"}
        return {"message": f"Диск {name} отмонтирован"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/format")
def format_disk(name: str, fstype: str = "ext4"):
    try:
        result = subprocess.run(["sudo", "-n", "mkfs", "-t", fstype, "-F", f"/dev/{name}"], capture_output=True, text=True)
        if result.returncode != 0:
            return {"error": result.stderr.strip() or "Ошибка форматирования"}
        return {"message": f"Диск {name} отформатирован в {fstype}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/create_mountpoint")
def create_mountpoint(name: str):
    try:
        os.makedirs(name, exist_ok=True)
        subprocess.run(["sudo", "-n", "chown", f"{os.getlogin()}:{os.getlogin()}", name], capture_output=True, text=True)
        return {"message": f"Точка монтирования {name} создана"}
    except Exception as e:
        return {"error": str(e)}