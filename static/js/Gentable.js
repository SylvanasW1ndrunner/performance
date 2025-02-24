
// 考核表相关功能
document.querySelector('.add-criteria')?.addEventListener('click', function() {
    const newItem = document.createElement('div');
    newItem.className = 'criteria-item';
    newItem.innerHTML = `
        <span>新评分项</span>
        <span class="remove">×</span>
    `;
    this.parentNode.insertBefore(newItem, this);
});

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('remove')) {
        e.target.parentNode.remove();
    }
});

document.getElementById('submitForm')?.addEventListener('click', async function() {
    // 收集表单数据
    const formData = {
        title: document.querySelector('.search-input')?.value,
        evaluationPeriod: document.querySelector('.date-input')?.value,
        criteria: Array.from(document.querySelectorAll('.criteria-item')).map(item => ({
            name: item.querySelector('span').textContent
        })),
        grades: {
            A: document.querySelector('.grade-pair:nth-child(1) .grade-input')?.value,
            'B+': document.querySelector('.grade-pair:nth-child(2) .grade-input')?.value,
            B: document.querySelector('.grade-pair:nth-child(3) .grade-input')?.value,
            C: document.querySelector('.grade-pair:nth-child(4) .grade-input')?.value
        },
        attendanceRules: Array.from(document.querySelectorAll('.score-item')).map(item => ({
            rule: item.querySelector('.score-label').textContent,
            score: item.querySelector('.score-input').value
        })),
        forcedDistribution: document.querySelector('.switch input')?.checked
    };

    try {
        const response = await fetch('/api/submit-evaluation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('考核表提交成功！');
        } else {
            alert('提交失败，请重试');
        }
    } catch (error) {
        console.error('提交出错：', error);
        alert('提交出错，请检查网络连接后重试');
    }
});