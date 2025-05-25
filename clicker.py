import time
import base64
import os
from playwright.async_api import async_playwright
from obtain_captcha import get_captcha_text

async def download_arrival_card(resident: bool, arrival_date: str, ic: str, dob: str, email: str) -> None:
    """
    resident: True → SCPR (use NRIC), False → LTP (use FIN)
    arrival_date: exact text of the date-button, e.g. "24/05/"
    ic: NRIC or FIN string
    dob: Date of Birth string, e.g. "20/11/1998"
    email: your email address
    """
    url = "https://eservices.ica.gov.sg/sgarrivalcard/scpr" if resident else "https://eservices.ica.gov.sg/sgarrivalcard/ltp"
    id_label = "NRIC * ! Please fill in the" if resident else "FIN * ! Please fill in the"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")

        # fill form
        await page.get_by_role("button", name=arrival_date).click()
        await page.get_by_role("textbox", name=id_label).fill(ic)
        await page.get_by_role("textbox", name="Date of Birth * !").fill(dob)
        await page.get_by_role("textbox", name="Email Address * tooltipLabel").fill(email)
        await page.get_by_role("button", name="NO").click()
        await page.get_by_role("button", name="NO").nth(1).click()
        await page.get_by_role("button", name="Next").click()
        await page.get_by_role("checkbox", name="I have read and agreed to the").check()
        await page.get_by_role("button", name="Next").click()

        await page.wait_for_timeout(1000)  # wait for captcha

        # extract & save captcha
        img = await page.wait_for_selector("img.bg_color")
        src = await img.get_attribute("src") or ""
        if not src.startswith("data:image"):
            print("❌ CAPTCHA not found")
            await browser.close()
            return

        header, b64 = src.split(",", 1)
        ext = header.split("/")[1].split(";")[0]      # e.g. 'png'
        captcha_file = f"captcha.{ext}"
        with open(captcha_file, "wb") as f:
            f.write(base64.b64decode(b64))
        print(f"✅ Saved {captcha_file}")

        # solve captcha
        text = get_captcha_text()
        await page.get_by_role("textbox", name="Enter text here:").fill(text)
        await page.get_by_role("button", name="Submit").click()

        # download PDF
        try:
            btn = page.get_by_role("button", name="  Download PDF")
            await btn.wait_for(state="visible", timeout=10000)
            async with page.expect_download(timeout=30000) as dl:
                await btn.click()
            download = await dl.value
            pdf_name = f"{ic}.pdf"
            await download.save_as(pdf_name)
            print(f"✅ Downloaded {pdf_name}")
        except Exception as e:
            print(f"❌ Download failed: {e}")

        # cleanup
        if os.path.exists(captcha_file):
            os.remove(captcha_file)
            print(f"🗑️ Removed {captcha_file}")

        await browser.close()
