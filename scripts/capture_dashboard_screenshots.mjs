import { mkdir } from 'node:fs/promises'
import { createRequire } from 'node:module'
import path from 'node:path'

const baseURL = process.env.FRAUDWAR_DASHBOARD_URL ?? 'http://localhost:3000'
const outputDir = path.resolve('docs/portfolio/screenshots')
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
const require = createRequire(path.resolve('frontend/package.json'))
const { chromium } = require('playwright')

const shots = [
  ['command-center', '/'],
  ['battlefield', '/battlefield'],
  ['cases', '/cases'],
  ['defense-lab', '/defense-lab'],
  ['after-action', '/after-action']
]

await mkdir(outputDir, { recursive: true })

const browser = await chromium.launch({
  headless: true,
  ...(executablePath ? { executablePath } : {})
})

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
  for (const [name, route] of shots) {
    await page.goto(`${baseURL}${route}`, { waitUntil: 'networkidle' })
    if (route === '/battlefield') {
      await page.locator('.react-flow__node').first().waitFor({ state: 'visible', timeout: 15_000 })
    }
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(outputDir, `${name}.png`), fullPage: false })
  }
  console.log(JSON.stringify({ outputDir, screenshots: shots.map(([name]) => `${name}.png`) }))
} finally {
  await browser.close()
}
