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
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        input[type="text"], textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        textarea {
            height: 100px;
            resize: vertical;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .validate-btn {
            background-color: #2196F3;
        }
        .validate-btn:hover {
            background-color: #0b7dda;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            white-space: pre-wrap;
            font-family: monospace;
        }
        .success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .error {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .info {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }
        .loading {
            display: none;
            text-align: center;
            color: #666;
        }
        .pine-ids-help {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>TradingView Access Management</h1>
        
        <div class="form-group">
            <label for="username">Username:</label>
            <input type="text" id="username" placeholder="Enter TradingView username">
        </div>
        
        <div class="form-group">
            <label for="pineIds">Pine IDs (for access operations):</label>
            <textarea id="pineIds" placeholder='Enter Pine IDs, one per line or as JSON array:
PUB;a34266bd1a4f46c4a6b541b7922c026c
PUB;another_id_here

OR

["PUB;a34266bd1a4f46c4a6b541b7922c026c", "PUB;another_id_here"]'></textarea>
            <div class="pine-ids-help">
                Pine IDs can be found in browser developer console when accessing scripts on TradingView.
            </div>
        </div>
        
        <div class="form-group">
            <label for="duration">Access Duration (for granting access):</label>
            <input type="text" id="duration" placeholder="e.g., 1M, 3M, 6M, 1Y, L" value="L" list="duration-options">
            <datalist id="duration-options">
                <option value="L">Lifetime</option>
                <option value="1M">1 Month</option>
                <option value="3M">3 Months</option>
                <option value="6M">6 Months</option>
                <option value="1Y">1 Year</option>
                <option value="2Y">2 Years</option>
                <option value="1W">1 Week</option>
                <option value="30D">30 Days</option>
            </datalist>
            <div class="pine-ids-help">
                Common options: <strong>L</strong> (Lifetime), 1M (1 Month), 3M (3 Months), 6M (6 Months), 1Y (1 Year)<br>
                Format: Number + Letter (M=Month, Y=Year, W=Week, D=Day) or <strong>L</strong> for Lifetime
            </div>
        </div>
        
        <button type="button" class="validate-btn" onclick="validateUsername()">Validate Username</button>
        <button type="button" onclick="checkAccess()">Check Current Access</button>
        <button type="button" onclick="grantAccess()">Grant Access</button>
        <button type="button" onclick="removeAccess()">Remove Access</button>
        
        <div class="loading" id="loading">Processing...</div>
        <div id="result"></div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }
        
        function showResult(message, type = 'info') {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = message;
            resultDiv.className = `result ${type}`;
        }
        
        function getUsername() {
            const username = document.getElementById('username').value.trim();
            if (!username) {
                showResult('Please enter a username', 'error');
                return null;
            }
            return username;
        }
        
        function getPineIds() {
            const pineIdsText = document.getElementById('pineIds').value.trim();
            if (!pineIdsText) {
                return [];
            }
            
            try {
                // Try to parse as JSON first
                if (pineIdsText.startsWith('[') && pineIdsText.endsWith(']')) {
                    return JSON.parse(pineIdsText);
                }
                
                // Otherwise split by lines and filter empty lines
                return pineIdsText.split('\\n').map(id => id.trim()).filter(id => id.length > 0);
            } catch (e) {
                showResult('Invalid Pine IDs format. Please use one ID per line or valid JSON array.', 'error');
                return null;
            }
        }
        
        async function validateUsername() {
            const username = getUsername();
            if (!username) return;
            
            showLoading(true);
            try {
                const response = await fetch(`${API_BASE}/validate/${encodeURIComponent(username)}`);
                const data = await response.json();
                
                if (response.ok) {
                    if (data.validuser) {
                        showResult(`✅ Valid username: ${data.verifiedUserName}`, 'success');
                    } else {
                        showResult('❌ Invalid username', 'error');
                    }
                } else {
                    showResult(`Error: ${data.errorMessage || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                showResult(`Network error: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        }
        
        async function checkAccess() {
            const username = getUsername();
            const pineIds = getPineIds();
            if (!username || pineIds === null) return;
            
            if (pineIds.length === 0) {
                showResult('Please enter at least one Pine ID to check access', 'error');
                return;
            }
            
            showLoading(true);
            try {
                const response = await fetch(`${API_BASE}/access/${encodeURIComponent(username)}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ pine_ids: pineIds })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showResult(`Current Access Status:\\n${JSON.stringify(data, null, 2)}`, 'info');
                } else {
                    showResult(`Error: ${data.errorMessage || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                showResult(`Network error: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        }
        
        async function grantAccess() {
            const username = getUsername();
            const pineIds = getPineIds();
            const duration = document.getElementById('duration').value.trim() || '1M';
            if (!username || pineIds === null) return;
            
            if (pineIds.length === 0) {
                showResult('Please enter at least one Pine ID to grant access', 'error');
                return;
            }
            
            showLoading(true);
            try {
                const response = await fetch(`${API_BASE}/access/${encodeURIComponent(username)}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ pine_ids: pineIds, duration: duration })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showResult(`✅ Access Grant Results:\\n${JSON.stringify(data, null, 2)}`, 'success');
                } else {
                    showResult(`Error: ${data.errorMessage || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                showResult(`Network error: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        }
        
        async function removeAccess() {
            const username = getUsername();
            const pineIds = getPineIds();
            if (!username || pineIds === null) return;
            
            if (pineIds.length === 0) {
                showResult('Please enter at least one Pine ID to remove access', 'error');
                return;
            }
            
            if (!confirm(`Are you sure you want to remove access for user "${username}" from ${pineIds.length} script(s)?`)) {
                return;
            }
            
            showLoading(true);
            try {
                const response = await fetch(`${API_BASE}/access/${encodeURIComponent(username)}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ pine_ids: pineIds })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showResult(`✅ Access Removal Results:\\n${JSON.stringify(data, null, 2)}`, 'success');
                } else {
                    showResult(`Error: ${data.errorMessage || 'Unknown error'}`, 'error');
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
