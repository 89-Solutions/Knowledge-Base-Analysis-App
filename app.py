import identity.web
import json
from flask import Flask, render_template, request, redirect, session, url_for
from flask_session import Session
from freshservice_analysis import fetch_all_articles, fetch_results
from servicenow_analysis import get_articles, get_results
from sharepoint_analysis import get_all_pages, get_result
from confluence_analysis import get_pages, fetch_result

import app_config

app = Flask(__name__)
app.config.from_object(app_config)
Session(app)

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

auth = identity.web.Auth(
    session=session,
    authority=app.config["AUTHORITY"],
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],
)

def load_connectors():
    try:
        with open('connectors.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def store_connectors(connectors):
    with open('connectors.json', 'w') as f:
        json.dump(connectors, f, indent=4)

def load_reports():
    try:
        with open('reports.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def store_reports(reports):
    with open('reports.json', 'w') as f:
        json.dump(reports, f, indent=4)

@app.route("/login")
def login():
    return render_template("login.html", **auth.log_in(
        scopes=app_config.SCOPE,
        redirect_uri=url_for("auth_response", _external=True)
    ))

@app.route(app_config.REDIRECT_PATH)
def auth_response():
    result = auth.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    return redirect(auth.log_out(url_for("admin", _external=True)))

@app.route("/save_connector", methods=["POST"])
def save_connector():
    user = auth.get_user()
    if not user:
        return redirect(url_for("login"))

    connectors = load_connectors()
    new_id = len(connectors) + 1
    connector_data = {
        "id": new_id,
        "app_name": request.form["app_name"],
        "connector_name": request.form["connector_name"],
        "user_email": user.get("preferred_username"),
        "details": {key: value for key, value in request.form.items() if key not in ["app_name", "connector_name"]}
    }
    connectors.append(connector_data)
    store_connectors(connectors)
    return redirect(url_for("admin"))

@app.route("/")
def admin():
    user = auth.get_user()
    if not user:
        return redirect(url_for("login"))
    
    # Filter connectors for the logged-in user
    user_email = user.get("preferred_username")
    connectors = load_connectors()
    user_connectors = [conn for conn in connectors if conn["user_email"] == user_email]
    
    return render_template("admin.html", user=user, connectors=user_connectors)

@app.route("/reports", methods=["GET", "POST"])
def manage_reports():
    user = auth.get_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        reports = load_reports()
        data = request.form.to_dict()
        report_id = data.get("report_id", None)
        if report_id:
            report_id = int(report_id)
        report_name = data["report_name"]
        connector = data["connector"]
        details = data["details"]

        if report_id:  # Update an existing report
            for report in reports:
                if report["id"] == report_id:
                    report["name"] = report_name
                    report["connector"] = connector
                    report["details"] = details
                    break
        else:  # Create a new report
            new_id = len(reports) + 1
            reports.append({
                "id": new_id,
                "name": report_name,
                "connector": connector,
                "details": details
            })
        store_reports(reports)

    return render_template("reports.html", reports=load_reports(), connectors=load_connectors())


@app.route("/run_report/<int:report_id>", methods=["GET"])
def run_report(report_id):

    token = auth.get_token_for_user(app_config.SCOPE)
    if "error" in token:
        return redirect(url_for("login"))

    reports = load_reports()
    report = next((r for r in reports if r["id"] == report_id), None)
    if not report:
        return "Report not found", 404
    connectors = load_connectors()
    connector_data = next((c for c in connectors if c["connector_name"] == report['connector']), None)
    app_name = connector_data["app_name"]
    data = connector_data["details"]

    # Perform analysis based on the selected application
    results = []
    if app_name == "Freshservice":
        Domain = data['domain']
        Api_Key = data['api_key']
        articles = fetch_all_articles(Domain,Api_Key)
        results, stats = fetch_results(articles,Domain)
    elif app_name == "ServiceNow":
        instance = data['instance']
        username = data['username']
        password = data['password']
        all_articles = get_articles(instance,username,password)
        results, stats = get_results(all_articles,instance)
    elif app_name == "SharePoint":
        client_id = data['client_id']
        client_secret = data['client_secret']
        tenant_id = data['tenant_id']
        site_url = data['site_url']
        pages = get_all_pages(client_id,client_secret,tenant_id,site_url)
        results, stats = get_result(pages)
    elif app_name == "Confluence":
        Domain = data['domain']
        Username = data['username']
        Api_Token = data['api_token']
        pages = get_pages(Domain,Username,Api_Token)
        results, stats = fetch_result(pages)
    
    return render_template("analysis.html", results=results, app_name=app_name, stats=stats, report_name=report['name'])

if __name__ == '__main__':
    app.run(debug=True)
