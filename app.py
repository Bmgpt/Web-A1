import subprocess
import streamlit as st
from urllib.parse import urlparse
from AI import consultantAI

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
        st.error(f"Error occurred during scanning: {e.output.decode('utf-8')}")
        return None  # Return None if any subprocess fails

    return report_file_name

# Main Streamlit app logic
def main():
    st.title("Web Vulnerability Scanner and AI Consultant")

    # Input form for website URL
    website_url = st.text_input("Enter the website URL to scan")

    if st.button("Run Scan"):
        if not website_url:
            st.error("Website URL is missing")
        else:
            # Call the web vulnerability scanner function
            report_file_name = web_vulnerability_scan(website_url)
            
            if report_file_name is None:
                st.error("Error during scanning process.")
            else:
                try:
                    # Run simple.py to get additional output
                    scanner_output = subprocess.check_output(['python', 'simple.py', website_url])
                except subprocess.CalledProcessError as e:
                    st.error(f"Error occurred while running simple.py: {e.output.decode('utf-8')}")
                    return

                # Call the AI module
                ai_instance = consultantAI()
                prompt = ai_instance.read_report(report_file_name)
                solution_content = ai_instance.generate_solution(prompt)

                # Append scanner output to the report file
                with open(report_file_name, 'a') as report_file:
                    report_file.write(scanner_output.decode('utf-8'))

                # Read the final content of the report
                with open(report_file_name, 'r') as report_file:
                    tool_output = report_file.read()

                # Display the report content
                st.subheader("Tool Output:")
                st.text(tool_output)

                # Display the AI solutions
                st.subheader("AI Generated Solutions:")
                if solution_content is None:
                    st.warning("API key invalid, see AI.py")
                else:
                    solutions_list = solution_content.strip().split('\n')
                    for solution in solutions_list:
                        st.write(solution)

    st.sidebar.title("Navigation")
    st.sidebar.write("This is a web vulnerability scanning app with AI consulting powered by Streamlit.")

if __name__ == '__main__':
    main()
