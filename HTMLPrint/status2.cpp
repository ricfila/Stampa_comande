#include <iostream>
#include <comdef.h>
#include <Wbemidl.h>
#include <windows.h>  // Per MultiByteToWideChar

#pragma comment(lib, "wbemuuid.lib")
#pragma comment(lib, "ole32.lib")

// Codice non usato. Va controllato

BSTR ConvertToBSTR(const char* str) {
    int len = MultiByteToWideChar(CP_ACP, 0, str, -1, NULL, 0);
    BSTR bstr = SysAllocStringLen(NULL, len);
    MultiByteToWideChar(CP_ACP, 0, str, -1, bstr, len);
    return bstr;
}

void CheckPrinterStatusWMI(const char* printerName) {
    HRESULT hres;

    // Inizializza COM.
    hres = CoInitializeEx(0, COINIT_MULTITHREADED);
    if (FAILED(hres)) {
        std::cerr << "Errore nella inizializzazione di COM" << std::endl;
        return;
    }

    // Imposta i livelli di sicurezza.
    hres = CoInitializeSecurity(
        NULL,
        -1,
        NULL,
        NULL,
        RPC_C_AUTHN_LEVEL_DEFAULT,
        RPC_C_IMP_LEVEL_IMPERSONATE,
        NULL,
        EOAC_NONE,
        NULL
    );

    if (FAILED(hres)) {
        std::cerr << "Errore nella sicurezza COM" << std::endl;
        CoUninitialize();
        return;
    }

    // Ottieni un puntatore all'interfaccia WMI.
    IWbemLocator* pLoc = NULL;
    hres = CoCreateInstance(
        CLSID_WbemLocator,
        0,
        CLSCTX_INPROC_SERVER,
        IID_IWbemLocator, (LPVOID*)&pLoc);

    if (FAILED(hres)) {
        std::cerr << "Errore nella creazione dell'istanza IWbemLocator" << std::endl;
        CoUninitialize();
        return;
    }

    // Connettiti a WMI.
    IWbemServices* pSvc = NULL;
    BSTR namespaceName = SysAllocString(L"ROOT\\CIMV2");
    BSTR user = SysAllocString(L"");
    BSTR password = SysAllocString(L"");
    BSTR authority = SysAllocString(L"");

    hres = pLoc->ConnectServer(
        namespaceName,
        user,
        password,
        authority,
        RPC_C_AUTHN_LEVEL_DEFAULT,
        NULL,
        NULL,
        &pSvc);

    SysFreeString(namespaceName);
    SysFreeString(user);
    SysFreeString(password);
    SysFreeString(authority);

    if (FAILED(hres)) {
        std::cerr << "Impossibile connettersi a WMI" << std::endl;
        pLoc->Release();
        CoUninitialize();
        return;
    }

    // Imposta i livelli di sicurezza nel servizio WMI.
    hres = CoSetProxyBlanket(
        pSvc,
        RPC_C_AUTHN_WINNT,
        RPC_C_AUTHZ_NONE,
        NULL,
        RPC_C_AUTHN_LEVEL_CALL,
        RPC_C_IMP_LEVEL_IMPERSONATE,
        NULL,
        EOAC_NONE
    );

    if (FAILED(hres)) {
        std::cerr << "Errore nella configurazione della sicurezza del proxy" << std::endl;
        pSvc->Release();
        pLoc->Release();
        CoUninitialize();
        return;
    }

    // Esegui una query WMI per ottenere lo stato della stampante.
    IEnumWbemClassObject* pEnumerator = NULL;
    std::string query = "SELECT * FROM Win32_Printer WHERE Name = '";
    query += printerName;
    query += "'";

    BSTR bstrQuery = ConvertToBSTR(query.c_str());
    hres = pSvc->ExecQuery(
        bstr_t("WQL"),
        bstrQuery,
        WBEM_FLAG_FORWARD_ONLY | WBEM_FLAG_RETURN_IMMEDIATELY,
        NULL,
        &pEnumerator);

    SysFreeString(bstrQuery);

    if (FAILED(hres)) {
        std::cerr << "Errore nella esecuzione della query WMI" << std::endl;
        pSvc->Release();
        pLoc->Release();
        CoUninitialize();
        return;
    }

    // Elabora i risultati della query.
    IWbemClassObject* pclsObj = NULL;
    ULONG uReturn = 0;

    while (pEnumerator) {
        HRESULT hr = pEnumerator->Next(WBEM_INFINITE, 1, &pclsObj, &uReturn);

        if (uReturn == 0) {
            break;
        }

        VARIANT vtProp;

        // Ottieni il valore della proprietà "PrinterStatus".
        hr = pclsObj->Get(L"PrinterStatus", 0, &vtProp, 0, 0);
        if (SUCCEEDED(hr)) {
            int printerStatus = vtProp.intVal;
            std::cout << "Stato della stampante: " << printerStatus << std::endl;

            switch (printerStatus) {
                case 1:
                    std::cout << "La stampante è in pausa." << std::endl;
                    break;
                case 2:
                    std::cout << "La stampante è in attesa." << std::endl;
                    break;
                case 3:
                    std::cout << "La stampante è in stampa." << std::endl;
                    break;
                case 4:
                    std::cout << "La stampante è offline." << std::endl;
                    break;
                case 5:
                    std::cout << "La stampante ha un errore." << std::endl;
                    break;
                default:
                    std::cout << "Stato sconosciuto o pronto." << std::endl;
            }
        }

        VariantClear(&vtProp);
        pclsObj->Release();
    }

    // Pulisci.
    pEnumerator->Release();
    pSvc->Release();
    pLoc->Release();
    CoUninitialize();
}
