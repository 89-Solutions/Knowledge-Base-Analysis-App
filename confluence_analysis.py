import requests
from bs4 import BeautifulSoup
def get_spaces(Domain,Username,Api_Token):
    """
    Fetch all spaces from Confluence.
    """
    spaces = []
    start = 0
    limit = 50  # Number of results per request
    SPACES_URL = f"https://{Domain}.atlassian.net/wiki/rest/api/space"

    while True:
        response = requests.get(SPACES_URL, auth=(Username, Api_Token), params={"start": start, "limit": limit})
        if response.status_code != 200:
            print(f"Failed to fetch spaces: {response.status_code}, {response.text}")
            break

        data = response.json()
        spaces.extend(data.get("results", []))

        if data["size"] < limit:
            break  # No more results to fetch

        start += limit

    return spaces

def get_all_pages(Domain,Username,Api_Token,space_key,space_name):
    """
    Fetch all pages for a given space.
    """
    pages = []
    start = 0
    limit = 50  # Number of results per request
    PAGES_URL = f"https://{Domain}.atlassian.net/wiki/rest/api/content"

    while True:
        response = requests.get(PAGES_URL, auth=(Username, Api_Token), params={
            "spaceKey": space_key,
            "type": "page",
            "expand": "body.storage",
            "start": start,
            "limit": limit
        })
        if response.status_code != 200:
            print(f"Failed to fetch pages for space {space_key}: {response.status_code}, {response.text}")
            break

        data = response.json()
        results= data.get("results", [])
        for page in results:
            pages.append({
                    "space_name": space_name,
                    "title": page['title'],
                    "content": page.get("body", {}).get("storage", {}).get("value", ""),
                    "link": f"https://{Domain}.atlassian.net/wiki/spaces/{space_name}/pages/{page['id']}"
            })
        if data["size"] < limit:
            break  # No more results to fetch
        start += limit

    return pages

def check_compatibility(content):
    """Check compatibility of an article's HTML content with the specified criteria."""
    issues = []
    soup = BeautifulSoup(content, "html.parser")

    # Check for disallowed headers (H4-H7)
    if soup.find(["h4", "h5", "h6", "h7"]):
        issues.append("Uses disallowed header tags (H4-H7).")

    # Check for tables
    if soup.find("table"):
        issues.append("Uses tables, which are not allowed.")

    # Check for hyperlinks in headings
    for heading in soup.find_all(["h1", "h2", "h3"]):
        if heading.find("a"):
            issues.append("Contains hyperlinks in headings.")

    # Check for buttons or quick links
    if soup.find(class_="button") or soup.find(class_="quick-link"):
        issues.append("Contains buttons or quick links.")
        
    if soup.find("button"):
        issues.append("Contains <button> elements, which are not allowed.")
    
    if soup.find("div", class_="button") or soup.find("div", onclick=True):
        issues.append("Contains <div> elements used as buttons, which are not allowed.")
    
    if soup.find("a", class_="quick-link"):
        issues.append("Contains quick links with class 'quick-link', which are not allowed.")
    
    if soup.find("div", class_="quick-link") or soup.find("div", onclick=True):
        issues.append("Contains <div> elements used as quick links, which are not allowed.")

    # Check for elaborate introductory content
    first_paragraph = soup.find("p")
    if first_paragraph and len(first_paragraph.text) > 500:
        issues.append("Has an overly elaborate introductory paragraph.")

    # Check for images
    has_images = bool(soup.find("img"))
    if has_images:
        note = "This article has embedded images. Please ensure there is sufficient text included to explain the content of the images."
        if not issues:
            return {"is_compatible": False, "needs_review": True, "issues": [note]}
        else:
            issues.append(note)

    return {"is_compatible": not issues, "issues": issues}

def fetch_result(pages):

    results = []
    needs_review_counter = 0 
    compatible_counter = 0
    incompatible_counter = 0
    for page in pages:
        compatibility = check_compatibility(page["content"])
        if compatibility.get("needs_review"):
            needs_review_counter+=1
            row_class = "needs-review"
            status = "Needs Review"
        else:
            if compatibility["is_compatible"]:
                compatible_counter+=1
            else:
                incompatible_counter+=1

            row_class = "compatible" if compatibility["is_compatible"] else "incompatible"
            status = "Compatible" if compatibility["is_compatible"] else "Incompatible"

        results.append({
                "title": page["title"],
                "status": status,
                "findings": compatibility["issues"],
                "row_class": row_class,
                "link": page['link'],
                "space_name": page['space_name']
            })
        stats = {
            "Total": len(pages),
            "Needs_Review": needs_review_counter,
            "Compatible": compatible_counter,
            "Incompatible": incompatible_counter
        }
    return results, stats

def get_pages(Domain,Username,Api_Token):

    all_pages = []
    spaces = get_spaces(Domain,Username,Api_Token)
    for space in spaces:
        space_key = space["key"]
        space_name = space["name"]
        pages = get_all_pages(Domain,Username,Api_Token,space_key,space_name)
        all_pages.extend(pages)
    return all_pages