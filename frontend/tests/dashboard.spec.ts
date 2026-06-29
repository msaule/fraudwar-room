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

  await expect(page.locator('h1')).toHaveText('Evidence Map')
  await expect(page.locator('input[type="range"]')).toHaveCount(1)
  await expect(page.locator('select')).toHaveCount(2)
  await expect(page.getByRole('region', { name: 'Scenario selector' })).toBeVisible()
  await expect(page.locator('.ring-overlay-row')).toHaveCount(4)
  await expect(page.locator('.react-flow__node').first()).toBeVisible()
  expect(await page.locator('.react-flow__node').count()).toBeGreaterThan(35)
  await expect(page.locator('.react-flow')).toBeVisible()
  await expect(page.getByText('222 links')).toBeVisible()
  await expect(page.locator('.status')).toHaveText('Demo data only')

  await page.locator('.react-flow__node').first().click()
  await expect(page.locator('.evidence-drawer')).toBeVisible()
  await expect(page.getByText('Linked Evidence')).toBeVisible()
  await page.getByLabel('Close evidence detail').click()
  await expect(page.locator('.evidence-drawer')).toHaveCount(0)

  expect(consoleErrors).toEqual([])
  expect(notFound).toEqual([])
})

test('case rows open evidence detail', async ({ page }) => {
  await page.goto('/cases')

  await expect(page.locator('h1')).toHaveText('Cases')
  await expect(page.locator('tbody tr[role="button"]').first()).toBeVisible()
  await page.locator('tbody tr[role="button"]').first().click()
  await expect(page.locator('.evidence-drawer')).toBeVisible()
  await expect(page.getByText('False-positive risk')).toBeVisible()
  await expect(page.getByText('Synthetic evidence bundle generated for defensive simulation.')).toBeVisible()
})

test('primary dashboard routes render without empty shells', async ({ page }) => {
  const routes = [
    ['/', 'Static Fraud vs Adaptive Fraud'],
    ['/rings', 'Rings'],
    ['/cases', 'Cases'],
    ['/experiments', 'Experiments'],
    ['/defense-lab', 'Defense Tests'],
    ['/after-action', 'Run Memo'],
    ['/methodology', 'Methodology']
  ] as const

  for (const [route, heading] of routes) {
    await page.goto(route)
    await expect(page.locator('h1')).toHaveText(heading)
    await expect(page.locator('.status')).toHaveText('Demo data only')
  }
})
