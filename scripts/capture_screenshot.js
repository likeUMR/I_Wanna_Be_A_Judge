import puppeteer from 'puppeteer';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function capture() {
  const url = 'http://localhost:5173/';
  const screenshotDir = path.join(__dirname, '../screenshots');
  
  // 1. 清空截图文件夹
  if (fs.existsSync(screenshotDir)) {
    console.log('正在清空旧截图...');
    fs.readdirSync(screenshotDir).forEach(file => {
      const filePath = path.join(screenshotDir, file);
      fs.unlinkSync(filePath);
    });
  } else {
    fs.mkdirSync(screenshotDir);
  }
  
  // 2. 固定文件名，确保“覆盖”效果
  const outputPath = path.join(screenshotDir, `latest_screenshot.png`);

  console.log(`正在启动浏览器访问 ${url}...`);
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();
    
    // 设置 16:8 分辨率 (1920x960)
    await page.setViewport({
      width: 1920,
      height: 960,
      deviceScaleFactor: 1,
    });

    console.log('正在加载页面...');
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 90000 });
    
    // 等待位置加载完成
    console.log('等待应用初始化...');
    await page.waitForFunction(() => {
      const loadingScreen = document.querySelector('.loading-screen');
      const loadingCase = document.querySelector('.loading-case');
      return !loadingScreen && !loadingCase;
    }, { timeout: 60000 });

    // 额外的渲染缓冲
    await new Promise(r => setTimeout(r, 2000));

    console.log(`正在截图并保存至 ${outputPath}...`);
    await page.screenshot({ path: outputPath, fullPage: false });
    
    console.log('截图成功！最新截图已保存为 latest_screenshot.png');
  } catch (error) {
    console.error('截图失败:', error);
  } finally {
    await browser.close();
  }
}

capture();
