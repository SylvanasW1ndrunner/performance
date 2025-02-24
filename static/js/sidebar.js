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
                e.preventDefault();

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
});