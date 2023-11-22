from flask import *
import pyodbc
import requests
from bs4 import BeautifulSoup



# Database connection setup
server_name = "SQLServer/Omar-Ahmed"
database_name = "ContentReader"
username = ""
password = ""

try:
    conn = pyodbc.connect(
        f"DRIVER={{SQL Server}};SERVER={server_name};DATABASE={database_name};UID={username};PWD={password}"
    )
    print("Database connection successful")
except pyodbc.Error as e:
    print("Database connection failed:", e)

app = Flask(__name__)

@app.route('/processing')
def processing():
    url = request.args.get('url')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM [ContentReader].[dbo].[WebPages] WHERE url=?", (url,))
    existing_record = cursor.fetchone()
    if existing_record:
        cursor.close()
        return jsonify({"status": False, "messages": "URL already exists in the database."})
    else:
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            clean_content = soup.get_text()
            clean_content = clean_content.replace('\n', '')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO [ContentReader].[dbo].[WebPages] (url, content) VALUES (?, ?)", url, clean_content)
            cursor.close()
            conn.commit()
            return   jsonify({"status":True,"messages":"Fetch content from the URL."}) 
        else:
            return   jsonify({"status":False,"messages":"Failed to fetch content from the URL."}) 


def find_and_output(text, query):
    index = text.find(query)
    if index != -1:
        end_index = text.find(". ", index)
        if end_index != -1:
            result = text[index:end_index + 1]
        else:
            result = text[index:]
    else:
        result = ""
    return result

def jaccard_similarity(str1, str2):
    set1 = set(str1.split())
    set2 = set(str2.split())
    intersection = len(set1.intersection(set2))
    union = len(set1) + len(set2) - intersection
    similarity = intersection / union
    return similarity * 100

@app.route("/search")
def search():
    query = request.args.get('searchtext')

    cursor = conn.cursor()
    cursor.execute("SELECT content FROM WebPages WHERE content LIKE ?", f"%{query}%")
    rows = cursor.fetchall()
    cursor.close()
    summaries = []
    for row in rows:
        content = row[0]
        result = find_and_output(content, query)
        similarity_percentage = jaccard_similarity(result, query)
        print(similarity_percentage)
        temp=[]
        temp.append(result)
        temp.append(round(similarity_percentage,2))
        summaries.append(temp)

    summaries.sort(key=lambda x: x[1], reverse=True)
    return jsonify({"query":query,"summaries":summaries}) 

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/secondpages')
def secondpages():
    return render_template("secondpages.html")

if __name__ == '__main__':
    app.run(host='127.0.0.1',debug=True) 