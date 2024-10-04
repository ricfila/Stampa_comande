#include <windows.h>
#include <string>
#include <iostream>

/*
ATTENZIONE:
L'eseguibile dev'essere avviato con permessi di amministratore per poter funzionare
*/

bool PrinterExists(const std::string& printerName) {
    DWORD needed, returned;
    // Ottieni il numero di byte necessari per l'elenco delle stampanti
    EnumPrintersA(PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS, NULL, 2, NULL, 0, &needed, &returned);

    BYTE* buffer = new BYTE[needed];
    // Ottieni l'elenco delle stampanti
    if (EnumPrintersA(PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS, NULL, 2, buffer, needed, &needed, &returned)) {
        PRINTER_INFO_2A* printerInfo = (PRINTER_INFO_2A*)buffer;
        for (DWORD i = 0; i < returned; i++) {
            // Confronta i nomi delle stampanti usando strcmp
            if (strcmp(printerName.c_str(), printerInfo[i].pPrinterName) == 0) {
                delete[] buffer;
                return true; // Stampante trovata
            }
        }
    }
    delete[] buffer;
    return false; // Stampante non trovata
}

int main() {
    std::string printerName = "Titanic";

    if (PrinterExists(printerName)) {
        std::cout << "La stampante esiste già." << std::endl;
    } else {
        PRINTER_INFO_2A printerInfo;
        ZeroMemory(&printerInfo, sizeof(printerInfo));

        // Usa stringhe normali (LPSTR)
        printerInfo.pPrinterName = (LPSTR)printerName.c_str();
        printerInfo.pPortName = (LPSTR)"NUL:";  // Usa il dispositivo NUL per ignorare i dati
        printerInfo.pDriverName = (LPSTR)"Microsoft Print to PDF";  // Sostituisci con il driver virtuale che installi
        printerInfo.pPrintProcessor = (LPSTR)"WinPrint";
        printerInfo.pDatatype = (LPSTR)"RAW";
        printerInfo.Attributes = PRINTER_ATTRIBUTE_LOCAL;

        // Usa AddPrinterA per stringhe normali
        HANDLE hPrinter = AddPrinterA(NULL, 2, (LPBYTE)&printerInfo);
        if (hPrinter) {
            std::cout << "Stampante aggiunta con successo." << std::endl;
            ClosePrinter(hPrinter);
        } else {
            std::cout << "Errore nell'aggiungere la stampante." << std::endl;
        }
    }

    return 0;
}
