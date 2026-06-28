import { expect, test } from '@playwright/test'

test('battlefield renders graph evidence, filters, and ring overlays', async ({ page }) => {
  const consoleErrors: string[] = []
  const notFound: string[] = []

  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text())
    }
  })
  page.on('response', (response) => {
    if (response.status() === 404) {
      notFound.push(response.url())
    }
  })

  await page.goto('/battlefield')

  await expect(page.locator('h1')).toHaveText('Battlefield')
  await expect(page.locator('input[type="range"]')).toHaveCount(1)
  await expect(page.locator('select')).toHaveCount(1)
  await expect(page.locator('.ring-overlay-row')).toHaveCount(4)
  await expect(page.locator('.react-flow__node').first()).toBeVisible()
  expect(await page.locator('.react-flow__node').count()).toBeGreaterThan(35)
  await expect(page.locator('.react-flow')).toBeVisible()
  await expect(page.getByText('222 links')).toBeVisible()
  await expect(page.locator('.status')).toHaveText('Demo data only')

  expect(consoleErrors).toEqual([])
  expect(notFound).toEqual([])
})

test('primary dashboard routes render without empty shells', async ({ page }) => {
  const routes = [
    ['/', 'Static Fraud vs Adaptive Fraud'],
    ['/rings', 'Rings'],
    ['/cases', 'Cases'],
    ['/experiments', 'Experiments'],
    ['/defense-lab', 'Defense Lab'],
    ['/after-action', 'After-Action Report'],
    ['/methodology', 'Methodology']
  ] as const

  for (const [route, heading] of routes) {
    await page.goto(route)
    await expect(page.locator('h1')).toHaveText(heading)
    await expect(page.locator('.status')).toHaveText('Demo data only')
  }
})
