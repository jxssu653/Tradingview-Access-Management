from flask import Flask, request
from tradingview import tradingview
import json
from flask_cors import CORS
#from threading import Thread
app = Flask('')
CORS(app)


@app.route('/validate/<username>', methods=['GET'])
def validate(username):
  try:
    print(username)
    tv = tradingview()
    response = tv.validate_username(username)
    return json.dumps(response), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }
  except Exception as e:
    print("[X] Exception Occured : ", e)
    failureResponse = {'errorMessage': 'Unknown Exception Occurred'}
    return json.dumps(failureResponse), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/access/<username>', methods=['GET', 'POST', 'DELETE'])
def access(username):
  try:
    jsonPayload = request.json
    pine_ids = jsonPayload.get('pine_ids')
    print(jsonPayload)
    print(pine_ids)
    tv = tradingview()
    accessList = []
    for pine_id in pine_ids:
      access = tv.get_access_details(username, pine_id)
      accessList = accessList + [access]

    if request.method == 'POST':
      duration = jsonPayload.get('duration', '1M')  # Default to 1 month if not provided
      if not duration:
        duration = '1M'
      
      # Handle lifetime access (L) separately
      if duration.upper() == 'L':
        dType = 'L'
        dNumber = 0  # Not used for lifetime
      else:
        dNumber = int(duration[:-1])
        dType = duration[-1:]
      
      for access in accessList:
        tv.add_access(access, dType, dNumber)

    if request.method == 'DELETE':
      for access in accessList:
        tv.remove_access(access)
    return json.dumps(accessList), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occured : ", e)
    failureResponse = {'errorMessage': 'Unknown Exception Occurred'}
    return json.dumps(failureResponse), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/')
def main():
  return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingView Access Management</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 500px;
            text-align: center;
            animation: slideUp 0.6s ease-out;
        }
        
        @keyframes slideUp {
            from {
                transform: translateY(30px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
            font-weight: 700;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 40px;
            font-size: 16px;
        }
        
        .form-group {
            margin-bottom: 25px;
            text-align: left;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
            font-size: 14px;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: #f8f9fa;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .button-container {
            margin-top: 30px;
        }
        
        button {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .validate-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: none;
        }
        
        .validate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .claim-btn {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
            color: white;
            display: none;
        }
        
        .claim-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(86, 171, 47, 0.3);
        }
        
        button:disabled {
            background: #cccccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .loading {
            display: none;
            margin-top: 20px;
            color: #667eea;
            font-weight: 600;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .result {
            margin-top: 25px;
            padding: 20px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
            display: none;
        }
        
        .success {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            color: #155724;
        }
        
        .error {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            color: #721c24;
        }
        
        .user-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 12px;
            margin-top: 20px;
            display: none;
            text-align: left;
        }
        
        .user-info strong {
            color: #667eea;
        }
        
        .input-hint {
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: #aaa;
            font-size: 14px;
            display: none;
        }
        
        .form-group {
            position: relative;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>TradingView Access</h1>
        <p class="subtitle">Manage script access for users</p>
        
        <div class="form-group">
            <label for="username">TradingView Username</label>
            <input type="text" id="username" placeholder="Enter username to validate">
            <span class="input-hint" id="inputHint">Enter username</span>
        </div>
        
        <div class="button-container">
            <button type="button" class="validate-btn" id="validateBtn" onclick="validateUsername()">
                Validate User
            </button>
            <button type="button" class="claim-btn" id="claimBtn" onclick="claimAccess()">
                Claim Access
            </button>
        </div>
        
        <div class="loading" id="loading">
            <span class="spinner"></span>
            Processing...
        </div>
        
        <div class="user-info" id="userInfo">
            <strong>Verified User:</strong> <span id="verifiedUsername"></span>
        </div>
        
        <div id="result" class="result"></div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        let validatedUsername = null;
        
        // Show validate button when username is entered
        document.getElementById('username').addEventListener('input', function() {
            const username = this.value.trim();
            const validateBtn = document.getElementById('validateBtn');
            const claimBtn = document.getElementById('claimBtn');
            
            if (username) {
                validateBtn.style.display = 'block';
                claimBtn.style.display = 'none';
                validatedUsername = null;
                document.getElementById('userInfo').style.display = 'none';
                document.getElementById('result').style.display = 'none';
            } else {
                validateBtn.style.display = 'none';
                claimBtn.style.display = 'none';
            }
        });
        
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }
        
        function showResult(message, type = 'info') {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = message;
            resultDiv.className = `result ${type}`;
            resultDiv.style.display = 'block';
        }
        
        async function validateUsername() {
            const username = document.getElementById('username').value.trim();
            if (!username) {
                showResult('Please enter a username', 'error');
                return;
            }
            
            showLoading(true);
            document.getElementById('result').style.display = 'none';
            
            try {
                const response = await fetch(`${API_BASE}/validate/${encodeURIComponent(username)}`);
                const data = await response.json();
                
                if (response.ok) {
                    if (data.validuser) {
                        validatedUsername = data.verifiedUserName;
                        
                        // Hide validate button, show claim button
                        document.getElementById('validateBtn').style.display = 'none';
                        document.getElementById('claimBtn').style.display = 'block';
                        
                        // Show user info
                        document.getElementById('verifiedUsername').textContent = data.verifiedUserName;
                        document.getElementById('userInfo').style.display = 'block';
                        
                        showResult(`✅ Username validated successfully!`, 'success');
                    } else {
                        showResult('❌ Invalid username. Please check and try again.', 'error');
                    }
                } else {
                    showResult(`Error: ${data.errorMessage || 'Validation failed'}`, 'error');
                }
            } catch (error) {
                showResult(`Network error: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        }
        
        async function claimAccess() {
            if (!validatedUsername) {
                showResult('Please validate username first', 'error');
                return;
            }
            
            // Hardcoded Pine IDs for the claim access functionality
            const pineIds = ['PUB;a34266bd1a4f46c4a6b541b7922c026c'];
            const duration = 'L'; // Lifetime access
            
            showLoading(true);
            document.getElementById('result').style.display = 'none';
            
            try {
                const response = await fetch(`${API_BASE}/access/${encodeURIComponent(validatedUsername)}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ pine_ids: pineIds, duration: duration })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    const successMessage = `🎉 Access granted successfully!\\n\\nUser: ${validatedUsername}\\nAccess Level: Lifetime\\nStatus: Active`;
                    showResult(successMessage, 'success');
                } else {
                    showResult(`Error: ${data.errorMessage || 'Failed to grant access'}`, 'error');
                }
            } catch (error) {
                showResult(`Network error: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        }
    </script>
</body>
</html>
  '''


# def run():
#   app.run(host='0.0.0.0', port=5000)

# def start_server_async():
#   server = Thread(target=run)
#   server.start()


def start_server():
  app.run(host='0.0.0.0', port=5000)
