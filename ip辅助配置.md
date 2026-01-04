# 服务端部署与 Nginx 代理配置文档

本项目在生产环境下需要 Nginx 反向代理来处理跨域请求、Referer 校验以及获取用户真实 IP。

## 1. Nginx 核心配置

在你的 Nginx 虚拟主机配置文件中（通常在 `/etc/nginx/conf.d/` 或 `/etc/nginx/sites-available/` 下），请在对应的 `server` 块中添加以下内容。

> **注意**：下文中的 `/i-wanna-be-a-judge/` 应替换为你实际的部署子目录路径。

```nginx
server {
    listen 443 ssl; # 建议使用 HTTPS
    server_name gallery.liruochen.cn;

    # 1. 静态资源根目录
    location /i-wanna-be-a-judge/ {
        alias /var/www/i-wanna-be-a-judge/dist/; # 替换为你的 dist 文件夹实际路径
        index index.html;
        try_files $uri $uri/ /i-wanna-be-a-judge/index.html;
    }

    # 2. 定位接口代理 (解决 Referer 校验与跨域)
    location /i-wanna-be-a-judge/api-mapchaxun/ {
        proxy_pass https://www.mapchaxun.cn/;
        
        # 必须伪造请求头，否则对方服务器会拒绝请求
        proxy_set_header Referer "https://www.mapchaxun.cn/Regeo";
        proxy_set_header Origin "https://www.mapchaxun.cn";
        proxy_set_header Host "www.mapchaxun.cn";
        
        proxy_ssl_server_name on;
        add_header 'Access-Control-Allow-Origin' '*';
    }

    # 3. IP 获取接口代理 (解决 CORS 跨域限制)
    location /i-wanna-be-a-judge/api-ip {
        proxy_pass https://4.ipw.cn/;
        
        # 强制指定 Host，穿透对方的反向代理校验
        proxy_set_header Host "4.ipw.cn";
        
        proxy_ssl_server_name on;
    }
}
```

## 2. 部署流程 (更新步骤)

每次更新代码后，请按照以下步骤操作：

1. **本地构建**：
   ```bash
   npm run build
   ```
2. **同步代码**：
   将本地 `dist/` 目录下的内容通过 Git 或 SCP 同步到服务器的对应目录。
3. **重载 Nginx** (仅在第一次配置或修改 Nginx 配置后需要)：
   ```bash
   sudo nginx -t          # 检查配置文件语法是否正确
   sudo nginx -s reload   # 平滑重载配置
   ```

## 3. 原理解析

*   **api-mapchaxun**: 前端代码调用 `api-mapchaxun/...`。Nginx 会在后台将其转发给 `mapchaxun.cn`。由于后端（Nginx）不受浏览器 Referer 修改限制，它可以成功伪造来源完成校验。
*   **api-ip**: 由于 `4.ipw.cn` 的 CORS 策略非常严格，前端直接调用会报跨域错误。通过 Nginx 代理，前端访问的是同源路径，由 Nginx 在后端代为请求获取 IP。
*   **子目录部署**: 代码中已通过 `vite.config.js` 的 `base: './'` 实现了相对路径引用，结合 Nginx 的 `alias` 或 `root` 配置，可确保在任何子路径下正常运行。
