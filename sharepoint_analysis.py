import requests
from bs4 import BeautifulSoup

def get_access_token(client_id,client_secret,tenant_id):
    """
    Generate an access token using client credentials flow.
    """
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default"
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Error obtaining access token: {response.status_code} - {response.text}")

def get_site(access_token,site_url):

    url_without_protocol = site_url.split("://")[1]
    hostname, relative_path = url_without_protocol.split("/", 1)
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:/{relative_path}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["id"]

def get_pages(access_token,site_id,site_url):
    """
    Retrieve all pages from the Site Pages library.
    """
    pages = []
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/microsoft.graph.sitePage?expand=canvasLayout"
    while pages_url:
        response = requests.get(pages_url, headers=headers)
        response.raise_for_status()
        data = response.json().get("value", [])
        pages_url = response.json().get("@odata.nextLink")  # Fetch the next page if available
        for page in data:
            pages.append({
                    "title": page["title"],
                    "content": page["canvasLayout"],
                    "link": f"{site_url}/SitePages/{page['name']}"
            })
    return pages

def check_compatibility(content):

    issues = []
    needs_review = False
    # Iterate through horizontal sections
    for section in content.get("horizontalSections", []):
        for column in section.get("columns", []):
            for webpart in column.get("webparts", []):
                webpart_odata_type = webpart.get("@odata.type")
                webpart_type = webpart.get("webPartType")

                # Check if the web part type is incompatible
                if webpart_odata_type=="#microsoft.graph.standardWebPart":
                    if webpart_type=="0f087d7f-520e-42b7-89c0-496aaf979d58":
                        issues.append("Contains button webpart, which are not allowed.")
                    if webpart_type=="c70391ea-0b10-4ee9-b2b4-006d3fcad0cd":
                        issues.append("Contains quick links webpart, which are not allowed.")
                    if webpart_type=="f92bf067-bc19-489e-a556-7fe95f508720":
                        issues.append("Contains list webpart, which are not allowed.")
                    if webpart_type=="d1d91016-032f-456d-98a4-721247c305e8":
                        needs_review = True  
                if webpart_odata_type=="#microsoft.graph.textWebPart":
                    Html_content = webpart.get("innerHtml")
                    """Check compatibility of an article's HTML content with the specified criteria."""
                    soup = BeautifulSoup(Html_content, "html.parser")
                    # Check for disallowed headers (H4-H7)
                    if soup.find(["h4", "h5", "h6", "h7"]):
                        issues.append("Uses disallowed header tags (H4-H7).")

                    # Check for tables
                    if soup.find("table"):
                        issues.append("Uses tables, which are not allowed.")

                    # Check for lists
                    if soup.find(["ul", "ol"]):
                        issues.append("Uses lists, which are not allowed.")

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
                        needs_review = True
                        
    if not issues and needs_review:
        return {"is_compatible": False, "needs_review": True, "issues": ["This article has embedded images. Please ensure there is sufficient text included to explain the content of the images."]}
    if needs_review:
        issues.append("This article has embedded images. Please ensure there is sufficient text included to explain the content of the images.")

    return {"is_compatible": not issues, "issues": issues}

def get_result(pages):

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
                "link": page['link']
            })
        stats = {
            "Total": len(pages),
            "Needs_Review": needs_review_counter,
            "Compatible": compatible_counter,
            "Incompatible": incompatible_counter
        }
    return results, stats

def get_all_pages(client_id,client_secret,tenant_id,site_url):
        
    access_token = get_access_token(client_id,client_secret,tenant_id)
    site_id = get_site(access_token,site_url)
    pages = get_pages(access_token,site_id,site_url)
    return pages
