/**
 * 获取所有部门并填充下拉框
 */

document.addEventListener("DOMContentLoaded", function() {
    const yearSelect = document.getElementById('year-select');
    const quarterSelect = document.getElementById('quarter-select');
    const monthSelect = document.getElementById('month-select');

    const currentYear = new Date().getFullYear();
    const numberOfYears = 5; // 生成未来 5 年的选项

    // 动态生成年份选项
    for (let year = currentYear - 1; year < currentYear + numberOfYears; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }

    // 生成季度选项
    const quarters = ['Q1', 'Q2', 'Q3', 'Q4'];
    quarters.forEach(quarter => {
        const option = document.createElement('option');
        option.value = quarter;
        option.textContent = quarter;
        quarterSelect.appendChild(option);
    });

    // 生成月份选项
    const months = ['M1', 'M2', 'M3', '--'];
    months.forEach(month => {
        const option = document.createElement('option');
        option.value = month;
        option.textContent = month;
        monthSelect.appendChild(option);
    });

    // 监听年份选择变化
    yearSelect.addEventListener('change', function() {
        const selectedYear = yearSelect.value;
        const selectedQuarter = quarterSelect.value;
        const selectedMonth = monthSelect.value;
        console.log(`选择的年份：${selectedYear}，季度：${selectedQuarter}，月份：${selectedMonth}`);
    });

    // 监听季度选择变化
    quarterSelect.addEventListener('change', function() {
        const selectedYear = yearSelect.value;
        const selectedQuarter = quarterSelect.value;
        const selectedMonth = monthSelect.value;
        console.log(`选择的年份：${selectedYear}，季度：${selectedQuarter}，月份：${selectedMonth}`);
    });

    // 监听月份选择变化
    monthSelect.addEventListener('change', function() {
        const selectedYear = yearSelect.value;
        const selectedQuarter = quarterSelect.value;
        const selectedMonth = monthSelect.value;
        console.log(`选择的年份：${selectedYear}，季度：${selectedQuarter}，月份：${selectedMonth}`);
    });
});



 function getToken() {
    // 从localStorage或sessionStorage获取令牌
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
}

function loadDepartments() {
    // 显示加载状态
    const departmentSelect = document.getElementById('department-select');
    departmentSelect.innerHTML = '';
    departmentSelect.disabled = true;
    token = getToken();
    // 发起AJAX请求获取部门数据
    fetch('/showalldepartment',
        {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            // 检查响应状态
            if (!response.ok) {
                throw new Error('网络响应不正常，状态码: ' + response.status);
            }
            console.log(response.json)
            return response.json();
        })
        .then(data => {
            // 清空下拉框
            departmentSelect.innerHTML = '<option value="">请选择部门</option>';

            // 检查返回的数据格式并填充下拉框
            if (Array.isArray(data)) {
                // 假设返回的是数组格式
                data.forEach(department => {
                    const option = document.createElement('option');
                    option.value = department.id;
                    option.textContent = department.name;
                    departmentSelect.appendChild(option);
                });
            } else if (data.data && Array.isArray(data.data)) {
                // 假设返回的是 {data: [...]} 格式
                data.data.forEach(department => {
                    const option = document.createElement('option');
                    option.value = department.id;
                    option.textContent = department.name;
                    departmentSelect.appendChild(option);
                });
            } else {
                throw new Error('返回的数据格式不正确');
            }

            // 启用下拉框
            departmentSelect.disabled = false;

            // 如果下拉框为空，显示提示信息
            if (departmentSelect.options.length <= 1) {
                departmentSelect.innerHTML = '<option value="">暂无部门数据</option>';
            }
        })
        .catch(error => {
            console.error('获取部门数据失败:', error);
            departmentSelect.innerHTML = '<option value="">加载失败，请重试</option>';
            departmentSelect.disabled = false;

            // 可选：显示错误提示
            alert('获取部门数据失败: ' + error.message);
        });
}

// 页面加载完成后自动加载部门数据
document.addEventListener('DOMContentLoaded', loadDepartments);

// 为下拉框添加变更事件监听器（可选）
document.getElementById('department-select').addEventListener('change', function() {
    const selectedDepartmentId = this.value;
    const selectedDepartmentName = this.options[this.selectedIndex].text;

    if (selectedDepartmentId) {
        console.log('已选择部门:', selectedDepartmentId, selectedDepartmentName);
        // 这里可以添加选择部门后的其他操作
        // 例如加载该部门的员工列表等
    }
});

document.querySelectorAll('.dimension-score-display').forEach(scoreElement => {
    scoreElement.addEventListener('click', handleDimensionScoreClick);
});

// 维度分数点击事件处理函数
function handleDimensionScoreClick() {
    const currentValue = parseInt(this.textContent) || 0;
    const inputElement = document.createElement('input');
    inputElement.type = 'number';
    inputElement.min = 0;
    // 可以根据需要设置最大值，比如10分制或100分制
    inputElement.value = currentValue;
    inputElement.classList.add('dimension-score-input');

    // 替换文本为输入框
    this.parentNode.replaceChild(inputElement, this);
    inputElement.focus();

    // 失去焦点时保存内容并恢复为文本显示
    inputElement.addEventListener('blur', function() {
        const newScore = document.createElement('span');
        newScore.classList.add('dimension-score-display');
        newScore.textContent = this.value || 0;
        newScore.title = '点击编辑';
        this.parentNode.replaceChild(newScore, this);

        // 重新添加点击事件
        newScore.addEventListener('click', handleDimensionScoreClick);
    });

    // 按下回车键也保存内容
    inputElement.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            this.blur();
        }
    });
}

// 为每个维度添加评级/打分模式选择功能
// document.querySelectorAll('.dimension-section').forEach(section => {
//     // 获取该维度的标题区域
//     const dimensionTitle = section.querySelector('.dimension-title');
//
//     // 如果标题存在且还没有添加下拉框
//     if (dimensionTitle && !section.querySelector('.evaluation-mode-select')) {
//         // 创建下拉框
//         const modeSelect = document.createElement('select');
//         modeSelect.classList.add('evaluation-mode-select');
//
//         // 添加选项
//         modeSelect.innerHTML = `
//             <option value="rating">评级</option>
//             <option value="scoring">打分</option>
//         `;
//
//         // 将下拉框插入到标题后面
//         dimensionTitle.parentNode.insertBefore(modeSelect, dimensionTitle.nextSibling);
//     }
// });

// 修改添加评分项的功能，根据所选模式创建不同的评分项
document.querySelectorAll('.add-criteria').forEach(button => {
    button.addEventListener('click', function() {
        // 获取当前维度区域
        const dimensionSection = this.closest('.dimension-section');

        // 获取评级/打分模式
        const modeSelect = dimensionSection.querySelector('.evaluation-mode-select');
        const mode = modeSelect ? modeSelect.value : 'rating'; // 默认为评级模式

        // 创建新的评分项
        const newItem = document.createElement("div");
        newItem.classList.add("criteria-item", "cursor-hover");

        // 根据模式设置不同的HTML内容
        if (mode === 'rating') {
            newItem.innerHTML = `
        <span class="criteria-text pointer-hover" title="点击编辑">新评分项</span>
        <span class="remove pointer-hover" title="删除此评分项">✖</span>
        <div class="criteria-detail-container">
            <textarea class="criteria-detail" placeholder="请输入详细信息..." rows="2"></textarea>
            <div class="more-detail-container">
                <span class="more-detail-icon pointer-hover" title="更多详细说明">
                    <i class="fas fa-info-circle"></i>📝
                </span>
            <!-- 在创建气泡编辑器的HTML代码中确保箭头正确放置 -->
            <div class="bubble-editor" style="display: none;">
                <div class="bubble-arrow arrow-left"></div>
                <div class="bubble-editor-header">
                    <span>详细说明</span>
                    <span class="close-bubble pointer-hover">✖</span>
                </div>
                <textarea class="more-detail-content" placeholder="请输入更多详细说明..." rows="8"></textarea>
            </div>
            </div>
        </div>
    `;
        } else {
            newItem.innerHTML = `
        <span class="criteria-text pointer-hover" title="点击编辑">新评分项</span>
        <span class="score-value-container">
            <span class="score-value-display" title="点击编辑">0</span>分
        </span>
        <span class="remove pointer-hover" title="删除此评分项">✖</span>
        <div class="criteria-detail-container">
            <textarea class="criteria-detail" placeholder="请输入详细信息..." rows="2"></textarea>
            <div class="more-detail-container">
                <span class="more-detail-icon pointer-hover" title="更多详细说明">
                    <i class="fas fa-info-circle"></i>📝
                </span>
                <!-- 在创建气泡编辑器的HTML代码中确保箭头正确放置 -->
                <div class="bubble-editor" style="display: none;">
                    <div class="bubble-arrow arrow-left"></div>
                    <div class="bubble-editor-header">
                        <span>详细说明</span>
                        <span class="close-bubble pointer-hover">✖</span>
                    </div>
                    <textarea class="more-detail-content" placeholder="请输入更多详细说明..." rows="8"></textarea>
                </div>
            </div>
        </div>
    `;
        }

        // 在添加按钮前插入新评分项
        this.parentNode.insertBefore(newItem, this);

        // 给评分项文本添加点击编辑功能
        const criteriaText = newItem.querySelector('.criteria-text');
        criteriaText.addEventListener('click', function () {
            this.contentEditable = true;
            this.focus(); // 让元素进入编辑模式

            // 监听键盘事件
            this.addEventListener(
                'keydown',
                function (e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        // 按下 Enter 结束编辑
                        e.preventDefault();
                        this.blur();
                    }
                    if (e.key === 'Enter' && e.shiftKey) {
                        // Shift + Enter 插入换行
                        e.preventDefault();
                        document.execCommand('insertLineBreak'); // 兼容性较好
                    }
                },
                { once: true }
            );

            // 失去焦点时停止编辑
            this.addEventListener(
                'blur',
                function () {
                    this.contentEditable = false;
                },
                { once: true }
            );
        });

        const detailToggle = newItem.querySelector('.detail-toggle');
        const detailContainer = newItem.querySelector('.criteria-detail-container');
        detailContainer.style.display = 'block';

        if (detailToggle) {
            detailToggle.addEventListener('click', function() {
                if (detailContainer.style.display === 'none' || !detailContainer.style.display) {
                    detailContainer.style.display = 'block';
                    this.textContent = '收起';
                    // 自动聚焦到文本框
                    newItem.querySelector('.criteria-detail').focus();
                } else {
                    detailContainer.style.display = 'none';
                    this.textContent = '详细';
                }
            });
        }

        // 给删除按钮添加功能 - 删除整个评分项
        const removeBtn = newItem.querySelector('.remove');
        removeBtn.addEventListener('click', function() {
            // 直接删除整个评分项元素
            newItem.remove();
        });

        // 根据模式添加不同的编辑功能
        if (mode === 'rating') {
            // 评级模式：给百分比添加点击编辑功能
            const percentageDisplay = newItem.querySelector('.percentage-display');
            if (percentageDisplay) {
                percentageDisplay.addEventListener('click', function() {
                    this.contentEditable = true;
                    this.focus();

                    // 选中所有文本
                    const range = document.createRange();
                    range.selectNodeContents(this);
                    const selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range);

                    // 失去焦点时停止编辑并格式化
                    this.addEventListener('blur', function() {
                        this.contentEditable = false;
                        // 确保是有效的数字并添加%符号
                        let value = parseInt(this.textContent) || 0;
                        if (value > 100) value = 100;
                        if (value < 0) value = 0;
                        this.textContent = value + '%';
                    }, { once: true });

                    // 按下回车键也停止编辑
                    this.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            this.blur();
                        }
                    });
                });
            }
        } else {
            // 打分模式：给分值添加点击编辑功能
            const scoreValueDisplay = newItem.querySelector('.score-value-display');
            if (scoreValueDisplay) {
                scoreValueDisplay.addEventListener('click', function() {
                    this.contentEditable = true;
                    this.focus();

                    // 选中所有文本
                    const range = document.createRange();
                    range.selectNodeContents(this);
                    const selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range);

                    // 失去焦点时停止编辑并格式化
                    this.addEventListener('blur', function() {
                        this.contentEditable = false;
                        // 确保是有效的数字
                        let value = parseInt(this.textContent) || 0;
                        if (value < 0) value = 0;
                        this.textContent = value;
                    }, { once: true });

                    // 按下回车键也停止编辑
                    this.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            this.blur();
                        }
                    });
                });
            }
        }

        // 添加气泡编辑器的功能
        setupBubbleEditor(newItem);
    });
});

// 设置气泡编辑器功能
// 设置气泡编辑器功能
function setupBubbleEditor(criteriaItem) {
    const moreDetailIcon = criteriaItem.querySelector('.more-detail-icon');
    const bubbleEditor = criteriaItem.querySelector('.bubble-editor');
    const closeBubble = criteriaItem.querySelector('.close-bubble');
    const moreDetailContent = criteriaItem.querySelector('.more-detail-content');

    // 点击图标显示气泡编辑器
    moreDetailIcon.addEventListener('click', function(e) {
        e.stopPropagation(); // 阻止事件冒泡

        // 获取图标的位置信息
        const rect = moreDetailIcon.getBoundingClientRect();

        // 计算相对于父元素的位置
        const criteriaRect = criteriaItem.getBoundingClientRect();

        // 设置位置 - 简化定位逻辑
        // 1. 垂直位置：与图标顶部对齐
        const topPosition = rect.top - criteriaRect.top - 187;

        // 2. 水平位置：图标右侧加上偏移量
        const leftPosition = (rect.right - criteriaRect.left + 20);

        // 应用位置
        bubbleEditor.style.position = 'absolute';
        bubbleEditor.style.top = topPosition + 'px';
        bubbleEditor.style.left = leftPosition + 'px';
        bubbleEditor.style.zIndex = '1000';
        bubbleEditor.style.display = 'block';

        // 设置文本框样式并确保内边距
        moreDetailContent.style.width = 'calc(100% - 30px)';
        moreDetailContent.style.margin = '15px';
        moreDetailContent.style.marginBottom = '25px';
        moreDetailContent.style.resize = 'vertical';
        moreDetailContent.style.minHeight = '150px';
        moreDetailContent.focus();

        // 监听文本框尺寸变化，同步调整气泡编辑器大小
        const resizeObserver = new ResizeObserver(() => {
            const textAreaHeight = moreDetailContent.offsetHeight;
            const textAreaWidth = moreDetailContent.offsetWidth;
            const headerHeight = bubbleEditor.querySelector('.bubble-editor-header').offsetHeight;
            const horizontalPadding = 30;
            const verticalPadding = 30 + headerHeight + 25;

            // 设置气泡编辑器的尺寸，确保同步缩放
            bubbleEditor.style.width = (textAreaWidth + horizontalPadding) + 'px';
            bubbleEditor.style.height = (textAreaHeight + verticalPadding) + 'px';
        });

        // 手动触发一次调整以确保初始大小正确
        setTimeout(() => {
            resizeObserver.observe(moreDetailContent);

            // 手动触发一次调整
            const textAreaHeight = moreDetailContent.offsetHeight;
            const textAreaWidth = moreDetailContent.offsetWidth;
            const headerHeight = bubbleEditor.querySelector('.bubble-editor-header').offsetHeight;
            const horizontalPadding = 30;
            const verticalPadding = 30 + headerHeight + 25;

            bubbleEditor.style.width = (textAreaWidth + horizontalPadding) + 'px';
            bubbleEditor.style.height = (textAreaHeight + verticalPadding) + 'px';

            // 确保在视窗内
            const bubbleRect = bubbleEditor.getBoundingClientRect();
            const arrow = bubbleEditor.querySelector('.bubble-arrow');

            // 如果超出右边界
            if (bubbleRect.right > window.innerWidth - 20) {
                // 尝试放在左侧
                bubbleEditor.style.left = 'auto';
                bubbleEditor.style.right = (window.innerWidth - rect.left + 15) + 'px';

                // 调整箭头
                if (arrow) {
                    arrow.classList.remove('arrow-left');
                    arrow.classList.add('arrow-right');
                }
            }

            // 如果超出底部
            if (bubbleRect.bottom > window.innerHeight - 20) {
                const overflow = bubbleRect.bottom - window.innerHeight + 30;
                bubbleEditor.style.top = (parseFloat(bubbleEditor.style.top) - overflow) + 'px';
            }

            // 如果超出顶部
            if (bubbleRect.top < 20) {
                bubbleEditor.style.top = (parseFloat(bubbleEditor.style.top) + (20 - bubbleRect.top)) + 'px';
            }
        }, 10);

        // 添加点击外部关闭气泡的事件
        document.addEventListener('click', closeOnClickOutside);

        // 存储 ResizeObserver，以便在关闭时断开连接
        bubbleEditor._resizeObserver = resizeObserver;
    });

    // 其余代码保持不变...
    // 添加文本框内容变化事件 - 自动保存
    moreDetailContent.addEventListener('input', function() {
        // 自动保存逻辑
        moreDetailIcon.setAttribute('data-content', moreDetailContent.value);
        if (moreDetailContent.value.trim()) {
            moreDetailIcon.classList.add('has-content');
            moreDetailIcon.style.color = '#2196F3';
        } else {
            moreDetailIcon.classList.remove('has-content');
            moreDetailIcon.style.color = '';
        }
    });

    // 关闭气泡
    function closeBubbleEditor() {
        // 断开 ResizeObserver 连接
        if (bubbleEditor._resizeObserver) {
            bubbleEditor._resizeObserver.disconnect();
            bubbleEditor._resizeObserver = null;
        }

        bubbleEditor.style.display = 'none';
        document.removeEventListener('click', closeOnClickOutside);
    }

    // 点击气泡外部关闭气泡
    function closeOnClickOutside(e) {
        if (!bubbleEditor.contains(e.target) && e.target !== moreDetailIcon) {
            closeBubbleEditor();
        }
    }

    // 关闭按钮事件
    closeBubble.addEventListener('click', function() {
        closeBubbleEditor();
    });
}

// 监听模式选择变化，可以选择是否清空现有评分项
document.addEventListener('change', function(e) {
    if (e.target.classList.contains('evaluation-mode-select')) {
        const dimensionSection = e.target.closest('.dimension-section');
        const criteriaList = dimensionSection.querySelector('.criteria-list');
        const mode = e.target.value;

        // 可选：询问用户是否要清空现有评分项
        if (confirm('切换评分模式会清空现有评分项，是否继续？')) {
            // 清空现有评分项，只保留添加按钮
            const addButton = criteriaList.querySelector('.add-criteria');
            criteriaList.innerHTML = '';
            criteriaList.appendChild(addButton);
        }
    }
});

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('remove')) {
        e.target.parentNode.remove();
    }
});

document.getElementById('submitForm')?.addEventListener('click', async function() {
    // 收集表单数据
    const departmentSelect = document.getElementById('department-select');
    const departmentname = departmentSelect.options[departmentSelect.selectedIndex].text;
    const year = document.querySelector('#year-select')?.value;
    const quarter = document.querySelector('#quarter-select')?.value;
    const month = document.querySelector('#month-select')?.value;

// 组装 title
    const title = `${departmentname}${year}年 ${quarter}-${month}`;

// 计算 evaluationPeriod（当前日期加 15 天）
    const currentDate = new Date();
    const futureDate = new Date();
    futureDate.setDate(currentDate.getDate() + 15);

// 格式化日期为 YYYY-MM-DD
    const evaluationPeriod = futureDate.toISOString().split('T')[0];
    const formData = {
        title: title,
        evaluationPeriod: evaluationPeriod,
        departmentId: (() => {
            const departmentSelect = document.getElementById('department-select');

            // 检查元素是否存在
            if (!departmentSelect) {
                console.error('找不到ID为department-select的下拉框');
                // 尝试使用其他选择器
                const altSelect = document.querySelector('.department-select-container select');
                if (!altSelect) {
                    console.error('无法通过任何方式找到部门下拉框');
                    return null;
                }
                return altSelect.value || null;
            }

            // 检查是否有选中的值
            if (!departmentSelect.value) {
                console.warn('未选择部门，表单提交可能会失败');
                return null;
            }

            return departmentSelect.value;
        })(),
        // 重组评分项为新的description格式
        description: (() => {
            // 创建结果对象
            const result = {
                "专业职能": {
                    "分数": 0,
                    "评分方式": "评级", // 默认为评级方式
                    "评分项": []
                },
                "通用职能": {
                    "分数": 0,
                    "评分项": []
                },
                "产品表现": {
                    "分数": 0
                }
            };

            // 遍历所有维度区域
            document.querySelectorAll('.dimension-section').forEach(section => {
                // 获取维度标题和分数
                const dimensionTitle = section.querySelector('.dimension-title')?.textContent?.trim();
                const dimensionScore = section.querySelector('.dimension-score-display')?.textContent;

                // 根据维度标题选择对应的对象
                let targetObj;
                if (dimensionTitle === "专业职能") {
                    targetObj = result["专业职能"];

                    // 获取专业职能的评分方式
                    const modeSelect = section.querySelector('.evaluation-mode-select');
                    if (modeSelect) {
                        targetObj["评分方式"] = modeSelect.value === "scoring" ? "打分" : "评级";
                    }

                } else if (dimensionTitle === "通用职能") {
                    targetObj = result["通用职能"];
                } else if (dimensionTitle === "产品表现" || dimensionTitle === "项目表现" || dimensionTitle === "产品/项目表现") {
                    targetObj = result["产品表现"];
                } else {
                    return; // 如果不是预期的维度，跳过
                }

                // 设置分数
                targetObj["分数"] = parseFloat(dimensionScore) || 0;

                // 只有专业职能和通用职能需要处理评分项
                if (dimensionTitle === "专业职能" || dimensionTitle === "通用职能") {
                    // 获取该维度下的所有评分项
                    const criteriaItems = section.querySelectorAll('.criteria-list .criteria-item');

                    criteriaItems.forEach(item => {
                        const itemText = item.querySelector('.criteria-text')?.textContent?.trim();

                        if (itemText) {
                            // 创建包含评分项的对象
                            const criteriaObj = {};

                            // 根据维度和评分方式获取不同的值
                            if (dimensionTitle === "专业职能" && targetObj["评分方式"] === "打分") {
                                // 打分模式：获取分数值
                                const scoreValue = item.querySelector('.score-value-display')?.textContent;

                                // 获取气泡文本框中的内容
                                const moreDetailIcon = item.querySelector('.more-detail-icon');
                                const detailContent = moreDetailIcon?.getAttribute('data-content') || '';

                                criteriaObj[itemText] = {
                                    "分数": parseInt(scoreValue) || 0,
                                    "描述": item.querySelector('.criteria-detail')?.value?.trim(),
                                    "详细": detailContent  // 新增加的键值对
                                }
                            } else {
                                // 评级模式：获取百分比
                                const percentageText = item.querySelector('.percentage-display')?.textContent;

                                // 获取气泡文本框中的内容
                                const moreDetailIcon = item.querySelector('.more-detail-icon');
                                const detailContent = moreDetailIcon?.getAttribute('data-content') || '';

                                criteriaObj[itemText] = {
                                    "分数": parseInt(percentageText) || 0,
                                    "描述": item.querySelector('.criteria-detail')?.value?.trim(),
                                    "详细": detailContent  // 新增加的键值对
                                }
                            }

                            targetObj["评分项"].push(criteriaObj);
                        }
                    });
                }
            });

            return result;
        })(),

        grades: Array.from(document.querySelectorAll('.grade-pair')).map(pair => {
            const grade = pair.querySelector('span')?.textContent.trim(); // 获取等级名称
            const value = pair.querySelector('.grade-input')?.value; // 获取分数值
            return { "grade": grade, "value": value }; // 返回对象形式
        }),

        attendanceRules: Array.from(document.querySelectorAll('.score-item')).map(item => ({
            rule: item.querySelector('span')?.textContent.trim(),
            score: item.querySelector('.score-input')?.value
        })),

        forcedDistributionPercentage: 0
    };
    try {
        const response = await fetch('/api/submit_evaluation', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json(); // 解析 JSON 数据

        if (response.ok) {
            alert('考核表提交成功！');
            window.location.href = "/table_index";
        } else {
            alert('提交失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('提交出错：', error);
        alert('提交出错，请检查网络连接后重试');
    }
});
