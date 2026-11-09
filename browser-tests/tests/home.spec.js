const { test, expect } = require("@playwright/test");

test("shows the default greeting and refreshes it", async ({ page }) => {
  await page.goto("/");

  const greeting = page.locator("#greeting");
  await expect(greeting).toHaveText("Hello from Lab 3!");

  await page.getByRole("button", { name: "Refresh greeting" }).click();
  await expect(greeting).toHaveText("Hello from Lab 3!");
});
