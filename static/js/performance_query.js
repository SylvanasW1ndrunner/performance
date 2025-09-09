// performance.js

document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();

    // 绑定检索按钮事件
    document.querySelector('.search-button').addEventListener('click', performSearch);

    // 绑定分页按钮事件
    document.querySelectorAll('.page-button').forEach(button => {
        button.addEventListener('click', function() {
            if (!this.classList.contains('active')) {
                const page = this.textContent;
                if (page === '<') {
                    // 前一页
                    const activePage = document.querySelector('.page-button.active');
                    if (activePage && activePage.previousElementSibling &&
                        activePage.previousElementSibling.classList.contains('page-button')) {
                        activePage.previousElementSibling.click();
                    }
                } else if (page === '>') {
                    // 后一页
                    const activePage = document.querySelector('.page-button.active');
                    if (activePage && activePage.nextElementSibling &&
                        activePage.nextElementSibling.classList.contains('page-button')) {
                        activePage.nextElementSibling.click();
                    }
                } else {
                    // 直接跳转到指定页
                    document.querySelectorAll('.page-button').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    this.classList.add('active');
                    loadUserData(parseInt(page));
                }
            }
        });
    });
});

// 获取JWT令牌
function getToken() {
    // 从localStorage或sessionStorage获取令牌
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
}

// 创建带有认证头的请求选项
function createAuthHeaders() {
    const token = getToken();
    return {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    };
}

// 初始化页面
async function initPage() {
    try {
        // 加载当前用户信息
        await loadCurrentUserInfo();

        // 加载筛选条件选项
        await loadFilterOptions();

        // 初始加载用户数据（第1页）
        await loadUserData(1);
    } catch (error) {
        console.error('初始化页面失败:', error);
        showMessage('初始化页面失败，请刷新重试', 'error');
    }
}

// 加载当前用户信息
async function loadCurrentUserInfo() {
    try {
        // 调用后端接口获取当前登录用户信息
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/current_user_info',
            {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        if (!response.ok) {
            throw new Error('获取用户信息失败');
        }

        const userData = await response.json();

        // 更新个人信息卡片
        document.querySelector('.user-basic-info h3').textContent = userData.name;
        document.querySelector('.employee-id').textContent = `工号：${userData.employeeId}`;
        document.querySelector('.department-info span:first-child').textContent = `${userData.team}`;
        document.querySelector('.department-info span:last-child').textContent = userData.position;

        // 更新绩效摘要信息
        document.querySelector('.performance-summary .performance-item:nth-child(1) .value').textContent = userData.directLeader;
        document.querySelector('.performance-summary .performance-item:nth-child(2) .value').textContent = userData.productLine;

        // 更新最近绩效
        const performanceElement = document.querySelector('.performance-summary .performance-item:nth-child(3) .value');
        performanceElement.textContent = userData.recentPerformance || 'N/A';

        // 根据绩效等级设置样式
        performanceElement.className = 'value';
        if (userData.recentPerformance) {
            performanceElement.classList.add(`grade-${userData.recentPerformance.trim().toLowerCase()}`);
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
        showMessage('加载用户信息失败', 'error');
    }
}

// 加载筛选条件选项
async function loadFilterOptions() {
    try {
        // 获取团队列表
        const teamsResponse = await fetch('/api/teams', createAuthHeaders());
        if (!teamsResponse.ok) throw new Error('获取团队列表失败');
        const teams = await teamsResponse.json();

        // 填充团队下拉框
        const teamSelect = document.querySelector('select[name="team"]');
        teamSelect.innerHTML = '<option value="">全部</option>';
        teams.forEach(team => {
            const option = document.createElement('option');
            option.value = team.id;
            option.textContent = team.name;
            teamSelect.appendChild(option);
        });

        // 获取产品线列表
        const productLinesResponse = await fetch('/api/product_lines', createAuthHeaders());
        if (!productLinesResponse.ok) throw new Error('获取产品线列表失败');
        const productLines = await productLinesResponse.json();

        // 填充产品线下拉框
        const productLineSelect = document.querySelector('select[name="productLine"]');
        productLineSelect.innerHTML = '<option value="">全部</option>';
        productLines.forEach(productLine => {
            const option = document.createElement('option');
            option.value = productLine.id;
            option.textContent = productLine.name;
            productLineSelect.appendChild(option);
        });

        // 获取直属领导列表
        const leadersResponse = await fetch('/api/leaders', createAuthHeaders());
        if (!leadersResponse.ok) throw new Error('获取领导列表失败');
        const leaders = await leadersResponse.json();

        // 填充直属领导下拉框
        const leaderSelect = document.querySelector('select[name="directLeader"]');
        leaderSelect.innerHTML = '<option value="">全部</option>';
        leaders.forEach(leader => {
            const option = document.createElement('option');
            option.value = leader.id;
            option.textContent = leader.name;
            leaderSelect.appendChild(option);
        });
    } catch (error) {
        console.error('加载筛选选项失败:', error);
        showMessage('加载筛选选项失败', 'error');
    }
}

// 执行检索
async function performSearch() {
    try {
        // 获取所有筛选条件
        const filters = {
            team: document.querySelector('select[name="team"]').value,
            productLine: document.querySelector('select[name="productLine"]').value,
            directLeader: document.querySelector('select[name="directLeader"]').value,
            name: document.querySelector('input[name="name"]').value.trim(),
            employeeId: document.querySelector('input[name="employeeId"]').value.trim()
        };

        // 存储当前筛选条件到sessionStorage，方便翻页时使用
        sessionStorage.setItem('performanceQueryFilters', JSON.stringify(filters));

        // 重置分页并加载第一页数据
        resetPagination();
        await loadUserData(1, filters);
    } catch (error) {
        console.error('执行检索失败:', error);
        showMessage('执行检索失败', 'error');
    }
}

// 重置分页控件
function resetPagination() {
    const paginationButtons = document.querySelectorAll('.page-button');
    paginationButtons.forEach(button => {
        button.classList.remove('active');
    });

    // 设置第一页为活动页
    const firstPageButton = document.querySelector('.page-button:nth-child(2)');
    if (firstPageButton) {
        firstPageButton.classList.add('active');
    }
}

// 加载用户数据
async function loadUserData(page = 1, filters = null) {
    try {
        // 如果没有传入筛选条件，尝试从sessionStorage获取
        if (!filters) {
            const savedFilters = sessionStorage.getItem('performanceQueryFilters');
            filters = savedFilters ? JSON.parse(savedFilters) : {};
        }

        // 构建请求参数
        const params = new URLSearchParams({
            page: page,
            ...filters
        });

        // 调用后端接口获取用户列表
        const response = await fetch(`/api/users?${params.toString()}`, createAuthHeaders());
        if (!response.ok) {
            throw new Error('获取用户数据失败');
        }

        const result = await response.json();
        const users = result.users;
        const totalPages = result.totalPages;

        // 更新表格数据
        updateUserTable(users);

        // 更新分页控件
        updatePagination(page, totalPages);
    } catch (error) {
        console.error('加载用户数据失败:', error);
        showMessage('加载用户数据失败', 'error');
    }
}

// 更新用户表格
function updateUserTable(users) {
    const tableBody = document.querySelector('.performance-table tbody');
    tableBody.innerHTML = '';

    if (users.length === 0) {
        // 如果没有数据，显示一个提示行
        const emptyRow = document.createElement('tr');
        const emptyCell = document.createElement('td');
        emptyCell.colSpan = 7;
        emptyCell.textContent = '没有找到匹配的用户数据';
        emptyCell.style.textAlign = 'center';
        emptyRow.appendChild(emptyCell);
        tableBody.appendChild(emptyRow);
        return;
    }

    // 添加用户数据行
    users.forEach(user => {
        const row = document.createElement('tr');

        // 创建各列数据
        const columns = [
            user.name,
            user.employeeId,
            user.team,
            user.productLine,
            user.position,
            user.directLeader
        ];

        // 添加数据列
        columns.forEach(text => {
            const cell = document.createElement('td');
            cell.textContent = text;
            row.appendChild(cell);
        });

        // 添加操作列（查看按钮）
        const actionCell = document.createElement('td');
        const viewButton = document.createElement('button');
        viewButton.className = 'view-button';
        viewButton.textContent = '查看';
        viewButton.dataset.userId = user.id;
        viewButton.addEventListener('click', () => viewPerformance(user.id, user.name));
        actionCell.appendChild(viewButton);
        row.appendChild(actionCell);

        tableBody.appendChild(row);
    });
}

// 更新分页控件
function updatePagination(currentPage, totalPages) {
    const pagination = document.querySelector('.pagination');

    // 清除现有的页码按钮（保留前后箭头）
    const pageButtons = pagination.querySelectorAll('.page-button:not(:first-child):not(:last-child)');
    pageButtons.forEach(button => button.remove());

    // 移除省略号
    const ellipsis = pagination.querySelector('span');
    if (ellipsis) ellipsis.remove();

    // 获取前后箭头按钮
    const prevButton = pagination.querySelector('.page-button:first-child');
    const nextButton = pagination.querySelector('.page-button:last-child');

    // 禁用或启用前后箭头
    prevButton.disabled = currentPage <= 1;
    nextButton.disabled = currentPage >= totalPages;

    // 确定要显示的页码范围
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);

    // 调整起始页，确保显示5个页码（如果有足够的页数）
    if (endPage - startPage < 4 && totalPages > 4) {
        startPage = Math.max(1, endPage - 4);
    }

    // 创建页码按钮
    for (let i = startPage; i <= endPage; i++) {
        const pageButton = document.createElement('button');
        pageButton.className = 'page-button';
        pageButton.textContent = i;

        if (i === currentPage) {
            pageButton.classList.add('active');
        }

        pageButton.addEventListener('click', function() {
            if (!this.classList.contains('active')) {
                loadUserData(parseInt(this.textContent));
            }
        });

        // 插入到下一页按钮之前
        pagination.insertBefore(pageButton, nextButton);
    }

    // 如果总页数大于显示的页码范围，添加省略号
    if (endPage < totalPages) {
        const ellipsis = document.createElement('span');
        ellipsis.textContent = '...';
        pagination.insertBefore(ellipsis, nextButton);

        // 添加最后一页按钮
        const lastPageButton = document.createElement('button');
        lastPageButton.className = 'page-button';
        lastPageButton.textContent = totalPages;
        lastPageButton.addEventListener('click', function() {
            loadUserData(totalPages);
        });
        pagination.insertBefore(lastPageButton, nextButton);
    }
}

// 查看绩效详情
async function viewPerformance(userId, userName) {
    try {
        // 首先检查当前用户是否有权限查看该用户的绩效
        const permissionResponse = await fetch(`/api/check_performance_permission?userId=${userId}`, createAuthHeaders());
        if (!permissionResponse.ok) {
            throw new Error('检查权限失败');
        }

        const permissionData = await permissionResponse.json();

        if (!permissionData.hasPermission) {
            showMessage('您没有权限查看此用户的绩效信息', 'error');
            return;
        }

        // 获取该用户已评分的绩效表列表
        const tablesResponse = await fetch(`/api/user_performance_tables?userId=${userId}`, createAuthHeaders());
        if (!tablesResponse.ok) {
            throw new Error('获取绩效表列表失败');
        }

        const tables = await tablesResponse.json();

        if (tables.length === 0) {
            showMessage(`${userName} 暂无绩效评分记录`, 'info');
            return;
        }

        // 创建绩效查看弹窗
        createPerformanceModal(userId, userName, tables, permissionData.permissionLevel);
    } catch (error) {
        console.error('查看绩效失败:', error);
        showMessage('查看绩效失败', 'error');
    }
}

// 创建绩效查看弹窗
async function createPerformanceModal(userId, userName, tables, permissionLevel) {
    // 创建模态框背景
    const modalOverlay = document.createElement('div');
    modalOverlay.className = 'modal-overlay';

    // 创建模态框内容
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';

    // 创建标题
    const modalHeader = document.createElement('div');
    modalHeader.className = 'modal-header';

    const modalTitle = document.createElement('h3');
    modalTitle.textContent = `${userName} 的绩效详情`;

    const closeButton = document.createElement('button');
    closeButton.className = 'close-button';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
    });

    modalHeader.appendChild(modalTitle);
    modalHeader.appendChild(closeButton);

    // 创建表单内容
    const modalBody = document.createElement('div');
    modalBody.className = 'modal-body';

    // 创建表选择下拉框
    const formGroup = document.createElement('div');
    formGroup.className = 'form-group';

    const selectLabel = document.createElement('label');
    selectLabel.textContent = '选择绩效表:';

    const tableSelect = document.createElement('select');
    tableSelect.id = 'performance-table-select';

    tables.forEach(table => {
        const option = document.createElement('option');
        option.value = table.id;
        option.textContent = table.name;
        tableSelect.appendChild(option);
    });

    formGroup.appendChild(selectLabel);
    formGroup.appendChild(tableSelect);

    // 创建绩效结果显示区域
    const resultContainer = document.createElement('div');
    resultContainer.className = 'performance-result';
    resultContainer.innerHTML = '<p>请选择绩效表查看详细结果</p>';

    // 创建按钮区域
    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'button-group';

    const viewButton = document.createElement('button');
    viewButton.className = 'primary-button';
    viewButton.textContent = '查看';
    viewButton.addEventListener('click', async () => {
        const tableId = tableSelect.value;
        if (!tableId) {
            showMessage('请选择绩效表', 'warning');
            return;
        }

        try {
            // 获取绩效详情
            const response = await fetch(`/api/performance_detail?userId=${userId}&tableId=${tableId}`, createAuthHeaders());
            if (!response.ok) {
                throw new Error('获取绩效详情失败');
            }

            const performanceData = await response.json();
            buttonGroup.innerHTML = ''; // 清空按钮区域
            // 重新渲染结果
            console.log("userId:",userId)
            console.log("tableId:",tableId)
            updatePerformanceResult(resultContainer, performanceData, permissionLevel, userId, tableId);
        } catch (error) {
            console.error('获取绩效详情失败:', error);
            showMessage('获取绩效详情失败', 'error');
        }
    });

    buttonGroup.appendChild(viewButton);

    // 组装模态框
    modalBody.appendChild(formGroup);
    modalBody.appendChild(resultContainer);
    modalBody.appendChild(buttonGroup);

    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);

    modalOverlay.appendChild(modalContent);

    // 添加到页面
    document.body.appendChild(modalOverlay);
}

// 更新绩效结果显示
function updatePerformanceResult(container, data, permissionLevel, userId, tableId) {
    // 清空容器
    container.innerHTML = '';

    // 创建结果表格
    const resultTable = document.createElement('table');
    resultTable.className = 'result-table';

    // 创建表头
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    const headers = ['评分类型', '分数'];
    headers.forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    resultTable.appendChild(thead);

    // 创建表体
    const tbody = document.createElement('tbody');

    // 职能评分行
    if (permissionLevel <= 2) { // 超级管理员或直接领导可以看到职能评分
        const functionalRow = document.createElement('tr');

        const typeCell = document.createElement('td');
        typeCell.textContent = '职能评分';

        const scoreCell = document.createElement('td');
        scoreCell.textContent = data.functionalScore.toFixed(1);

        functionalRow.appendChild(typeCell);
        functionalRow.appendChild(scoreCell);
        tbody.appendChild(functionalRow);
    }
    

    // 产品评分行
    const productRow = document.createElement('tr');
    const productTypeCell = document.createElement('td');
    productTypeCell.textContent = '产品评分';

    const productScoreCell = document.createElement('td');
    productScoreCell.textContent = data.productScore.toFixed(1);

    productRow.appendChild(productTypeCell);
    productRow.appendChild(productScoreCell);
    tbody.appendChild(productRow);

    // 考勤评分 
    const attendanceRow = document.createElement('tr');
    const attendanceTypeCell = document.createElement('td');
    attendanceTypeCell.textContent = '考勤评分';

    const attendanceScoreCell = document.createElement('td');
    const attendanceScore = data.attendanceScore || 0
    attendanceScoreCell.textContent = attendanceScore.toFixed(1);

    attendanceRow.appendChild(attendanceTypeCell);
    attendanceRow.appendChild(attendanceScoreCell);
    tbody.appendChild(attendanceRow);

    // 总分行（超级管理员可编辑）
    if (permissionLevel <= 2) {
        const totalRow = document.createElement('tr');
        totalRow.className = 'total-row';

        const totalTypeCell = document.createElement('td');
        totalTypeCell.textContent = '总分';

        const totalScoreCell = document.createElement('td');

        if (permissionLevel === 1) {
            // 超级管理员可编辑总分
            const totalScoreInput = document.createElement('input');
            totalScoreInput.type = 'number';
            totalScoreInput.value = data.totalScore.toFixed(1);
            totalScoreInput.className = 'editable-input';
            totalScoreCell.appendChild(totalScoreInput);
        } else {
            // 其他人只能查看
            totalScoreCell.textContent = data.totalScore.toFixed(1);
        }

        totalRow.appendChild(totalTypeCell);
        totalRow.appendChild(totalScoreCell);
        tbody.appendChild(totalRow);
    }

    resultTable.appendChild(tbody);
    container.appendChild(resultTable);

    // 添加绩效等级（不影响原逻辑）
    if (permissionLevel <= 2 && data.grade) {
        const gradeContainer = document.createElement('div');
        gradeContainer.className = 'grade-container';

        const gradeLabel = document.createElement('span');
        gradeLabel.textContent = '绩效等级: ';

        const gradeValue = document.createElement('span');
        gradeValue.className = `grade-value grade-${data.grade.toLowerCase()}`;
        gradeValue.textContent = data.grade;

        gradeContainer.appendChild(gradeLabel);
        gradeContainer.appendChild(gradeValue);
        container.appendChild(gradeContainer);
    }

    // 超级管理员提供提交修改按钮
    if (permissionLevel === 1) {
        const submitButton = document.createElement('button');
        submitButton.className = 'primary-button';
        submitButton.textContent = '提交修改';

        submitButton.addEventListener('click', async () => {
            const newTotalScore = parseFloat(document.querySelector('.editable-input').value);

            if (isNaN(newTotalScore)) {
                showMessage('请输入有效的总分', 'warning');
                return;
            }
            token = getToken();
            try {
                const response = await fetch('/api/update_performance_score', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        userId: userId,
                        tableId: tableId,
                        totalScore: newTotalScore
                    })
                });

                if (!response.ok) {
                    throw new Error('修改失败');
                }
                showSuccessModal();

            } catch (error) {
                console.error('修改失败:', error);
                showMessage('修改失败', 'error');
            }
        });

        container.appendChild(submitButton);
    }
}



// 显示消息提示
function showMessage(message, type = 'info') {
    // 创建消息元素
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;
    messageElement.textContent = message;

    // 添加到页面
    document.body.appendChild(messageElement);

    // 自动消失
    setTimeout(() => {
        messageElement.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(messageElement);
        }, 500);
    }, 3000);
}

function showSuccessModal() {
    const modalOverlay = document.createElement('div');
    modalOverlay.style.position = 'fixed';
    modalOverlay.style.top = '0';
    modalOverlay.style.left = '0';
    modalOverlay.style.width = '100%';
    modalOverlay.style.height = '100%';
    modalOverlay.style.background = 'rgba(0, 0, 0, 0.5)';
    modalOverlay.style.display = 'flex';
    modalOverlay.style.alignItems = 'center';
    modalOverlay.style.justifyContent = 'center';
    modalOverlay.style.zIndex = '1000';

    const modalContent = document.createElement('div');
    modalContent.style.background = 'white';
    modalContent.style.padding = '20px';
    modalContent.style.borderRadius = '12px';
    modalContent.style.boxShadow = '0px 4px 10px rgba(0, 0, 0, 0.2)';
    modalContent.style.textAlign = 'center';
    modalContent.style.maxWidth = '400px';
    modalContent.style.width = '90%';
    modalContent.style.animation = 'fadeIn 0.3s ease-in-out';

    const modalMessage = document.createElement('p');
    modalMessage.textContent = '总分已成功修改';
    modalMessage.style.fontSize = '18px';
    modalMessage.style.fontWeight = '600';
    modalMessage.style.marginBottom = '20px';
    modalMessage.style.color = '#333';

    const confirmButton = document.createElement('button');
    confirmButton.textContent = '确定';
    confirmButton.style.background = '#007bff';
    confirmButton.style.color = 'white';
    confirmButton.style.padding = '10px 20px';
    confirmButton.style.border = 'none';
    confirmButton.style.borderRadius = '6px';
    confirmButton.style.cursor = 'pointer';
    confirmButton.style.fontSize = '16px';
    confirmButton.style.transition = 'background 0.3s ease-in-out';

    confirmButton.addEventListener('mouseover', () => {
        confirmButton.style.background = '#0056b3';
    });

    confirmButton.addEventListener('mouseout', () => {
        confirmButton.style.background = '#007bff';
    });

    confirmButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
        window.location.href = '/performance_query'; // 返回主界面
    });

    modalContent.appendChild(modalMessage);
    modalContent.appendChild(confirmButton);
    modalOverlay.appendChild(modalContent);
    document.body.appendChild(modalOverlay);
}


