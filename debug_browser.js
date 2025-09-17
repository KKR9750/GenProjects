const { chromium } = require('playwright');

async function debugLocalhost() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('Navigating to http://localhost:8002...');

    // Monitor network requests
    page.on('response', response => {
        if (response.status() >= 400) {
            console.log(`FAILED REQUEST: ${response.url()} - Status: ${response.status()}`);
        }
    });

    await page.goto('http://localhost:8002', { waitUntil: 'networkidle' });

    // Wait a moment for any JavaScript to load
    await page.waitForTimeout(2000);

    // Take a screenshot
    await page.screenshot({ path: 'D:\\GenProjects\\localhost_screenshot.png', fullPage: true });
    console.log('Screenshot saved to localhost_screenshot.png');

    // Get some debug info
    const title = await page.title();
    console.log('Page title:', title);

    // Check if elements exist (using correct selectors for MetaGPT interface)
    const hasChatMessages = await page.locator('.chat-messages').count();
    const hasTextarea = await page.locator('textarea').count();
    const hasStartButton = await page.locator('.start-button, .continue-button').count();
    const hasWelcomeMessage = await page.locator('.welcome-message').count();

    console.log('Elements found:');
    console.log('- Chat messages area:', hasChatMessages > 0 ? 'YES' : 'NO');
    console.log('- Input textarea:', hasTextarea > 0 ? 'YES' : 'NO');
    console.log('- Action buttons:', hasStartButton > 0 ? 'YES' : 'NO');
    console.log('- Welcome message:', hasWelcomeMessage > 0 ? 'YES' : 'NO');

    // Get console logs and errors
    const logs = [];
    const errors = [];

    page.on('console', msg => {
        const logMessage = `[${msg.type()}] ${msg.text()}`;
        logs.push(logMessage);
        console.log('BROWSER LOG:', logMessage);
    });

    page.on('pageerror', error => {
        const errorMessage = error.message;
        errors.push(errorMessage);
        console.log('PAGE ERROR:', errorMessage);
    });

    // Wait for potential JavaScript execution
    await page.waitForTimeout(3000);

    // Check if React loaded
    const hasReact = await page.evaluate(() => {
        return typeof window.React !== 'undefined';
    });

    const hasReactDOM = await page.evaluate(() => {
        return typeof window.ReactDOM !== 'undefined';
    });

    const hasBabel = await page.evaluate(() => {
        return typeof window.Babel !== 'undefined';
    });

    const hasRoot = await page.evaluate(() => {
        return document.getElementById('root') !== null;
    });

    console.log('React Environment:');
    console.log('- React loaded:', hasReact ? 'YES' : 'NO');
    console.log('- ReactDOM loaded:', hasReactDOM ? 'YES' : 'NO');
    console.log('- Babel loaded:', hasBabel ? 'YES' : 'NO');
    console.log('- Root element exists:', hasRoot ? 'YES' : 'NO');

    // Check if the React app actually rendered
    const rootContent = await page.evaluate(() => {
        const root = document.getElementById('root');
        return root ? root.innerHTML : 'NO ROOT';
    });

    console.log('Root element content length:', rootContent.length);
    console.log('Root has content:', rootContent.length > 0 ? 'YES' : 'NO');

    if (errors.length > 0) {
        console.log('\n=== ERRORS FOUND ===');
        errors.forEach(error => console.log('ERROR:', error));
    }

  } catch (error) {
    console.error('Error:', error.message);
  }

  await browser.close();
}

debugLocalhost();