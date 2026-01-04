# 服务端部署与 Nginx 代理配置文档 (终极修复版)

为了解决“定位到服务器”以及“跨域被拦截”的问题，必须配置以下 Nginx 逻辑。

## 1. Nginx 核心配置

请在你的 Nginx `server` 块中添加/覆盖以下三个关键位置：

```nginx
server {
    listen 443 ssl;
    server_name gallery.liruochen.cn;

    # --- A. 静态资源 ---
    location /i-wanna-be-a-judge/ {
        alias /var/www/i-wanna-be-a-judge/dist/;
        index index.html;
        try_files $uri $uri/ /i-wanna-be-a-judge/index.html;
    }

    # --- B. 【核心】获取访问者真实 IP ---
    # 这个配置会让服务器直接把访问者的 IP 返回给前端，不经过任何三方转发
    location /i-wanna-be-a-judge/get-my-ip {
        default_type text/plain;
        return 200 $remote_addr; 
    }

    # --- C. 定位接口代理 ---
    location /i-wanna-be-a-judge/api-mapchaxun/ {
        proxy_pass https://www.mapchaxun.cn/;
        proxy_set_header Referer "https://www.mapchaxun.cn/Regeo";
        proxy_set_header Origin "https://www.mapchaxun.cn";
        proxy_set_header Host "www.mapchaxun.cn";
        proxy_ssl_server_name on;
    }
}
```

## 2. 为什么这样能行？

1.  **get-my-ip**: 当你的浏览器访问这个路径时，Nginx 会直接读取你的连接 IP（`$remote_addr`）并返回。因为是同域名，**没有 CORS 跨域问题**，且获取到的是**绝对真实的用户公网 IP**。
2.  **api-mapchaxun**: 前端拿到 IP 后，通过这个代理传给定位网站。由于我们在 Body 里传了明确的 `ip` 参数，定位网站就不会再去识别服务器的 IP 了。

## 3. 操作清单

1.  **本地执行**：`npm run build`。
2.  **上传代码**：更新服务器上的 `dist` 内容。
3.  **修改 Nginx**：确保添加了上面的 `get-my-ip` 配置。
4.  **重载 Nginx**：`sudo nginx -s reload`。
