from playwright.async_api import async_playwright
import win32print
import win32api
import win32con
import os
import asyncio


async def print_pdf(url, output_path, printer_name):
	async with async_playwright() as p:
		browser = await p.chromium.launch()
		page = await browser.new_page()
		#await page.set_viewport_size({'width': 1000, 'height': 2480})
		await page.goto(os.path.abspath(os.path.join(os.getcwd(), url)))
		await page.pdf(path=output_path, format= 'A5')
		#await page.screenshot(path=output_path, full_page=True)
		await browser.close()

		# Comando per stampare il PDF
		win32print.SetDefaultPrinter(printer_name)
		file_path = os.path.abspath(os.path.join(os.getcwd(), output_path))

		hPrinter = win32print.OpenPrinter(printer_name)
		job_id = win32print.StartDocPrinter(hPrinter, 1, ("Stampa comanda", None, None))
		win32print.StartPagePrinter(hPrinter)

		win32api.ShellExecute(0, "print", file_path, None, ".", win32con.SW_HIDE)

		win32print.EndPagePrinter(hPrinter)
		win32print.EndDocPrinter(hPrinter)

		jobs = win32print.EnumJobs(hPrinter, 0, -1, 1)
		for job in jobs:
			if job["JobId"] == job_id:
				print(f"Stato del job {job_id}: {job['Status']}")
				break
		
		win32print.ClosePrinter(hPrinter)
		print(job_id)


asyncio.run(print_pdf('output.html', 'print.pdf', 'HP4'))
