document.addEventListener('DOMContentLoaded', function() {
    // 获取当前页面URL路径
    const currentPath = window.location.pathname;

    // 处理主菜单项点击
    document.querySelectorAll('.menu-item > a').forEach(item => {
        item.addEventListener('click', (e) => {
            const parent = item.parentElement;
            const submenu = parent.querySelector('.submenu');

            // 只有当有子菜单时才阻止默认行为
            if (submenu) {

                // 移除所有主菜单active类
                document.querySelectorAll('.menu-item > a').forEach(a => {
                    a.classList.remove('active');
                });

                // 为当前点击项添加active类
                item.classList.add('active');

                // 处理子菜单显示/隐藏
                document.querySelectorAll('.submenu').forEach(sub => {
                    if (sub !== submenu) {
                        sub.style.display = 'none';
                    }
                });
                submenu.style.display = submenu.style.display === 'block' ? 'none' : 'block';
            }
        });
    });

    // 处理子菜单项点击
    document.querySelectorAll('.submenu a').forEach(item => {
        item.addEventListener('click', () => {
            // 不阻止默认行为，允许跳转

            // 移除所有子菜单项的active类
            document.querySelectorAll('.submenu a').forEach(a => {
                a.classList.remove('active');
            });

            // 为当前点击项添加active类
            item.classList.add('active');

            // 确保父菜单项保持active状态
            const parentMenuItem = item.closest('.menu-item').querySelector('> a');
            document.querySelectorAll('.menu-item > a').forEach(a => {
                a.classList.remove('active');
            });
            parentMenuItem.classList.add('active');
        });

        // 根据当前URL设置初始active状态
        if(item.getAttribute('href') === currentPath) {
            item.classList.add('active');
            const parentMenuItem = item.closest('.menu-item').querySelector('> a');
            parentMenuItem.classList.add('active');
            item.closest('.submenu').style.display = 'block';
        }
    });

    // 处理登出按钮点击
    const logoutButton = document.querySelector('.logout-btn');
    if (logoutButton) {
        logoutButton.addEventListener('click', (e) => {
            e.preventDefault();  // 防止默认行为

            // 发送 POST 请求调用后端的登出接口
            fetch('api/logout', {
                method: 'GET',  // 使用 POST 请求
                headers: {
                    'Content-Type': 'application/json'
                }
            })
                .then(response => {
                    if (response.ok) {
                        // 如果登出请求成功，后端会重定向
                        // 浏览器会自动处理重定向，因此无需额外操作
                        window.location.href = response.url;  // 重定向到后端提供的 URL
                    } else {
                        // 如果登出失败，做出相应处理
                        alert('登出失败，请重试！');
                    }
                })
                .catch(error => {
                    console.error('Error during logout:', error);
                    alert('登出失败，请重试！');
                });
        });
    }
});
