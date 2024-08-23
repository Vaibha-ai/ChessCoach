import subprocess

def run_chatgpt(fen, best_move):
    # Write the JavaScript code to a file
    js_code = f"""
const axios = require('axios');

const options = {{
  method: 'POST',
  url: 'https://chatgpt-api8.p.rapidapi.com/',
  headers: {{
    'content-type': 'application/json',
    'X-RapidAPI-Key': 'b262a22443msh09fce8bb1e138acp14a425jsn1dbcfc8a6b4c',
    'X-RapidAPI-Host': 'chatgpt-api8.p.rapidapi.com'
  }},
  data: [
    {{
      content: 'Why is the best move {best_move} useful for the board position {fen}? Are there any expected opponent moves?',
      role: 'user'
    }}
  ]
}};

async function run() {{
  try {{
    const response = await axios.request(options);
    console.log(response.data);
  }} catch (error) {{
    console.error('Error occurred:', error.message);
  }}
}}

run();
    """
    with open('script.js', 'w') as f:
        f.write(js_code)

    # Execute the JavaScript file using Node.js
    try:
        output = subprocess.check_output(['node', 'script.js'], stderr=subprocess.STDOUT)
        return output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return 'Error occurred: ' + e.output.decode('utf-8')
