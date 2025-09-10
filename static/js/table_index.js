document.addEventListener("DOMContentLoaded", function () {
    loadTableData(); // 页面加载时获取考核表
    function openModal() {
        document.getElementById("modal-overlay").style.display = "flex"; // 显示弹窗
    }

// 关闭弹窗

    // 获取考核表数据并展示
    function loadTableData() {
        fetch("/gettable")
            .then(response => response.json())
            .then(data => {
                const tbody = document.querySelector(".assessment-table tbody");
                tbody.innerHTML = ""; // 清空表格，避免重复加载

                data.forEach(row => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${row.name}</td>
                        <td>${row.departmentid}</td>
                        <td>${row.departmentname}</td>
                        <td>${row.deadline}</td>
                        <td>
                            <button class="view-btn" data-name="${row.name}">查看</button>
                            <button class="delete-btn" data-name="${row.name}" data-departmentid = "${row.departmentid}">删除</button>
                            <button class="copy-btn" data-name="${row.name}">复制</button>
                                                    </td>
                    `;
                    tbody.appendChild(tr);
                });

                // 绑定查看按钮
                document.querySelectorAll(".view-btn").forEach(btn => {
                    btn.addEventListener("click", function () {
                        viewTable(this.getAttribute("data-name"));
                    });
                });

                // 绑定删除按钮
                document.querySelectorAll(".delete-btn").forEach(btn => {
                    btn.addEventListener("click", function () {
                        deleteTable(this.getAttribute("data-name"),this.getAttribute("data-departmentid"));
                    });
                });
                document.querySelectorAll(".copy-btn").forEach(btn => {
                    btn.addEventListener("click", function () {
                        copyTable(this.getAttribute("data-name"));
                    });
                });

            })
            .catch(error => console.error("Error fetching table data:", error));
    }
    function deleteTable(version,departmentid) {
        fetch("/deletetable", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({version: version, departmentid:departmentid })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("删除成功");
                    loadTableData(); // 更新表格
                } else {
                    alert("删除失败");
                }
            });
    }


    // 查看考核表
    function viewTable(version) {
        if (!version) {
            console.error("Error: 缺少版本参数");
            alert("无法编辑表格，缺少必要的版本信息");
            return;
        }

        // 可以添加确认对话
            // 直接跳转到编辑界面，携带version参数
        window.location.href = `/edittable?version=${version}`;
    }

    // 显示考核表详情
// 显示考核表详情
    function copyTable(version) {
        // 先获取所有部门数据
        fetch("/showalldepartment")
            .then(response => response.json())
            .then(departments => {
                // 创建并显示复制弹窗
                showCopyModal(version, departments);
            })
            .catch(error => {
                console.error("Error fetching departments:", error);
                alert("获取部门信息失败，请稍后重试");
            });
    }

// 显示复制弹窗
    function showCopyModal(version, departments) {
        // 创建模态窗口元素
        const modalOverlay = document.createElement("div");
        modalOverlay.className = "modal-overlay";
        modalOverlay.id = "copy-modal-overlay";
        modalOverlay.style.display = "flex";

        const currentYear = new Date().getFullYear();
        const yearOptions = generateYearOptions(currentYear);

        // 创建模态窗口内容
        const modalContainer = document.createElement("div");
        modalContainer.className = "modal-container";

        modalContainer.innerHTML = `
        <div class="modal-header">
            <span class="modal-title">复制绩效考核表</span>
            <span class="close-btn" id="close-copy-modal">×</span>
        </div>
        <div class="modal-content">
            <div class="form-group">
                <label for="copy-year">选择年份:</label>
                <select class="form-input" id="copy-year">
                    ${yearOptions}
                </select>
            </div>
            <div class="form-group">
                <label for="copy-quarter">选择季度:</label>
                <select class="form-input" id="copy-quarter">
                    <option value="Q1">Q1</option>
                    <option value="Q2">Q2</option>
                    <option value="Q3">Q3</option>
                    <option value="Q4">Q4</option>
                </select>
            </div>
            <div class="form-group">
                <label for="copy-month">选择月份:</label>
                <select class="form-input" id="copy-month">
                    <option value="M1">M1</option>
                    <option value="M2">M2</option>
                    <option value="M3">M3</option>
                    <option value="--">--</option>
                </select>
            </div>
            <div class="form-group">
                <label for="copy-department">选择部门:</label>
                <select class="form-input" id="copy-department">
                    ${departments.map(dept => `<option value="${dept.id}">${dept.name}</option>`).join('')}
                </select>
            </div>
        </div>
        <div class="modal-footer">
            <button class="modal-close-btn" id="cancel-copy-btn">取消</button>
            <button class="modal-action-btn" id="confirm-copy-btn">确定复制</button>
        </div>
    `;

        modalOverlay.appendChild(modalContainer);
        document.body.appendChild(modalOverlay);

        // 绑定关闭按钮事件
        document.getElementById("close-copy-modal").addEventListener("click", function() {
            document.body.removeChild(modalOverlay);
        });

        // 绑定取消按钮事件
        document.getElementById("cancel-copy-btn").addEventListener("click", function() {
            document.body.removeChild(modalOverlay);
        });

        // 点击模态窗口外部关闭
        modalOverlay.addEventListener("click", function(event) {
            if (event.target === modalOverlay) {
                document.body.removeChild(modalOverlay);
            }
        });

        // 绑定确认复制按钮事件
        document.getElementById("confirm-copy-btn").addEventListener("click", function() {
            const year = document.getElementById("copy-year").value;
            const quarter = document.getElementById("copy-quarter").value;
            const month = document.getElementById("copy-month").value;
            const departmentid = document.getElementById("copy-department").value;

            // 调用复制API
            token = getToken();
            console.log("version:",version,"year:",year,"quarter:",quarter,"month:",month,"departmentid:",departmentid);
            fetch("/copytable", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    version: version,
                    year: year,
                    quarter: quarter,
                    month: month,
                    departmentid: departmentid
                })
            })
                .then(response => response.json())
                .then(data => {
                    document.body.removeChild(modalOverlay);

                    if (data.success) {
                        showNotification("复制成功:" + data.version, "success");
                        // 成功后重定向到table_index页面
                        setTimeout(() => {
                            window.location.href = "/table_index";
                        }, 1500);
                    } else {
                        console.log("Error copying table:", data.message);
                        showNotification(data.message || "复制失败", "error");
                    }
                })
                .catch(error => {
                    console.error("Error copying table:", error);
                    document.body.removeChild(modalOverlay);
                    showNotification("复制失败，请稍后重试", "error");
                });
        });
    }

// 生成年份选择选项
    function generateYearOptions(currentYear) {
        let options = '';
        // 去年到未来五年
        for (let year = currentYear - 1; year <= currentYear + 5; year++) {
            options += `<option value="${year}" ${year === currentYear ? 'selected' : ''}>${year}年</option>`;
        }
        return options;
    }

// 显示通知
    function showNotification(message, type) {
        // 检查通知容器是否存在，不存在则创建
        let container = document.querySelector(".notification-container");
        if (!container) {
            container = document.createElement("div");
            container.className = "notification-container";
            document.body.appendChild(container);
        }

        // 创建通知元素
        const notification = document.createElement("div");
        notification.className = `notification ${type}`;
        notification.textContent = message;
        container.appendChild(notification);

        // 3秒后自动消失
        setTimeout(() => {
            notification.classList.add("fade-out");
            setTimeout(() => {
                container.removeChild(notification);
                // 如果容器中没有通知了，移除容器
                if (container.children.length === 0) {
                    document.body.removeChild(container);
                }
            }, 500);
        }, 3000);
    }
});
function getToken() {
    // 从localStorage或sessionStorage获取令牌
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
}
