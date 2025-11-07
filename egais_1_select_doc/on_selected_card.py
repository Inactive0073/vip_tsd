from scan_interface import ScanSession
import json 

s = ScanSession(hashMap, dbname="egais") # type: ignore

selected_data: dict[str, str] = json.loads(hashMap.get("selected_card_data")) # type: ignore


if selected_data:
    s.start_doc(selected_data)
    toast(f"Document selected: {selected_data.get('_id', 'No id')}") # type: ignore
    hashMap.put("ShowScreen", "ЕГАИС3_Отгрузка_Сканирование") # type: ignore
else:
    toast("No document selected") # type: ignore