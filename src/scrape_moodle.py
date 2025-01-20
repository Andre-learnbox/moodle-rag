import requests
from pydantic import BaseModel, Field
from typing import Tuple, List, Optional
import os
import json


# Function to call Moodle API
def moodle_api_call(function_name, params):
    # Configuration
    MOODLE_URL = os.getenv("MOODLE_URL")
    API_TOKEN = os.getenv("MOODLE_API_TOKEN")
    REST_ENDPOINT = f"{MOODLE_URL}/webservice/rest/server.php"
    params["wstoken"] = API_TOKEN
    params["moodlewsrestformat"] = "json"
    params["wsfunction"] = function_name
    response = requests.get(REST_ENDPOINT, params=params)
    response.raise_for_status()
    return response.json()


def get_content_text(fileurl):
    API_TOKEN = os.getenv("MOODLE_API_TOKEN")
    params = {}
    params["wstoken"] = API_TOKEN
    response = requests.get(fileurl, params=params)
    response.raise_for_status()
    return response.json()


class MoodleModuleContent:
    def __init__(
        self,
        type: str,
        course_id: int = None,
        filename: Optional[str] = "",
        fileurl: Optional[str] = "",
        text: Optional[str] = "",
    ):
        self.type = type
        self.filename = filename
        self.fileurl = fileurl
        self.text = text

    def __str__(self):
        string = f"Filename: {self.filename}"
        if self.text:
            string += f", Content: {self.text}"
        return string

    def asdict(self):
        return {
            "filename": self.filename,
            "doc_type": "content",
            "course_id": self.course_id,
        }


class MoodleModule:
    def __init__(
        self,
        name: str,
        modname: str,
        url: str,
        course_id: int = None,
        description: Optional[str] = "",
        contents: List[MoodleModuleContent] = [],
    ):
        self.name = name
        self.description = description
        self.modname = modname
        self.url = url
        self.contents = contents

    def __str__(self):
        string = f"""
        Course Module {self.name}
        Type: {self.modname}
        URL: {self.url}
        Description: {self.description}
        """
        if len(self.contents) == 0:
            return string
        string += "\nContents:"
        for content in self.contents:
            string += "\n - " + str(content)
        return string

    def asdict(self):
        return {
            "name": self.name,
            "description": self.description,
            "doc_type": "module",
            "course_id": self.course_id,
        }


class MoodleCourseSection:
    def __init__(
        self,
        name: str,
        course_id: int = None,
        description: Optional[str] = "",
        modules: List[MoodleModule] = [],
    ):
        self.name = name
        self.description = description
        self.modules = modules

    def __str__(self):
        string = f"""
        Course Section {self.name}
        Description: {self.description}
        """
        if len(self.modules) == 0:
            return string
        string += "\nModules:"
        for module in self.modules:
            string += (
                "\n - Module Name " + module.name + ", Module Type " + module.modname
            )
        return string

    def asdict(self):
        return {
            "name": self.name,
            "description": self.description,
            "doc_type": "section",
            "course_id": self.course_id,
        }


class MoodleCourse:
    def __init__(
        self,
        id: int,
        name: str,
        summary: Optional[str] = "",
        sections: List[MoodleCourseSection] = [],
    ):
        self.id = id
        self.name = name
        self.summary = summary
        self.url = f"{os.getenv('MOODLE_URL')}/course/view.php?id={id}"
        self.sections = sections

    def __str__(self):
        string = f"""
        Course {self.name}
        URL: {self.url}
        Summary: {self.summary}
        """
        if len(self.sections) == 0:
            return string
        string += "\nSections:"
        for section in self.sections:
            string += "\n - " + section.name
        return string

    def asdict(self):
        return {
            "course_id": str(self.id),
            "name": self.name,
            "summary": self.summary,
            "url": self.url,
            "doc_type": "course",
        }


class MoodleSiteInfo:
    def __init__(
        self,
        name: str,
        url: str,
        summary: Optional[str] = "",
        courses: List[MoodleCourse] = [],
    ):
        self.name = name
        self.summary = summary
        self.url = url
        self.courses = courses

    def __str__(self):
        string = f"""
        Site Name: {self.name}
        URL: {self.url}
        Summary: {self.summary}
        """
        if len(self.courses) == 0:
            return string
        string += "\n" + str(len(self.courses)) + " courses available"

        if len(self.courses) > 10:
            string += "\nShowing first 10 courses"
            for i in range(min(10, len(self.courses))):
                course = self.courses[i]
                string += "\n - " + course.name
        else:
            for course in self.courses:
                string += "\n - " + course.name

        return string

    def asdict(self):
        return {
            "name": self.name,
            "summary": self.summary,
            "url": self.url,
            "doc_type": "site",
        }


# Get list of courses
def get_courses() -> MoodleSiteInfo:
    function_name = "core_course_get_courses"
    params = {}
    data = moodle_api_call(function_name, params)

    # First course is the site info
    if len(data) == 0:
        return None, []

    site_info = MoodleSiteInfo(
        name=data[0].get("fullname"),
        url=os.getenv("MOODLE_URL"),
        summary=data[0].get("summary"),
    )

    if len(data) < 2:
        return site_info, []

    courses = [
        MoodleCourse(
            id=course.get("id"),
            name=course.get("fullname"),
            summary=course.get("summary"),
        )
        for course in data[1:]
    ]

    site_info.courses = courses

    return site_info


# Get course sections
def get_course_sections(course_id) -> List[MoodleCourseSection]:
    function_name = "core_course_get_contents"
    params = {"courseid": course_id}
    data = moodle_api_call(function_name, params)
    sections = []
    for section in data:
        modules = []
        for module in section.get("modules"):
            contents = []
            if "contents" in module:
                for content in module.get("contents"):
                    if (
                        content.get("type") == "file"
                        and content.get("filename")
                        and content.get("filename").endswith(".html")
                    ):
                        contenttext = get_content_text(content.get("fileurl"))
                        contents.append(
                            MoodleModuleContent(
                                type="file",
                                filename=content.get("filename"),
                                fileurl=content.get("fileurl"),
                                text=contenttext,
                            )
                        )
                    else:
                        contents.append(
                            MoodleModuleContent(
                                type="file", filename=content.get("filename")
                            )
                        )
            modules.append(
                MoodleModule(
                    name=module.get("name"),
                    modname=module.get("modname"),
                    url=module.get("url"),
                    contents=contents,
                )
            )
        sections.append(
            MoodleCourseSection(
                name=section.get("name"),
                description=section.get("summary"),
                modules=modules,
            )
        )

    return sections


# Main function to scrape data
def scrape_moodle_data() -> MoodleSiteInfo:
    MOODLE_URL = (os.getenv("MOODLE_URL"),)
    site = get_courses()

    for course in site.courses:
        sections = get_course_sections(course.id)
        course.sections = sections

    return site

def write_course_data(file, course: MoodleCourse, indent_level: int = 0):
    indent = "    " * indent_level
    file.write(f"{indent}Kurs: {course.name}\n")
    file.write(f"{indent}ID: {course.id}\n")
    file.write(f"{indent}URL: {course.url}\n")
    file.write(f"{indent}Zusammenfassung: {course.summary}\n")
    
    if course.sections:
        file.write(f"{indent}Abschnitte:\n")
        for section in course.sections:
            write_section_data(file, section, indent_level + 1)
            file.write("\n")

def write_section_data(file, section: MoodleCourseSection, indent_level: int):
    indent = "    " * indent_level
    file.write(f"{indent}Abschnittsname: {section.name}\n")
    file.write(f"{indent}Beschreibung: {section.description}\n")
    
    if section.modules:
        file.write(f"{indent}Module:\n")
        for module in section.modules:
            write_module_data(file, module, indent_level + 1)

def write_module_data(file, module: MoodleModule, indent_level: int):
    indent = "    " * indent_level
    file.write(f"{indent}Modulname: {module.name}\n")
    file.write(f"{indent}Modultyp: {module.modname}\n")
    file.write(f"{indent}URL: {module.url}\n")
    file.write(f"{indent}Beschreibung: {module.description}\n")
    
    if module.contents:
        file.write(f"{indent}Inhalte:\n")
        for content in module.contents:
            write_content_data(file, content, indent_level + 1)

def write_content_data(file, content: MoodleModuleContent, indent_level: int):
    indent = "    " * indent_level
    file.write(f"{indent}Dateiname: {content.filename}\n")
    if content.fileurl:
        file.write(f"{indent}Datei-URL: {content.fileurl}\n")
    if content.text:
        file.write(f"{indent}Inhalt: {content.text}\n")

# Main function to scrape data and write to file
def scrape_moodle_data_to_file():
    site = get_courses()

    if site is None:
        print("Keine Daten verfügbar.")
        return

    for course in site.courses:
        sections = get_course_sections(course.id)
        course.sections = sections

    with open("moodle_content.txt", "w", encoding="utf-8") as f:
        f.write(f"Moodle-Site: {site.name}\n")
        f.write(f"URL: {site.url}\n")
        f.write(f"Zusammenfassung: {site.summary}\n\n")
        
        if site.courses:
            f.write(f"Gefundene Kurse: {len(site.courses)}\n\n")
            for course in site.courses:
                write_course_data(f, course)
                f.write("\n" + "="*80 + "\n\n")

    # Zusätzlich JSON-Export für strukturierte Daten
    with open("moodle_content.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "site": site.asdict(),
                "courses": [course.asdict() for course in site.courses],
                "sections": [
                    section.asdict() 
                    for course in site.courses 
                    for section in course.sections
                ],
                "modules": [
                    module.asdict()
                    for course in site.courses
                    for section in course.sections
                    for module in section.modules
                ],
                "contents": [
                    content.asdict()
                    for course in site.courses
                    for section in course.sections
                    for module in section.modules
                    for content in module.contents
                ]
            },
            f,
            indent=2,
            ensure_ascii=False
        )

# Trigger the scrape
def main():
    scrape_moodle_data_to_file()

if __name__ == "__main__":
    main()
