import os
import json
from typing import Dict, List, Optional, Union

def read_moodle_store(store_path: str = "data/stores/moodlestore") -> Dict:
    """
    Liest die gespeicherten Moodle-Daten aus dem Store.
    
    Args:
        store_path: Pfad zum Moodle Store Verzeichnis
        
    Returns:
        Dictionary mit allen Moodle-Daten
    """
    store_data = {
        'site': None,
        'courses': [],
        'sections': [],
        'modules': [],
        'contents': []
    }
    
    json_path = os.path.join(store_path, "moodle_content.json")
    
    if not os.path.exists(json_path):
        print(f"Keine Moodle-Daten gefunden in {json_path}")
        return store_data
        
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            store_data = json.load(f)
            print(f"Moodle-Daten erfolgreich geladen aus {json_path}")
            return store_data
    except Exception as e:
        print(f"Fehler beim Lesen der Moodle-Daten: {str(e)}")
        return store_data

def write_store_content_file(store_data: Dict, output_file: str = "content_datastore.txt"):
    """
    Schreibt die Store-Daten in eine formatierte Textdatei.
    
    Args:
        store_data: Die geladenen Store-Daten
        output_file: Zieldatei für die formatierte Ausgabe
    """
    with open(output_file, "w", encoding="utf-8") as f:
        # Site Information
        site = store_data.get('site', {})
        f.write(f"Moodle-Site: {site.get('name', '')}\n")
        f.write(f"URL: {site.get('url', '')}\n")
        f.write(f"Zusammenfassung: {site.get('summary', '')}\n\n")
        
        courses = store_data.get('courses', [])
        f.write(f"Gefundene Kurse: {len(courses)}\n\n")
        
        # Für jeden Kurs
        for course in courses:
            f.write("=" * 80 + "\n")
            f.write(f"Kurs: {course.get('name', '')}\n")
            f.write(f"ID: {course.get('course_id', '')}\n")
            f.write(f"URL: {course.get('url', '')}\n")
            f.write(f"Zusammenfassung: {course.get('summary', '')}\n\n")
            
            # Finde alle Abschnitte für diesen Kurs
            course_sections = [
                section for section in store_data.get('sections', [])
                if section.get('course_id') == course.get('course_id')
            ]
            
            f.write("Abschnitte:\n")
            for section in course_sections:
                f.write(f"    Abschnittsname: {section.get('name', '')}\n")
                f.write(f"    Beschreibung: {section.get('description', '')}\n")
                
                # Finde alle Module für diesen Abschnitt
                section_modules = [
                    module for module in store_data.get('modules', [])
                    if module.get('course_id') == course.get('course_id') and
                    module.get('section_name') == section.get('name')
                ]
                
                if section_modules:
                    f.write("    Module:\n")
                    for module in section_modules:
                        f.write(f"        Modulname: {module.get('name', '')}\n")
                        f.write(f"        Modultyp: {module.get('modname', '')}\n")
                        f.write(f"        URL: {module.get('url', '')}\n")
                        f.write(f"        Beschreibung: {module.get('description', '')}\n")
                        
                        # Finde alle Inhalte für dieses Modul
                        module_contents = [
                            content for content in store_data.get('contents', [])
                            if content.get('module_id') == module.get('id')
                        ]
                        
                        if module_contents:
                            f.write("        Inhalte:\n")
                            for content in module_contents:
                                f.write(f"            Dateiname: {content.get('filename', '')}\n")
                                f.write(f"            Datei-URL: {content.get('fileurl', '')}\n")
                                if content.get('text'):
                                    f.write(f"            Inhalt: {content.get('text', '')}\n")
                        f.write("\n")
                f.write("\n")
            f.write("\n")

def main():
    # Daten aus dem Store laden
    store_data = read_moodle_store()
    
    # In Vergleichsdatei schreiben
    write_store_content_file(store_data)
    
    print(f"\nStore-Daten wurden in content_datastore.txt geschrieben.")
    print("Sie können nun die Dateien moodle_content.txt und content_datastore.txt vergleichen.")

if __name__ == "__main__":
    main()
