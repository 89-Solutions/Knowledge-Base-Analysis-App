import requests
from bs4 import BeautifulSoup
     
headers = {"Content-Type": "application/json"}

def get_articles(instance,username,password):
    """Fetch all articles from the ServiceNow Knowledge Base."""
    articles = []
    page = 0
    limit = 100  # ServiceNow API supports pagination, fetch in batches
    while True:
        offset = page * limit
        url = f"https://{instance}.service-now.com/api/now/table/kb_knowledge?sysparm_query=textISNOTEMPTY&sysparm_display_value=true&sysparm_limit={limit}&sysparm_offset={offset}"
        response = requests.get(url, auth=(username, password), headers=headers)
        response.raise_for_status()
        data = response.json().get("result", [])
        if not data:  # No more articles
            break
        for article in data:
            articles.append({
                "id": article["sys_id"],
                "title": article["short_description"],
                "content": article.get("text", ""),
                "knowledge_base": article.get("kb_knowledge_base", {}).get("display_value", "Unknown")
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

def get_results(articles,instance):

    results = []
    needs_review_counter = 0 
    compatible_counter = 0
    incompatible_counter = 0
    for article in articles:
        compatibility = check_compatibility(article["content"])
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
                "knowledge_base": article["knowledge_base"],
                "status": status,
                "findings": compatibility["issues"],
                "row_class": row_class,
                "link": f"https://{instance}.service-now.com/now/nav/ui/classic/params/target/kb_view.do%3Fsys_kb_id%3D{article['id']}%26preview_article%3Dtrue"
            })
        stats = {
            "Total": len(articles),
            "Needs_Review": needs_review_counter,
            "Compatible": compatible_counter,
            "Incompatible": incompatible_counter
        }
    return results, stats