document.addEventListener("DOMContentLoaded", function () {
    const changePasswordForm = document.getElementById("changePasswordForm");
    const messageElement = document.getElementById("message");

    changePasswordForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const username = document.getElementById("username").value;
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
                window.location.href = "/"; // 跳转回登录页面
            } else {
                messageElement.textContent = result.error || "修改密码失败";
                messageElement.style.color = "red";
            }
        } catch (error) {
            console.error("请求错误:", error);
            messageElement.textContent = "服务器错误，请稍后重试";
            messageElement.style.color = "red";
        }
    });
});