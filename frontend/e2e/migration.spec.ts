import { test, expect, Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function waitForApp(page: Page) {
  await page.goto("/");
  await expect(page.locator("h1")).toContainText("OMA Agent");
}

// ---------------------------------------------------------------------------
// Smoke test
// ---------------------------------------------------------------------------

test("page loads and shows OMA Agent title", async ({ page }) => {
  await waitForApp(page);
  await expect(page.locator("h1")).toBeVisible();
  await expect(page.locator("#module-name-input")).toBeVisible();
  await expect(page.locator("#file-name-input")).toBeVisible();
  await expect(page.locator("#source-version-select")).toBeVisible();
});

// ---------------------------------------------------------------------------
// UI interaction tests
// ---------------------------------------------------------------------------

test("can change source version dropdown", async ({ page }) => {
  await waitForApp(page);
  const select = page.locator("#source-version-select");
  await select.selectOption("17.0");
  await expect(select).toHaveValue("17.0");
});

test("can type into module name and filename inputs", async ({ page }) => {
  await waitForApp(page);
  const moduleInput = page.locator("#module-name-input");
  await moduleInput.fill("sale_custom");
  await expect(moduleInput).toHaveValue("sale_custom");

  const fileInput = page.locator("#file-name-input");
  await fileInput.fill("models/sale_order.py");
  await expect(fileInput).toHaveValue("models/sale_order.py");
});

test("migrate button is visible and clickable", async ({ page }) => {
  await waitForApp(page);
  const migrateBtn = page.locator("#migrate-btn");
  await expect(migrateBtn).toBeVisible();
  await expect(migrateBtn).toBeEnabled();
});

test("results tab is visible by default", async ({ page }) => {
  await waitForApp(page);
  await expect(page.locator("#tab-results")).toBeVisible();
  await expect(page.locator("#tab-chat")).toBeVisible();
  await expect(page.locator("#tab-report")).toBeVisible();
});

test("chat tab opens expert assistant panel", async ({ page }) => {
  await waitForApp(page);
  await page.locator("#tab-chat").click();
  // The ChatInterface should render a text area / input
  await expect(page.locator("textarea, input[type='text']").first()).toBeVisible();
});

test("report tab is disabled until migration runs", async ({ page }) => {
  await waitForApp(page);
  const reportBtn = page.locator("#tab-report");
  await expect(reportBtn).toBeDisabled();
});

// ---------------------------------------------------------------------------
// Upload panel
// ---------------------------------------------------------------------------

test("upload button toggles file upload panel", async ({ page }) => {
  await waitForApp(page);
  const uploadBtn = page.locator("#toggle-upload-btn");
  await expect(uploadBtn).toBeVisible();

  // Upload panel hidden initially
  await expect(page.locator("#file-upload-zone")).not.toBeVisible();

  // Click to open
  await uploadBtn.click();
  await expect(page.locator("#file-upload-zone")).toBeVisible();

  // Click again to close
  await uploadBtn.click();
  await expect(page.locator("#file-upload-zone")).not.toBeVisible();
});

test("file upload zone accepts a dropped .py file", async ({ page }) => {
  await waitForApp(page);
  await page.locator("#toggle-upload-btn").click();
  await expect(page.locator("#file-upload-zone")).toBeVisible();

  // Simulate file selection via the hidden input
  const fileInput = page.locator("#file-upload-input");
  await fileInput.setInputFiles({
    name: "models.py",
    mimeType: "text/x-python",
    buffer: Buffer.from("from odoo import models, fields\nclass Test(models.Model):\n    _name = 'test.model'\n"),
  });

  // Uploaded file should appear in the list
  await expect(page.locator("text=models.py")).toBeVisible();
});

// ---------------------------------------------------------------------------
// Migration flow (mocked backend)
// ---------------------------------------------------------------------------

test("migrate button shows loading spinner during request", async ({ page }) => {
  // Intercept API call and delay it
  await page.route("**/api/migrate", async route => {
    await page.waitForTimeout(300);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        module_name: "test_module",
        source_version: "15.0",
        target_version: "19.0",
        original_code: "# original",
        migrated_code: "# migrated",
        diff: "",
        issues: [],
        explanation: "Test explanation.",
        filename: "models.py",
      }),
    });
  });

  await waitForApp(page);
  const btn = page.locator("#migrate-btn");
  await btn.click();

  // Spinner text appears briefly
  await expect(page.locator("text=Migrating")).toBeVisible();

  // Wait for result
  await expect(page.locator("text=Migration Output")).toBeVisible({ timeout: 5000 });
});

test("migration result shows issues list when API returns issues", async ({ page }) => {
  await page.route("**/api/migrate", async route => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        module_name: "test_module",
        source_version: "15.0",
        target_version: "19.0",
        original_code: "from openerp import models",
        migrated_code: "from odoo import models",
        diff: "",
        issues: [
          {
            line: 1,
            severity: "critical",
            message: "Uses deprecated 'openerp' import — must change to 'odoo'.",
            suggestion: "Replace `from openerp` with `from odoo`.",
          },
        ],
        explanation: "Changed import.",
        filename: "models.py",
      }),
    });
  });

  await waitForApp(page);
  await page.locator("#migrate-btn").click();
  await expect(page.locator("text=Migration Output")).toBeVisible({ timeout: 5000 });
  await expect(page.locator("text=CRITICAL Issue")).toBeVisible();
  await expect(page.locator("text=Apply Fix")).toBeVisible();
});

test("report tab becomes active after successful migration", async ({ page }) => {
  await page.route("**/api/migrate", async route => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        module_name: "test_module",
        source_version: "15.0",
        target_version: "19.0",
        original_code: "# original",
        migrated_code: "# migrated",
        diff: "",
        issues: [],
        explanation: "",
        filename: "models.py",
      }),
    });
  });

  await waitForApp(page);
  await page.locator("#migrate-btn").click();
  await expect(page.locator("text=Migration Output")).toBeVisible({ timeout: 5000 });
  await expect(page.locator("#tab-report")).toBeEnabled();
});

test("error banner shows on failed migration API call", async ({ page }) => {
  await page.route("**/api/migrate", async route => {
    await route.fulfill({ status: 500, body: "Internal Server Error" });
  });

  await waitForApp(page);
  await page.locator("#migrate-btn").click();
  await expect(page.locator("text=Migration failed")).toBeVisible({ timeout: 5000 });
});
