from flask import Flask, render_template, request, jsonify
import sqlite3
import re
import ollama

app = Flask(__name__)

# Function to execute SQL queries
def execute_query(query, params=()):
    try:
        conn = sqlite3.connect("company.db")  # Connect to the database
        cursor = conn.cursor()
        cursor.execute(query, params)  # Execute query with parameters
        result = cursor.fetchall()
        conn.close()
        return result
    except sqlite3.Error as e:
        return f"Database error: {e}"

# Function to check predefined queries
def process_query(user_input):
    user_input = user_input.lower()

    if "show me all employees in" in user_input:
        match = re.search(r"show me all employees in (the )?(?P<dept>\w+)", user_input)
        if match:
            department = match.group("dept").capitalize()
            query = "SELECT Name FROM Employees WHERE LOWER(Department) = LOWER(?)"
            result = execute_query(query, (department,))
        else:
            return "I couldn't understand the department name."

    elif "who is the manager of" in user_input:
        match = re.search(r"who is the manager of (the )?(?P<dept>\w+)", user_input)
        if match:
            department = match.group("dept").capitalize()
            query = "SELECT Manager FROM Departments WHERE LOWER(Name) = LOWER(?)"
            result = execute_query(query, (department,))
        else:
            return "I couldn't understand the department name."

    elif "list all employees hired after" in user_input:
        match = re.search(r"list all employees hired after (?P<date>\d{4}-\d{2}-\d{2})", user_input)
        if match:
            date = match.group("date")
            query = "SELECT Name FROM Employees WHERE Hire_Date > ?"
            result = execute_query(query, (date,))
        else:
            return "Please enter a valid date in YYYY-MM-DD format."

    elif "what is the total salary expense for" in user_input:
        match = re.search(r"what is the total salary expense for (the )?(?P<dept>\w+)", user_input)
        if match:
            department = match.group("dept").capitalize()
            query = "SELECT SUM(Salary) FROM Employees WHERE LOWER(Department) = LOWER(?)"
            result = execute_query(query, (department,))
        else:
            return "I couldn't understand the department name."

    else:
        # Call Ollama if query doesn't match predefined patterns
        return process_with_ollama(user_input)

    return result if result else "No data found."

# Function to use Ollama for unrecognized queries
def process_with_ollama(user_input):
    prompt = f"""
    You are an AI assistant with access to an employee database. Generate an SQL query based on the user's request.
    
    - If the query is about employees, departments, managers, salaries, or hiring dates, generate a valid SQL query.
    - If the query is unrelated to these topics, return "I'm not sure how to answer that."
    
    User Query: "{user_input}"
    
    Output ONLY the SQL query, nothing else.
    """

    response = ollama.chat(model="llama3.2:1b", messages=[{"role": "user", "content": prompt}])
    sql_query = response['message']['content'].strip()

    # If the response is a valid SQL query, execute it
    if "SELECT" in sql_query.upper():
        return execute_query(sql_query)
    
    return "I'm not sure how to answer that."


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    response = process_query(user_input)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
