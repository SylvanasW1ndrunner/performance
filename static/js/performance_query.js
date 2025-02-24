
// 搜索功能初始化和控制
function initializeSearch() {
    const searchButton = document.querySelector('.search-button');
    if (searchButton) {
        searchButton.addEventListener('click', performSearch);
    }
}

// 执行搜索
function performSearch() {
    // 获取所有搜索条件
    const department = document.querySelector('select[name="department"]').value;
    const directLeader = document.querySelector('select[name="directLeader"]').value;
    const topLeader = document.querySelector('select[name="topLeader"]').value;
    const name = document.querySelector('input[name="name"]').value;
    const employeeId = document.querySelector('input[name="employeeId"]').value;

    // 构建搜索参数
    const searchParams = {
        department,
        directLeader,
        topLeader,
        name,
        employeeId
    };

    // 发送搜索请求
    fetchSearchResults(searchParams);
}

// 获取搜索结果
async function fetchSearchResults(params) {
    try {
        const response = await fetch('/api/search-performance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });

        if (response.ok) {
            const data = await response.json();
            updateTableContent(data);
        } else {
            console.error('搜索请求失败');
        }
    } catch (error) {
        console.error('搜索出错：', error);
    }
}

// 更新表格内容
function updateTableContent(data) {
    const tbody = document.querySelector('.performance-table tbody');
    tbody.innerHTML = '';

    data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.name}</td>
            <td>${item.employeeId}</td>
            <td>${item.department}</td>
            <td>${item.position}</td>
            <td>${item.directLeader}</td>
            <td>${item.topLeader}</td>
            <td><button class="view-button" onclick="viewPerformance('${item.employeeId}')">查看</button></td>
        `;
        tbody.appendChild(row);
    });
}

// 分页控制初始化
// 修改侧边栏初始化函数

// 加载分页数据
async function loadPageData(page) {
    try {
        const response = await fetch(`/api/performance-data?page=${page}`);
        if (response.ok) {
            const data = await response.json();
            updateTableContent(data);
        }
    } catch (error) {
        console.error('加载分页数据失败：', error);
    }
}

// 查看绩效详情
function viewPerformance(employeeId) {
    // 根据权限检查和处理绩效详情查看
    window.location.href = `/performance-detail/${employeeId}`;
}