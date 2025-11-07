from scan_interface import ScanSession

s = ScanSession(hashMap, dbname="egais") # type: ignore

code = hashMap.get("barcode", "unknown") # type: ignore

# Удаляем запись из текущего документа
s.remove_scan(code)

# Обновляем таблицу документов
hashMap.put("docTable", s.build_table_json_for_items("^DOC_TABLE_ROW")) # type: ignore
hashMap.put("RefreshScreen", "") # type: ignore