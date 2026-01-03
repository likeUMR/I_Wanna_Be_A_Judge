简单直接地回答：不能直接运行，需要额外配置 Nginx。
目前的方案在开发环境下（npm run dev）运行完美，是因为 Vite 的开发服务器充当了“中间人”来帮你转发请求并伪造 Referer 头。但是当你执行 vite build 之后，所有的代理配置都会失效，因为生成的只是纯静态文件（HTML/JS/CSS）。
要在生产环境（Nginx）中跑通，你需要在 Nginx 的配置文件中手动添加一段“反向代理”配置，来模拟 Vite 的行为。
为什么需要配置？
浏览器出于安全考虑，禁止 JS 代码修改 Referer。你在开发环境能成功，是因为请求路径 /api-mapchaxun 被 Vite 拦截并由 Node.js 后端 发出了请求（后端不受浏览器限制）。
Nginx 配置方案
在你的 Nginx 虚拟主机配置（通常是 /etc/nginx/conf.d/default.conf 或类似文件）的 server 块中，添加以下内容：

server {
    listen 80;
    server_name yourdomain.com; # 你的域名

    # 静态资源根目录
    location / {
        root /usr/share/nginx/html; # 你部署打包后文件的路径
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 【关键】对应代码里的 /api-mapchaxun 代理配置
    location /api-mapchaxun/ {
        # 转发到目标接口
        proxy_pass https://www.mapchaxun.cn/;
        
        # 必须伪造请求头，否则对方服务器会拒绝
        proxy_set_header Referer "https://www.mapchaxun.cn/Regeo";
        proxy_set_header Origin "https://www.mapchaxun.cn";
        proxy_set_header Host "www.mapchaxun.cn";
        
        # 避免证书校验等可能导致的问题（可选）
        proxy_ssl_server_name on;
        
        # 处理跨域（如果 Nginx 和前端域名不一致）
        add_header 'Access-Control-Allow-Origin' '*';
    }
}

部署时的注意事项：
路径一致性：代码中使用的请求路径是 /api-mapchaxun/...，所以 Nginx 的 location 必须也是这个名字。
HTTPS 问题：如果你的服务器是 HTTPS 的，而接口是 HTTP 的，浏览器可能会报 Mixed Content 错误。不过 mapchaxun.cn 支持 HTTPS，所以尽量保持全站 HTTPS。
高德 API Key：高德的 restapi.amap.com 支持 CORS，通常不需要通过 Nginx 代理，直接在前端调用即可（就像你现在代码里写的那样）。
总结： 部署后，前端发出的 /api-mapchaxun 请求会被你的 Nginx 拦截，Nginx 会像之前的 Vite 一样，帮你在后台带上 Referer 头去请求目标服务器，然后再把结果吐回给前端。这样就完美解决了生产环境的限制问题。