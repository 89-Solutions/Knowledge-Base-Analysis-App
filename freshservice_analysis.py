import requests
from bs4 import BeautifulSoup

headers = {"Content-Type": "application/json"}

def get_categories(Domain,Api_Key):
    """Fetch all categories in the knowledge base."""
    url = f"https://{Domain}/api/v2/solutions/categories"
    response = requests.get(url, auth=(Api_Key, ""), headers=headers)
    response.raise_for_status()
    return response.json().get("categories")

def get_folders(category_id,Domain,Api_Key):
    """Fetch all folders for a specific category."""
    url = f"https://{Domain}/api/v2/solutions/folders?category_id={category_id}"
    response = requests.get(url, auth=(Api_Key, ""), headers=headers)
    response.raise_for_status()
    return response.json().get("folders")

def get_articles(folder_id,Domain,Api_Key):
    """Fetch all articles for a specific folder."""
    url = f"https://{Domain}/api/v2/solutions/articles?folder_id={folder_id}"
    articles = []
    page = 1
    while True:
        response = requests.get(f"{url}&page={page}", auth=(Api_Key, ""), headers=headers)
        response.raise_for_status()
        data = response.json().get("articles")
        if not data:  # No more articles
            break
        # Extract relevant details
        for article in data:
            articles.append({
                "id": article["id"],
                "title": article["title"],
                "description": article.get("description", "")
            })
        page += 1
    return articles

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

def fetch_all_articles(Domain,Api_Key):
    """Fetch all articles across all categories and folders."""
    all_articles = []
    categories = get_categories(Domain,Api_Key)
    for category in categories:
        category_name = category["name"]
        folders = get_folders(category["id"],Domain,Api_Key)
        for folder in folders:
            folder_name = folder["name"]
            articles = get_articles(folder["id"],Domain,Api_Key)
            for article in articles:
                article["category_name"] = category_name
                article["folder_name"] = folder_name
                all_articles.append(article)
    return all_articles

def fetch_results(articles,domain):

    results = []
    needs_review_counter = 0 
    compatible_counter = 0
    incompatible_counter = 0
    for article in articles:
        compatibility = check_compatibility(article["description"])
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
                "title": article["title"],
                "category_name": article["category_name"],
                "folder_name": article["folder_name"],
                "status": status,
                "findings": compatibility["issues"],
                "row_class": row_class,
                "link": f"https://{domain}/solution/articles/{article['id']}"
            })
        stats = {
            "Total": len(articles),
            "Needs_Review": needs_review_counter,
            "Compatible": compatible_counter,
            "Incompatible": incompatible_counter
        }
    return results, stats
