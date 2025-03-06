document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const changePasswordButton = document.getElementById("changePasswordButton");
    const changePasswordModal = document.getElementById("changePasswordModal");
    const changePasswordForm = document.getElementById("changePasswordForm");
    const cancelChangePassword = document.getElementById("cancelChangePassword");
    const messageElement = document.getElementById("message");
    // 登录逻辑
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, password })
            });

            const result = await response.json();
            console.log(result);
            if (response.ok) {
                // 保存 token 到 localStorage
                document.cookie = "access_token_cookie=" + result.access_token + "; path=/;";  // 将 token 存储到 cookie 中

                console.log("Access Token:", result.access_token);

                localStorage.setItem('access_token', result.access_token);

                messageElement.textContent = "登录成功，正在跳转...";
                messageElement.style.color = "green";

                // 跳转页面
                setTimeout(() => {
                    window.location.href = "/performance_query";  // 页面跳转
                }, 1000);
            } else {
                messageElement.textContent = result.error || "登录失败";
                messageElement.style.color = "red";
            }
        } catch (error) {
            console.error("请求错误:", error);
            messageElement.textContent = "服务器错误，请稍后重试";
            messageElement.style.color = "red";
        }
    });

    // 显示修改密码模态框
    changePasswordButton.addEventListener("click", function () {
        changePasswordModal.style.display = "block";
    });

    // 隐藏修改密码模态框
    cancelChangePassword.addEventListener("click", function () {
        changePasswordModal.style.display = "none";
    });

    // 修改密码逻辑
    changePasswordForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const username = document.getElementById("username").value; // 用户名从登录表单获取
        const oldPassword = document.getElementById("oldPassword").value;
        const newPassword = document.getElementById("newPassword").value;

        try {
            const response = await fetch("/api/change_password", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, old_password: oldPassword, new_password: newPassword })
            });

            const result = await response.json();

            if (response.ok) {
                alert("密码修改成功，请重新登录！");
                changePasswordModal.style.display = "none";
            } else {
                alert(result.error || "修改密码失败");
            }
        } catch (error) {
            console.error("请求错误:", error);
            alert("服务器错误，请稍后重试");
        }
    });
});
