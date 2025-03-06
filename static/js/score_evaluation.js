document.addEventListener("DOMContentLoaded", async function () {
    async function fetchUserInfo() {
        try {
            const response = await fetch("/api/me", {
                method: "GET",
                credentials: "include"
            });

            if (!response.ok) throw new Error("无法获取用户信息");

            const data = await response.json();
            return data.userinfo;
        } catch (error) {
            console.error("获取用户信息失败:", error);
            return null;
        }
    }

    async function fetchStaffList(userinfo) {
        try {
            const response = await fetch("/staffChecked", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ userinfo })
            });

            if (!response.ok) throw new Error("无法获取员工列表");

            return await response.json();
        } catch (error) {
            console.error("获取员工列表失败:", error);
            return [];
        }
    }

    async function fetchEvaluationTables(departmentid) {
        try {
            const response = await fetch("/showtablelist", { method: "GET" });

            if (!response.ok) throw new Error("无法获取评测表");

            return await response.json();
        } catch (error) {
            console.error("获取评测表失败:", error);
            return [];
        }
    }

    async function main() {
        const userinfo = await fetchUserInfo();
        if (!userinfo) return;

        const staffList = await fetchStaffList(userinfo);
        if (staffList.length > 0) {
            renderStaffTable(staffList);
        } else {
            console.warn("未获取到员工列表");
        }
    }

    function renderStaffTable(staffList) {
        const tableBody = document.querySelector(".employee-table tbody");
        if (!tableBody) return;
        tableBody.innerHTML = "";
        console.log(staffList);
        staffList.forEach(staff => {
            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${staff.emp_id || "-"}</td>
                <td>${staff.position || "-"}</td>
                <td>${staff.emp_name || "-"}</td>
                <td>${staff.department || "-"}</td>
                <td>${staff.ProductGroup || "-"}</td>
                <td>${staff.ismanage ? "是" : "否"}</td>
                <td><button class="score-btn" data-emp-id="${staff.emp_id}">评分</button></td>
            `;

            tableBody.appendChild(row);
        });

        document.querySelectorAll(".score-btn").forEach(button => {
            button.addEventListener("click", async function () {
                const empId = this.getAttribute("data-emp-id");
                showEvaluationModal(empId);
            });
        });
    }

    async function showEvaluationModal(empId) {
        const modalOverlay = document.createElement("div");
        modalOverlay.classList.add("modal-overlay");

        const modal = document.createElement("div");
        modal.classList.add("modal");

        modal.innerHTML = `
            <h2>对员工 ${empId} 进行评分</h2>
            <label for="evaluation-select">选择评测表：</label>
            <select id="evaluation-select">
                <option value="">加载中...</option>
            </select>
            <button id="confirm-btn">确认</button>
            <button class="close-btn">关闭</button>
        `;

        modalOverlay.appendChild(modal);
        document.body.appendChild(modalOverlay);
        // 使用 await 获取 TableList
        let TableList = await fetchEvaluationTables();
        console.log(typeof TableList);  // 检查 TableList 类型

        // 如果 fetch 返回空数组或错误，可以根据需要进行处理
        if (Array.isArray(TableList)) {
            const SelectBody = document.getElementById("evaluation-select");
            SelectBody.innerHTML = "";

            TableList.forEach(table => {
                const option = document.createElement("option");
                option.value = table.id;
                option.textContent = table.name;
                SelectBody.appendChild(option);
            });
        } else {
            console.error('TableList 不是有效的数组');
        }
        document.querySelector(".modal .close-btn").addEventListener("click", async function () {
            modalOverlay.remove()
        })
        document.getElementById("confirm-btn").addEventListener("click", async function () {
            const selectedTableId = document.getElementById("evaluation-select").value;
            if (!selectedTableId) {
                alert("请选择评测表");}
            window.location.href = `/score?emp_id=${empId}&table_id=${selectedTableId}`;
        });
        modalOverlay.style.display = "block";
    }


    main();
});
