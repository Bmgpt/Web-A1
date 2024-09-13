import subprocess
from flask import Flask, render_template, request, jsonify
from urllib.parse import urlparse 
from flask_cors import CORS
from AI import consultantAI

app = Flask(__name__)
CORS(app, resources={r"/get_report_data": {"origins": "http://localhost:3000"}})

# Define a function to call the web vulnerability scanner
def web_vulnerability_scan(website_url):
    domain_name = urlparse(website_url).netloc
    report_file_name = f"./report/{domain_name}_report.txt"
    
    try:
        # Run external scripts
        subprocess.check_output(['python', 'web-vulnerability-scanner.py', 'full', website_url])
        subprocess.check_output(['python', 'wap.py', '-u', website_url, '-wf', report_file_name])
        subprocess.check_output(['python', 'virus-total.py', website_url, report_file_name])
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while scanning: {e.output}")
        return None  # Return None if any subprocess fails

    return report_file_name

@app.route('/test_website', methods=['POST'])
def test_website():
    website_url = request.form.get('website_url')
    
    if not website_url:
        return jsonify({'error': 'Website URL is missing'}), 400
    
    # Call the web vulnerability scanner function
    report_file_name = web_vulnerability_scan(website_url)

    if report_file_name is None:
        return jsonify({'error': 'Error during scanning'}), 500
    
    try:
        # Call another script to get scanner output
        scanner_output = subprocess.check_output(['python', 'simple.py', website_url])
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running simple.py: {e.output}")
        return jsonify({'error': 'Error during scanner execution'}), 500

    # Call the AI module
    ai_instance = consultantAI()
    prompt = ai_instance.read_report(report_file_name)
    solution_content = ai_instance.generate_solution(prompt)

    # Write scanner output to the report file
    with open(report_file_name, 'a') as report_file:
        report_file.write(scanner_output.decode('utf-8'))

    # Read the updated content of the report file
    with open(report_file_name, 'r') as report_file:
        tool_output = report_file.read()

    # Split the content by newlines for organized display
    tool_output_lines = tool_output.split('\n')
    
    if solution_content is None:
        solutions_list = ["API key invalid, see AI.Py"]
    else:
        solutions_list = solution_content.strip().split('\n')

    # Return JSON if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'solution_content': solution_content, 'tool_output': tool_output})

    # Otherwise, return HTML response
    return render_template('result.html', tool_output_lines=tool_output_lines, solutions=solutions_list)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_report_data', methods=['POST', 'GET'])
def get_report_data():
    website_url = request.json.get('website_url')
    
    if not website_url:
        return jsonify({'error': 'Website URL is missing'}), 400

    report_file_name = web_vulnerability_scan(website_url)

    if report_file_name is None:
        return jsonify({'error': 'Error during scanning'}), 500

    with open(report_file_name, 'r') as report_file:
        tool_output = report_file.readlines()

    return jsonify({'tool_output': tool_output})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
