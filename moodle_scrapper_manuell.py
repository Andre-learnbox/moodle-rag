import requests
from pydantic import BaseModel, Field
from typing import Tuple, List, Optional
import os

# Function to call Moodle API
def moodle_api_call(function_name, params):
    # Configuration
    MOODLE_URL = "https://moodle.learnbox.de"
    API_TOKEN = "a81f41599657521b9321447f6704c0b8"
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
            string += "\n - Module Name " + module.name + ", Module Type " + module.modname
        return string

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

# Get list of courses
def get_courses() -> Optional[MoodleSiteInfo]:
    function_name = "core_course_get_courses"
    params = {}
    data = moodle_api_call(function_name, params)
    
    # Überprüfen, ob data eine Liste ist
    if not isinstance(data, list):
        print("Fehler: Die API hat keine Liste zurückgegeben.")
        return None

    # Überprüfen, ob die Liste leer ist
    if len(data) == 0:
        print("Fehler: Keine Kurse gefunden.")
        return None

    site_info = MoodleSiteInfo(
        name=data[0].get("fullname", "Unbekannt"),
        url=os.getenv("MOODLE_URL"),
        summary=data[0].get("summary", ""),
    )

    if len(data) < 2:
        return site_info

    courses = [
        MoodleCourse(
            id=course.get("id"),
            name=course.get("fullname"),
            summary=course.get("summary", ""),
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

# Main function to scrape data and write to file
def scrape_moodle_data_to_file():
    site = get_courses()

    if site is None:
        print("No data available.")
        return

    for course in site.courses:
        sections = get_course_sections(course.id)
        course.sections = sections

    with open("moodle_content.txt", "w", encoding="utf-8") as f:
        f.write(str(site))

# Trigger the scrape
def main():
    scrape_moodle_data_to_file()

if __name__ == "__main__":
    main()
