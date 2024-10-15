
#include <windows.h>
#include <winspool.h>
#include <iostream>


bool GetPrinterStatus(const char* printerName, DWORD& dwStatus) {
    HANDLE hPrinter;
    PRINTER_DEFAULTS pd = {0};
    pd.DesiredAccess = PRINTER_ACCESS_USE;

    // Apri la stampante
    if (!OpenPrinter((LPSTR)printerName, &hPrinter, &pd)) {
        std::cerr << "Impossibile aprire la stampante: " << printerName << std::endl;
        return false;
    }

    DWORD dwBytesNeeded;
    PRINTER_INFO_2* pPrinterInfo = nullptr;

    // Richiedi la dimensione del buffer necessario
    GetPrinter(hPrinter, 2, NULL, 0, &dwBytesNeeded);
    pPrinterInfo = (PRINTER_INFO_2*)malloc(dwBytesNeeded);

    // Ottieni le informazioni della stampante
    if (!GetPrinter(hPrinter, 2, (LPBYTE)pPrinterInfo, dwBytesNeeded, &dwBytesNeeded)) {
        std::cerr << "Errore nella lettura delle informazioni della stampante" << std::endl;
        free(pPrinterInfo);
        ClosePrinter(hPrinter);
        return false;
    }

    // Controlla lo stato della stampante
    dwStatus = pPrinterInfo->Status;
	std::cout << "Stato: " << pPrinterInfo->Status << std::endl;

    // Pulisci
    free(pPrinterInfo);
    ClosePrinter(hPrinter);

	return true;
}

void PrintStatus(DWORD& dwStatus) {
    if (dwStatus & PRINTER_STATUS_PAUSED) {
        std::cout << "Stampante in pausa" << std::endl;
    } else if (dwStatus & PRINTER_STATUS_ERROR) {
        std::cout << "Errore nella stampante" << std::endl;
    } else if (dwStatus & PRINTER_STATUS_OFFLINE) {
        std::cout << "Stampante offline" << std::endl;
    } else if (dwStatus & PRINTER_STATUS_PAPER_OUT) {
        std::cout << "Carta esaurita" << std::endl;
    } else if (dwStatus & PRINTER_STATUS_PRINTING) {
        std::cout << "Stampante in stampa" << std::endl;
    } else if (dwStatus == 0) {
        std::cout << "Stampante pronta" << std::endl;
    } else {
		std::cout << "Stato non riconosciuto" << std::endl;
	}
}

