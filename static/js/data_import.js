// 添加导入历史显示函数
async function loadImportHistory() {
    try {
        const response = await fetch('/api/import_history', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        const data = await response.json();
        console.log('API返回的数据:', data);  // 检查API返回的数据
        console.log('历史记录数组:', data.history);  // 检查历史记录数组
        console.log('数组长度:', data.history.length);  // 检查数组长度

        const historyDiv = document.getElementById('importHistory');
        console.log('获取到的DOM元素:', historyDiv);  // 检查DOM元素

        if (data.success && data.history && data.history.length > 0) {
            // 创建文件列表的容器
            const fileList = document.createElement('div');
            fileList.className = 'file-list';

            // 检查每个文件记录
            data.history.forEach((item, index) => {
                console.log(`处理第${index + 1}个文件:`, item);  // 检查循环处理
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.innerHTML = `<span class="filename">${item.filename}</span>`;
                fileList.appendChild(fileItem);
                console.log(`添加文件项到列表:`, fileItem);  // 检查DOM操作
            });

            // 更新 DOM
            historyDiv.innerHTML = '<h4>最近导入的文件：</h4>';
            historyDiv.appendChild(fileList);
            console.log('最终的DOM结构:', historyDiv.innerHTML);  // 检查最终DOM结构
        } else {
            historyDiv.innerHTML = `
                <h4>最近导入的文件：</h4>
                <p>暂无导入记录</p>
            `;
            console.log('无数据显示');  // 检查无数据情况
        }
    } catch (error) {
        console.error('加载导入历史失败:', error);
        console.log('错误详情:', error.message);  // 检查错误详情
    }
}

// 确保函数被调用
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面加载完成，开始获取历史记录');  // 检查函数调用时机
    loadImportHistory();
});

document.getElementById('performanceForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData();
    const files = {
        file1: this.file1.files[0],
        file2: this.file2.files[0],
        file3: this.file3.files[0]
    };

    // 检查是否选择了所有文件
    // if ( files.file1 && !files.file2 && !files.file3 ) {
    //     delete files.file2;
    //     delete files.file3;
    // }
    // else if ( files.file1 && files.file2 && files.file3 ) {
    // }
    // else {
    //     alert('请提交三个表格或仅提交第一张表格');
    //     return;
    // }

    // 添加确认对话框
    if (!confirm('确认要上传这些文件吗？')) {
        return;
    }

    // 添加文件到 FormData
    Object.keys(files).forEach(key => {
        formData.append(key, files[key]);
    });

    try {
        const token = localStorage.getItem('access_token');

        const response = await fetch('/upload_performance', {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 403) {
            alert('权限不足，仅系统管理员可以上传文件');
            return;
        }

        const result = await response.json();

        if (response.ok) {
            alert('文件上传成功！');
        } else {
            alert('上传失败：' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('Error:', error);
        if (error.name === 'SyntaxError') {
            alert('文件上传成功！');
              //如果需要更新表格，可以保留这些调用
             if (result.data) {
                 updateTable(result.data);
                 updateTotalHours(result.data);
             }
        } else {
            alert('上传出错，请重试');
        }
    }
});

// 页面加载时获取导入历史
document.addEventListener('DOMContentLoaded', function() {
    loadImportHistory();
});

function updateTable(data) {
    const tbody = document.getElementById('dataTableBody');
    tbody.innerHTML = '';

    data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.name}</td>
            <td>${item.total_hours.toFixed(2)}</td>
        `;
        tbody.appendChild(row);
    });
}

function updateTotalHours(data) {
    const total = data.reduce((sum, item) => sum + item.total_hours, 0);
    document.getElementById('totalHours').textContent = total.toFixed(2);
}




document.addEventListener('DOMContentLoaded', function() {

    // 获取DOM元素
    const departmentSelect = document.getElementById('departmentSelect');
    const versionSelect = document.getElementById('versionSelect');
    const queryBtn = document.getElementById('queryBtn');
    const exportBtn = document.getElementById('exportBtn');
    const resultSection = document.querySelector('.result-section');


    // 事件监听器
    departmentSelect.addEventListener('change', handleDepartmentChange);
    versionSelect.addEventListener('change', handleVersionChange);
    queryBtn.addEventListener('click', handleQuery);
    exportBtn.addEventListener('click', handleExport);



    // 修改获取用户信息的方式
    let userInfo;
    try {
        const token = localStorage.getItem('access_token');
        if (token) {
            // 解析 JWT token
            const tokenParts = token.split('.');
            const payload = JSON.parse(atob(tokenParts[1]));
            userInfo = JSON.parse(payload.sub);  // 解析嵌套的 JSON 字符串
        }
    } catch (error) {
        console.error('Error parsing user info:', error);
        alert('获取用户信息失败，请重新登录');
        return;
    }

    const isSA = userInfo?.userinfo?.isSA || false;
    const currentUserId = userInfo?.userinfo?.emp_id || '';

    console.log('User Info:', userInfo);  // 调试用
    console.log('Is SA:', isSA);          // 调试用
    console.log('User ID:', currentUserId);// 调试用

    // 初始化
    loadDepartments();

    // 加载部门列表
    async function loadDepartments() {
        try {
            const response = await fetch('/api/departments', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Departments data:', data);  // 调试用

            if (data.success) {
                departmentSelect.innerHTML = '<option value="">请选择部门</option>';

                // 超级管理员可以查看所有部门
                if (isSA) {
                    departmentSelect.innerHTML += '<option value="all">所有部门</option>';
                }

                if (data.departments && Array.isArray(data.departments)) {
                    data.departments.forEach(dept => {
                        // 根据权限显示部门
                        if (isSA || dept.leader_id === currentUserId) {
                            const option = document.createElement('option');
                            option.value = dept.id;
                            option.textContent = dept.name;
                            departmentSelect.appendChild(option);
                        }
                    });

                    // 部门管理员自动选中其部门
                    if (!isSA && departmentSelect.options.length === 2) {
                        departmentSelect.selectedIndex = 1;
                        departmentSelect.dispatchEvent(new Event('change'));
                    }
                } else {
                    console.error('Invalid departments data:', data);
                }
            } else {
                throw new Error(data.message || '加载部门列表失败');
            }
        } catch (error) {
            console.error('Error loading departments:', error);
            alert('加载部门列表失败: ' + error.message);
        }
    }


    // 处理部门选择变化
    async function handleDepartmentChange() {
        const departmentId = departmentSelect.value;
        console.log('选择的部门ID:', departmentId);  // 调试信息

        versionSelect.disabled = !departmentId;
        versionSelect.innerHTML = '<option value="">请选择版本</option>';
        queryBtn.disabled = true;

         // 处理"所有部门"的特殊情况
        if (departmentId === 'all' && isSA) {
            versionSelect.disabled = true;
            versionSelect.innerHTML = '<option value="latest">最新版本</option>';
            versionSelect.value = 'latest';
            queryBtn.disabled = false;
        } else {
            versionSelect.disabled = !departmentId;
            versionSelect.innerHTML = '<option value="">请选择版本</option>';
            queryBtn.disabled = true;

            if (departmentId) {
                try {
                    // ... 原有的版本加载代码 ...
                } catch (error) {
                    console.error('加载版本错误:', error);
                    alert('加载版本列表失败: ' + error.message);
                }
            }
        }

    if (departmentId) {
        try {
            console.log('发送版本请求:', `/api/versions?department=${departmentId}`);  // 调试信息

            const response = await fetch(`/api/versions?department=${departmentId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            console.log('版本请求状态:', response.status);  // 调试信息

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('版本数据:', data);  // 调试信息

            if (data.success && Array.isArray(data.versions)) {
                if (data.versions.length === 0) {
                    console.log('没有找到版本数据');  // 调试信息
                    versionSelect.innerHTML = '<option value="">无可用版本</option>';
                } else {
                    data.versions.forEach(version => {
                        console.log('添加版本选项:', version);  // 调试信息
                        const option = document.createElement('option');
                        option.value = version;
                        option.textContent = version;
                        versionSelect.appendChild(option);
                    });
                }
            } else {
                throw new Error(data.message || '加载版本列表失败');
            }
        } catch (error) {
            console.error('加载版本错误:', error);
            alert('加载版本列表失败: ' + error.message);
        }
    }
}

    // 处理版本选择变化
    function handleVersionChange() {
        queryBtn.disabled = !this.value;
    }

    // 处理查询请求
    async function handleQuery() {
        const departmentId = departmentSelect.value;
        const version = versionSelect.value;

        console.log('查询参数:', {
            departmentId,
            version,
            token: localStorage.getItem('access_token')
        });

        if (!departmentId || !version) {
            alert('请选择部门和版本');
            return;
        }

        try {
            console.log('发送请求到:', `/api/assessments?department=${departmentId}&version=${version}`);

            const response = await fetch(`/api/assessments?department=${departmentId}&version=${version}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                }
            });

            console.log('响应状态:', response.status);

            if (!response.ok) {
                if (response.status === 403) {
                    throw new Error('无权限查看该部门的绩效信息');
                }
                throw new Error(`请求失败: ${response.status}`);
            }

            const data = await response.json();
            console.log('返回数据:', data);

            if (data.success) {
                console.log('准备显示数据:', data.assessments);
                displayAssessments(data.assessments);
                exportBtn.style.display = 'block';
            } else {
                throw new Error(data.message || '查询失败');
            }
        } catch (error) {
            console.error('查询错误详情:', error);
            alert(error.message || '查询失败，请重试');
        }
    }



     function displayAssessments(assessments) {
    console.log('开始处理显示数据');
    const tableBody = document.getElementById('assessmentTableBody');

    if (!assessments || assessments.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center">没有找到匹配的记录</td></tr>';
        resultSection.style.display = 'block';
        return;
    }

    tableBody.innerHTML = '';

    assessments.forEach((deptData, index) => {
        // 添加部门标题行
        const deptRow = document.createElement('tr');
        deptRow.className = 'department-header';

        // 获取统计信息
        let headerText = deptData.department_name;
        if (deptData.assessments && deptData.assessments.stats) {
            // 从正确的数据结构中获取统计信息
            const stats = deptData.assessments.stats;
            headerText += ` AVG（A、B+）: ${stats.avg_grades} 个`;
        }
        deptRow.innerHTML = `<td colspan="7">${headerText}</td>`;
        tableBody.appendChild(deptRow);

        // 获取实际的考核数据
        const assessmentData = deptData.assessments && deptData.assessments.assessments ?
                             deptData.assessments.assessments :
                             (Array.isArray(deptData.assessments) ? deptData.assessments : []);

        // 添加部门数据
        assessmentData.forEach(assessment => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${assessment.emp_id || ''}</td>
                <td>${assessment.emp_name || ''}</td>
                <td>${assessment.totalrank || ''}</td>
                <td>${assessment.totalscore || ''}</td>
                <td>${assessment.checktime || ''}</td>
                <td>${assessment.abiscore || ''}</td>
                <td>${assessment.productscore || ''}</td>
            `;
            tableBody.appendChild(row);
        });
    });

    resultSection.style.display = 'block';
}

    // 处理导出请求
    function handleExport() {
        const table = document.querySelector('.assessment-table');
        const rows = Array.from(table.querySelectorAll('tr'));

        // 准备CSV内容
        let csvContent = '\uFEFF'; // 添加BOM以支持中文

        // 添加表头
        const headers = ['员工ID', '姓名', '总评级', '总分', '评估时间', '职能分数', '产品分数'];
        csvContent += headers.join(',') + '\n';

        // 添加数据行
        let currentDepartment = '';
        rows.forEach(row => {
            if (row.classList.contains('department-header')) {
                currentDepartment = row.textContent;
                csvContent += `\n${currentDepartment}\n`;
            } else {
                const cells = Array.from(row.querySelectorAll('td'));
                if (cells.length === 7) { // 确保是数据行
                    const rowData = cells.map(cell => `"${cell.textContent}"`).join(',');
                    csvContent += rowData + '\n';
                }
            }
        });

        // 创建并下载文件
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        link.href = window.URL.createObjectURL(blob);
        link.download = `绩效评估数据_${timestamp}.csv`;

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});

// 添加导出功能
document.getElementById('exportWorkingRate').addEventListener('click', async function() {
    try {
        const response = await fetch('/api/export_working_rate', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '工时统计详情.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            alert('导出失败，请重试');
        }
    } catch (error) {
        console.error('导出错误:', error);
        alert('导出失败，请重试');
    }
});



