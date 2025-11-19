from scan_interface import ScanSession

s = ScanSession(hashMap, dbname="egais")
endpoint = hashMap.get("1C_endpoint") if hashMap.containsKey("1C_endpoint") else None

sent = s.finish_document(endpoint)

if sent:
    toast("Документ успешно отправлен")
else:
    toast("Документ сохранён в очередь отправки")

hashMap.put("ShowScreen", "ЕГАИС3_Отгрузка_ВыборДокумента")
