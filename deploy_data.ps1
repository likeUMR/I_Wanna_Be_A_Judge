# 数据同步脚本：压缩 -> 传输 -> 解压 -> 清理
# 适用于文件数量多 (10000+) 的场景

$archiveName = "data_transfer.tar.gz"
$localDataPath = "public/data"
$remotePath = "/root/Projects/I_Wanna_Be_A_Judge/public"
$remoteTarget = "ali99:$remotePath"

Write-Host "----------------------------------------------------" -ForegroundColor Cyan
Write-Host "1. 正在本地压缩数据 ($localDataPath)..." -ForegroundColor Cyan

# 使用 Windows 自带的 tar 命令进行压缩 (效率比 Compress-Archive 高很多)
# -c: 创建, -z: gzip压缩, -f: 指定文件名, -C: 切换目录（避免压缩包内包含多层路径）
tar -czf $archiveName -C public data

if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 压缩失败" -ForegroundColor Red
    exit
}

Write-Host "2. 正在传输压缩包到 ali99..." -ForegroundColor Cyan
scp $archiveName $remoteTarget

if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 传输失败" -ForegroundColor Red
    Remove-Item $archiveName
    exit
}

Write-Host "3. 正在远程解压并清理..." -ForegroundColor Cyan
# 在远程执行：删除旧数据 -> 解压新数据 -> 删除压缩包
ssh ali99 "cd $remotePath && rm -rf data && tar -xzf $archiveName && rm $archiveName"

if ($LASTEXITCODE -eq 0) {
    Write-Host "4. 正在清理本地临时文件..." -ForegroundColor Cyan
    Remove-Item $archiveName
    Write-Host "----------------------------------------------------" -ForegroundColor Cyan
    Write-Host "[成功] 数据打包传输并解压完成" -ForegroundColor Green
} else {
    Write-Host "[错误] 远程解压失败，请检查服务器磁盘空间或权限" -ForegroundColor Red
}
