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
        for d in disks_data["blockdevices"]:
            if d["name"].startswith("loop") or d["name"] in ["vda", "sda", "sr0"]:
                continue

            disks.append({
                "name": d["name"],
                "size": d["size"],
                "mountpoint": d["mountpoint"]
            })

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
        check = subprocess.run(
            ["mount"], capture_output=True, text=True
        )

        for line in check.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                dev, _, mountpoint = parts[0], parts[1], parts[2]
                if mountpoint == path and dev != f"/dev/{name}":
                    return {"error": f"Точка монтирования {path} уже используется устройством {dev}"}
                if dev == f"/dev/{name}":
                    return {"error": f"Диск {name} уже примонтирован в {mountpoint}"}

        result = subprocess.run(
            ["sudo", "-n", "mount", f"/dev/{name}", path],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            if "already mounted" in result.stderr.lower():
                return {"error": f"Диск {name} уже примонтирован"}
            elif "does not exist" in result.stderr.lower():
                return {"error": f"Устройство /dev/{name} не существует"}
            elif "mount point does not exist" in result.stderr.lower():
                return {"error": f"Точка монтирования {path} не существует"}
            else:
                return {"error": f"Ошибка при монтировании {name}: {result.stderr.strip()}"}

        return {"message": f"Диск {name} примонтирован в {path}"}

    except Exception as e:
        return {"error": str(e)}


@app.post("/umount")
def umount_disk(name: str):
    try:
        result = subprocess.run(
            ["sudo", "-n", "umount", f"/dev/{name}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            if "not mounted" in result.stderr.lower():
                return {"error": f"Не удалось отмонтировать {name}: диск не был примонтирован"}
            return {"error": f"Ошибка при отмонтировании {name}: {result.stderr.strip()}"}

        return {"message": f"Диск {name} отмонтирован"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/format")
def format_disk(name: str, fstype: str = "ext4"):
    try:
        result = subprocess.run(
            ["sudo", "-n", "mkfs", "-t", fstype, "-F", f"/dev/{name}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            if "is mounted" in result.stderr:
                return {"error": f"Не удалось отформатировать {name}: диск смонтирован. Сначала отмонтируй его."}
            if "No such file" in result.stderr:
                return {"error": f"Не удалось отформатировать {name}: такого диска не существует."}
            if "busy" in result.stderr:
                return {"error": f"Не удалось отформатировать {name}: диск сейчас используется системой."}
            return {"error": f"Ошибка при форматировании {name}: {result.stderr.strip()}"}

        return {"message": f"Диск {name} успешно отформатирован в {fstype}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка при форматировании: {str(e)}"}


@app.post("/create_mountpoint")
def create_mountpoint(name: str):
    try:
        path = name

        os.makedirs(path, exist_ok=True)

        result = subprocess.run(
            ["sudo", "-n", "chown", f"{os.getlogin()}:{os.getlogin()}", path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"error": f"Ошибка при изменении владельца {path}: {result.stderr.strip()}"}

        return {"message": f"Точка монтирования {path} создана"}

    except Exception as e:
        return {"error": str(e)}
