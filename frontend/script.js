async function loadDisks() {
    const response = await fetch("/disks");
    const disks = await response.json();

    const responseMounts = await fetch("/mountpoints");
    const mounts = await responseMounts.json();
    const mountList = mounts.mountpoints || [];

    const table = document.getElementById("disks");
    table.innerHTML = "";

    disks.forEach(d => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${d.name}</td>
            <td>${d.size}</td>
            <td>${d.mountpoint || "—"}</td>
            <td>
                <select id="path-${d.name}" class="form-select form-select-sm">
                    ${mountList.map(m => `<option value="/mnt/${m}">/mnt/${m}</option>`).join("")}
                </select>
            </td>
            <td>
                <button class="btn btn-success btn-sm" onclick="mountDisk('${d.name}')">Монтировать</button>
                <button class="btn btn-warning btn-sm" onclick="umountDisk('${d.name}')">Демонтировать</button>
                <button class="btn btn-danger btn-sm" onclick="formatDisk('${d.name}')">Форматировать</button>
            </td>
        `;

        table.appendChild(row);
    });
}

async function mountDisk(name) {
    const path = document.getElementById(`path-${name}`).value;
    const res = await fetch(`/mount?name=${name}&path=${path}`, {method: "POST"});
    const data = await res.json();
    alert(JSON.stringify(data));
    loadDisks();
}

async function umountDisk(name) {
    const res = await fetch(`/umount?name=${name}`, {method: "POST"});
    const data = await res.json();
    alert(JSON.stringify(data));
    loadDisks();
}

async function formatDisk(name) {
    const res = await fetch(`/format?name=${name}`, {method: "POST"});
    const data = await res.json();
    alert(JSON.stringify(data));
    loadDisks();
}

async function createMountpoint() {
    const name = prompt("Введите имя новой точки монтирования (например: data1):");
    if (!name) return;

    const res = await fetch(`/create_mountpoint?name=${name}`, {method: "POST"});
    const data = await res.json();
    alert(JSON.stringify(data));
    loadDisks();
}

window.onload = loadDisks;
