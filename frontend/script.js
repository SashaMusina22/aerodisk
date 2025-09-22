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
        const baseIndent = 10;
        const extraIndent = d.level * 20;
        const nameCell = `<td style="padding-left:${baseIndent + extraIndent}px">${d.name}</td>`;


        const actionButtons = d.has_children ? "" : `
            <button class="btn btn-success btn-sm" onclick="mountDisk('${d.name}')">Монтировать</button>
            <button class="btn btn-warning btn-sm" onclick="umountDisk('${d.name}')">Демонтировать</button>
            <button class="btn btn-danger btn-sm" onclick="formatDisk('${d.name}')">Форматировать</button>
        `;

        const mountSelect = d.has_children ? "" : `
            <select id="path-${d.name}" class="form-select form-select-sm">
                ${mountList.map(m => `<option value="/mnt/${m}">/mnt/${m}</option>`).join("")}
            </select>
        `;

        row.innerHTML = `
            ${nameCell}
            <td>${d.size}</td>
            <td>${d.mountpoint || "—"}</td>
            <td>${mountSelect}</td>
            <td>${actionButtons}</td>
            >
        `;
        table.appendChild(row);
    });
}

async function mountDisk(name) {
    const path = document.getElementById(`path-${name}`).value;
    const res = await fetch(`/mount?name=${name}&path=${path}`, { method: "POST" });
    alert(JSON.stringify(await res.json()));
    loadDisks();
}

async function umountDisk(name) {
    const res = await fetch(`/umount?name=${name}`, { method: "POST" });
    alert(JSON.stringify(await res.json()));
    loadDisks();
}

async function formatDisk(name) {
    const res = await fetch(`/format?name=${name}`, { method: "POST" });
    alert(JSON.stringify(await res.json()));
    loadDisks();
}

async function createMountpoint() {
    const name = prompt("Введите имя новой точки монтирования (например: data1):");
    if (!name) return;
    const res = await fetch(`/create_mountpoint?name=${name}`, { method: "POST" });
    alert(JSON.stringify(await res.json()));
    loadDisks();
}

window.onload = loadDisks;
