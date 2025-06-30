from flask import Flask, request
from tradingview import tradingview
import json
import secrets
import time
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask('')
CORS(app)

# In-memory storage for activation keys and claimed users
activation_keys = {}  # {key: {email, name, timestamp, used, cancelled, agent_key}}
claimed_users = {}   # {username: {name, email, key, timestamp}}
agent_keys = {}      # {agent_key: {name, email, timestamp, key_limit, keys_generated}}

# Admin configuration
admin_config = {
  'passcode': 'ABC1322',
  'key_creation_limit': 10  # Default limit
}

# Track key generation count
key_generation_count = 0


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
    activation_key = jsonPayload.get('activation_key')

    # Validate activation key for POST requests (claiming access)
    if request.method == 'POST' and activation_key:
      if activation_key not in activation_keys:
        return json.dumps({'errorMessage': 'Invalid activation key'}), 400, {
          'Content-Type': 'application/json; charset=utf-8'
        }

      key_data = activation_keys[activation_key]
      if key_data['used']:
        return json.dumps({'errorMessage': 'Activation key already used'}), 400, {
          'Content-Type': 'application/json; charset=utf-8'
        }

      # Mark key as used and store claimed user
      key_data['used'] = True
      claimed_users[username] = {
        'name': key_data['name'],
        'email': key_data['email'],
        'key': activation_key,
        'timestamp': time.time()
      }

    print(jsonPayload)
    print(pine_ids)
    tv = tradingview()
    accessList = []
    for pine_id in pine_ids:
      access = tv.get_access_details(username, pine_id)
      accessList = accessList + [access]

    if request.method == 'POST':
      duration = jsonPayload.get('duration', 'L')  # Default to lifetime
      if not duration:
        duration = 'L'

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


@app.route('/validate-agent-key/<key>', methods=['GET'])
def validate_agent_key(key):
  try:
    if key not in agent_keys:
      return json.dumps({'valid': False, 'message': 'Invalid agent key'}), 200, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    return json.dumps({'valid': True, 'name': agent_keys[key]['name']}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/agent')
def agent():
  return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Management - TradingView Access</title>
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
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }

        .header p {
            opacity: 0.9;
            font-size: 16px;
        }

        .login-section {
            padding: 40px;
            text-align: center;
        }

        .content {
            padding: 40px;
            display: none;
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

        input[type="text"], input[type="email"], input[type="password"] {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: #f8f9fa;
        }

        input[type="text"]:focus, input[type="email"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .generate-btn {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(86, 171, 47, 0.3);
        }

        .login-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border-left: 4px solid #667eea;
        }

        .stat-number {
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .section {
            margin-bottom: 40px;
        }

        .section-title {
            font-size: 24px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e1e5e9;
        }

        .table-container {
            overflow-x: auto;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            min-width: 800px;
        }

        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e1e5e9;
        }

        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }

        tr:hover {
            background: #f8f9fa;
        }

        .status-active {
            background: #d4edda;
            color: #155724;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-used {
            background: #f8d7da;
            color: #721c24;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-cancelled {
            background: #fff3cd;
            color: #856404;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }

        .cancelled-key {
            text-decoration: line-through;
            opacity: 0.6;
            transition: opacity 0.3s ease;
        }

        .cancelled-name {
            text-decoration: line-through;
            opacity: 0.6;
            color: #6c757d;
            transition: all 0.3s ease;
        }

        .cancelled-email {
            text-decoration: line-through;
            opacity: 0.6;
            color: #6c757d;
            transition: all 0.3s ease;
        }

        .remove-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-right: 5px;
        }

        .remove-btn:hover {
            background: #c82333;
            transform: translateY(-1px);
        }

        .edit-btn {
            background: #ffc107;
            color: #212529;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-right: 5px;
        }

        .edit-btn:hover {
            background: #e0a800;
            transform: translateY(-1px);
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            animation: fadeIn 0.3s ease;
        }

        .modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            width: 90%;
            max-width: 500px;
            animation: slideIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideIn {
            from { transform: translate(-50%, -60%); opacity: 0; }
            to { transform: translate(-50%, -50%); opacity: 1; }
        }

        .modal h2 {
            color: #333;
            margin-bottom: 10px;
            font-size: 24px;
        }

        .modal p {
            color: #666;
            margin-bottom: 30px;
        }

        .modal-actions {
            display: flex;
            gap: 15px;
            justify-content: flex-end;
            margin-top: 30px;
        }

        .btn-cancel {
            background: #6c757d;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-confirm {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-cancel:hover, .btn-confirm:hover {
            transform: translateY(-1px);
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }

        .empty-state h3 {
            font-size: 24px;
            margin-bottom: 10px;
            color: #999;
        }

        .key-display {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 14px;
            word-break: break-all;
            margin-top: 15px;
            border: 2px solid #e1e5e9;
        }

        .copy-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            margin-top: 10px;
            transition: background 0.3s ease;
        }

        .copy-btn:disabled {
            background: #cccccc;
            cursor: not-allowed;
            opacity: 0.6;
        }

        .copy-btn:hover:not(:disabled) {
            background: #218838;
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

        .actions-column {
            display: flex;
            gap: 5px;
            justify-content: left;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Agent Management</h1>
            <p>Manage activation keys and user access</p>
        </div>

        <!-- Agent Key Login -->
        <div class="login-section" id="loginSection">
            <h2>Agent Access</h2>
            <p>Enter your agent key to access the management panel</p>

            <div class="form-group">
                <label for="agentKey">Agent Key</label>
                <input type="password" id="agentKey" placeholder="Enter your agent key">
            </div>

            <button class="login-btn" onclick="validateAgentKey()">Access Panel</button>

            <div id="loginResult" class="result"></div>
        </div>

        <!-- Main Content -->
        <div class="content" id="mainContent">
            <div class="actions">
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number" id="totalKeys">0</div>
                        <div class="stat-label">Total Keys</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="activeKeys">0</div>
                        <div class="stat-label">Active Keys</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="claimedUsers">0</div>
                        <div class="stat-label">Claimed Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="remainingKeys">0</div>
                        <div class="stat-label">Keys Remaining</div>
                    </div>
                </div>
                <button class="generate-btn" onclick="showGenerateModal()">Generate Key</button>
            </div>

            <div class="section">
                <h2 class="section-title">Activation Keys</h2>
                <div class="table-container">
                    <table id="keysTable">
                        <thead>
                            <tr>
                                <th>Key</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Status</th>
                                <th>Generated</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="keysTableBody">
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">Claimed Users</h2>
                <div class="table-container">
                    <table id="usersTable">
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Claimed Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="usersTableBody">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Generate Key Modal -->
    <div id="generateModal" class="modal">
        <div class="modal-content">
            <h2>Generate Activation Key</h2>
            <p>Create a new activation key for user access</p>

            <div class="form-group">
                <label for="userName">Name</label>
                <input type="text" id="userName" placeholder="Enter full name">
            </div>

            <div class="form-group">
                <label for="userEmail">Email</label>
                <input type="email" id="userEmail" placeholder="Enter email address">
            </div>

            <div class="modal-actions">
                <button class="btn-cancel" onclick="hideGenerateModal()">Cancel</button>
                <button class="btn-confirm" onclick="generateKey()">Generate Key</button>
            </div>
        </div>
    </div>

    <!-- Edit Key Modal -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <h2>Edit Key Details</h2>
            <p>Update the name and email for this activation key</p>

            <div class="form-group">
                <label for="editName">Name</label>
                <input type="text" id="editName" placeholder="Enter full name">
            </div>

            <div class="form-group">
                <label for="editEmail">Email</label>
                <input type="email" id="editEmail" placeholder="Enter email address">
            </div>

            <div class="modal-actions">
                <button class="btn-cancel" onclick="hideEditModal()">Cancel</button>
                <button class="btn-confirm" onclick="updateKeyDetails()">Update Details</button>
            </div>
        </div>
    </div>

    <!-- Key Generated Modal -->
    <div id="keyGeneratedModal" class="modal">
        <div class="modal-content">
            <h2>Key Generated Successfully!</h2>
            <p>Share this activation key with the user:</p>

            <div class="key-display" id="generatedKeyDisplay"></div>
            <button class="copy-btn" onclick="copyKey()">Copy Key</button>

            <div class="modal-actions">
                <button class="btn-confirm" onclick="hideKeyGeneratedModal()">Close</button>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        let generatedKey = '';
        let currentAgentKey = '';
        let editingKey = '';

        async function validateAgentKey() {
            const key = document.getElementById('agentKey').value.trim();

            if (!key) {
                showLoginResult('Please enter your agent key', 'error');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/validate-agent-key/${encodeURIComponent(key)}`);
                const data = await response.json();

                if (response.ok && data.valid) {
                    currentAgentKey = key;
                    document.getElementById('loginSection').style.display = 'none';
                    document.getElementById('mainContent').style.display = 'block';
                    loadData();
                    showLoginResult(`Welcome, ${data.name}!`, 'success');
                } else {
                    showLoginResult(data.message || 'Invalid agent key', 'error');
                }
            } catch (error) {
                showLoginResult(`Network error: ${error.message}`, 'error');
            }
        }

        function showLoginResult(message, type = 'info') {
            const resultDiv = document.getElementById('loginResult');
            resultDiv.innerHTML = message;
            resultDiv.className = `result ${type}`;
            resultDiv.style.display = 'block';

            setTimeout(() => {
                resultDiv.style.display = 'none';
            }, 3000);
        }

        async function loadData() {
            if (!currentAgentKey) return;

            try {
                const response = await fetch(`${API_BASE}/agent/data`, {
                    headers: {
                        'Agent-Key': currentAgentKey
                    }
                });
                const data = await response.json();

                updateStats(data);
                updateKeysTable(data.keys);
                updateUsersTable(data.users);
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }

        function updateStats(data) {
            document.getElementById('totalKeys').textContent = Object.keys(data.keys).length;
            document.getElementById('activeKeys').textContent = Object.values(data.keys).filter(k => !k.used && !k.cancelled).length;
            document.getElementById('claimedUsers').textContent = Object.keys(data.users).length;
            document.getElementById('remainingKeys').textContent = Math.max(0, data.remaining_keys || 0);

            if (data.remaining_keys <= 2 && data.remaining_keys > 0) {
                showLimitWarning(`Warning: Only ${data.remaining_keys} key(s) remaining!`);
            }
        }

        function showLimitWarning(message) {
            const warning = document.createElement('div');
            warning.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                color: #856404;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                z-index: 1000;
                max-width: 300px;
            `;
            warning.textContent = message;
            document.body.appendChild(warning);

            setTimeout(() => {
                if (warning.parentNode) {
                    warning.parentNode.removeChild(warning);
                }
            }, 5000);
        }

        function updateKeysTable(keys) {
            const tbody = document.getElementById('keysTableBody');
            tbody.innerHTML = '';

            const agentKeys = Object.entries(keys).filter(([key, data]) => data.agent_key === currentAgentKey);

            if (agentKeys.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" style="text-align: center; padding: 40px; color: #999;">
                            No activation keys generated yet
                        </td>
                    </tr>
                `;
                return;
            }

            agentKeys.forEach(([key, data]) => {
                const row = document.createElement('tr');
                let status = 'active';
                let statusText = 'Active';

                if (data.used) {
                    status = 'used';
                    statusText = 'Used';
                } else if (data.cancelled) {
                    status = 'cancelled';
                    statusText = 'Cancelled';
                }

                const keyClass = data.cancelled ? 'cancelled-key' : '';
                const nameClass = data.cancelled ? 'cancelled-name' : '';
                const emailClass = data.cancelled ? 'cancelled-email' : '';

                row.innerHTML = `
                    <td><code class="${keyClass}">${key.substring(0, 12)}...</code></td>
                    <td class="${nameClass}">${data.name}</td>
                    <td class="${emailClass}">${data.email}</td>
                    <td><span class="status-${status}">${statusText}</span></td>
                    <td>${new Date(data.timestamp * 1000).toLocaleDateString()}</td>
                    <td class="actions-column">
                        <button class="copy-btn" onclick="copyActivationKey('${key}')" ${data.cancelled ? 'disabled' : ''}>Copy</button>
                        <button class="edit-btn" onclick="editKeyDetails('${key}')">Edit</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function updateUsersTable(users) {
            const tbody = document.getElementById('usersTableBody');
            tbody.innerHTML = '';

            if (Object.keys(users).length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 40px; color: #999;">
                            No users have claimed access yet
                        </td>
                    </tr>
                `;
                return;
            }

            Object.entries(users).forEach(([username, data]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${username}</strong></td>
                    <td>${data.name}</td>
                    <td>${data.email}</td>
                    <td>${new Date(data.timestamp * 1000).toLocaleDateString()}</td>
                    <td><button class="remove-btn" onclick="removeUserAccess('${username}')">Remove Access</button></td>
                `;
                tbody.appendChild(row);
            });
        }

        function showGenerateModal() {
            document.getElementById('generateModal').style.display = 'block';
        }

        function hideGenerateModal() {
            document.getElementById('generateModal').style.display = 'none';
            document.getElementById('userName').value = '';
            document.getElementById('userEmail').value = '';
        }

        function showKeyGeneratedModal(key) {
            generatedKey = key;
            document.getElementById('generatedKeyDisplay').textContent = key;
            document.getElementById('keyGeneratedModal').style.display = 'block';
        }

        function hideKeyGeneratedModal() {
            document.getElementById('keyGeneratedModal').style.display = 'none';
        }

        function editKeyDetails(key) {
            editingKey = key;

            // Get current key data
            fetch(`${API_BASE}/agent/data`, {
                headers: {
                    'Agent-Key': currentAgentKey
                }
            })
            .then(response => response.json())
            .then(data => {
                const keyData = data.keys[key];
                if (keyData) {
                    document.getElementById('editName').value = keyData.name;
                    document.getElementById('editEmail').value = keyData.email;
                    document.getElementById('editModal').style.display = 'block';
                }
            });
        }

        function hideEditModal() {
            document.getElementById('editModal').style.display = 'none';
            document.getElementById('editName').value = '';
            document.getElementById('editEmail').value = '';
            editingKey = '';
        }

        async function updateKeyDetails() {
            const name = document.getElementById('editName').value.trim();
            const email = document.getElementById('editEmail').value.trim();

            if (!name || !email) {
                alert('Please fill in all fields');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/agent/edit-key`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Agent-Key': currentAgentKey
                    },
                    body: JSON.stringify({ 
                        key: editingKey,
                        name: name, 
                        email: email 
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    hideEditModal();
                    loadData();
                    alert('Key details updated successfully!');
                } else {
                    alert(`Error: ${data.errorMessage}`);
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }

        async function generateKey() {
            const name = document.getElementById('userName').value.trim();
            const email = document.getElementById('userEmail').value.trim();

            if (!name || !email) {
                alert('Please fill in all fields');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/agent/generate-key`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Agent-Key': currentAgentKey
                    },
                    body: JSON.stringify({ name, email })
                });

                const data = await response.json();

                if (response.ok) {
                    hideGenerateModal();
                    showKeyGeneratedModal(data.key);
                    loadData();
                } else {
                    if (data.errorMessage && data.errorMessage.includes('limit reached')) {
                        const alertDiv = document.createElement('div');
                        alertDiv.style.cssText = `
                            position: fixed;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                            background: #f8d7da;
                            border: 2px solid #dc3545;
                            color: #721c24;
                            padding: 30px;
                            border-radius: 12px;
                            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                            z-index: 1001;
                            max-width: 400px;
                            text-align: center;
                            font-weight: 600;
                        `;
                        alertDiv.innerHTML = `
                            <h3 style="margin-bottom: 15px;">⚠️ Limit Reached</h3>
                            <p style="margin-bottom: 20px;">${data.errorMessage}</p>
                            <button onclick="this.parentNode.remove()" style="
                                background: #dc3545;
                                color: white;
                                border: none;
                                padding: 10px 20px;
                                border-radius: 6px;
                                cursor: pointer;
                            ">Close</button>
                        `;
                        document.body.appendChild(alertDiv);
                    } else {
                        alert(`Error: ${data.errorMessage}`);
                    }
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }

        function copyKey() {
            copyToClipboard(generatedKey, event.target);
        }

        function copyActivationKey(key) {
            copyToClipboard(key, event.target);
        }

        function copyToClipboard(text, button) {
            // Try modern clipboard API first
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(() => {
                    showCopySuccess(button);
                }).catch(err => {
                    console.error('Clipboard API failed:', err);
                    fallbackCopyTextToClipboard(text, button);
                });
            } else {
                // Fallback for non-secure contexts
                fallbackCopyTextToClipboard(text, button);
            }
        }

        function fallbackCopyTextToClipboard(text, button) {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            textArea.style.top = "-999999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    showCopySuccess(button);
                } else {
                    showCopyError(button, text);
                }
            } catch (err) {
                console.error('Fallback copy failed:', err);
                showCopyError(button, text);
            } finally {
                document.body.removeChild(textArea);
            }
        }

        function showCopySuccess(button) {
            const originalText = button.textContent;
            const originalBackground = button.style.background;
            button.textContent = 'Copied!';
            button.style.background = '#28a745';
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = originalBackground;
            }, 2000);
        }

        function showCopyError(button, text) {
            // Show the text in a prompt for manual copying
            prompt('Copy this text manually:', text);
        }

        async function removeUserAccess(username) {
            if (!confirm(`Are you sure you want to remove access for ${username}?`)) {
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/agent/remove-access/${encodeURIComponent(username)}`, {
                    method: 'DELETE',
                    headers: {
                        'Agent-Key': currentAgentKey
                    }
                });

                const data = await response.json();

                if (response.ok) {
                    alert('Access removed successfully');
                    loadData();
                } else {
                    alert(`Error: ${data.errorMessage}`);
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }

        // Close modal when clicking outside
        window.onclick = function(event) {
            const generateModal = document.getElementById('generateModal');
            const keyGeneratedModal = document.getElementById('keyGeneratedModal');
            const editModal = document.getElementById('editModal');

            if (event.target === generateModal) {
                hideGenerateModal();
            }
            if (event.target === keyGeneratedModal) {
                hideKeyGeneratedModal();
            }
            if (event.target === editModal) {
                hideEditModal();
            }
        }
    </script>
</body>
</html>
  '''


@app.route('/agent/data', methods=['GET'])
def agent_data():
  try:
    agent_key = request.headers.get('Agent-Key')

    if not agent_key or agent_key not in agent_keys:
      return json.dumps({'errorMessage': 'Invalid agent key'}), 401, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    agent_info = agent_keys[agent_key]

    # Filter keys for this agent
    agent_activation_keys = {k: v for k, v in activation_keys.items() if v.get('agent_key') == agent_key}

    return json.dumps({
      'keys': agent_activation_keys,
      'users': claimed_users,
      'key_limit': agent_info.get('key_limit', 10),
      'keys_generated': agent_info.get('keys_generated', 0),
      'remaining_keys': agent_info.get('key_limit', 10) - agent_info.get('keys_generated', 0)
    }), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }
  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/agent/generate-key', methods=['POST'])
def generate_key():
  try:
    agent_key = request.headers.get('Agent-Key')

    if not agent_key or agent_key not in agent_keys:
      return json.dumps({'errorMessage': 'Invalid agent key'}), 401, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    agent_info = agent_keys[agent_key]

    # Check if limit is reached for this agent
    if agent_info['keys_generated'] >= agent_info['key_limit']:
      return json.dumps({'errorMessage': f'Key generation limit reached ({agent_info["key_limit"]}). Contact admin for more keys.'}), 400, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    jsonPayload = request.json
    name = jsonPayload.get('name')
    email = jsonPayload.get('email')

    if not name or not email:
      return json.dumps({'errorMessage': 'Name and email are required'}), 400, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Generate a secure random key
    key = secrets.token_urlsafe(32)

    # Store key data
    activation_keys[key] = {
      'name': name,
      'email': email,
      'timestamp': time.time(),
      'used': False,
      'cancelled': False,
      'agent_key': agent_key
    }

    # Increment key generation count for this agent
    agent_keys[agent_key]['keys_generated'] += 1

    return json.dumps({'key': key}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/agent/edit-key', methods=['POST'])
def edit_key():
  try:
    agent_key = request.headers.get('Agent-Key')

    if not agent_key or agent_key not in agent_keys:
      return json.dumps({'errorMessage': 'Invalid agent key'}), 401, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    jsonPayload = request.json
    key = jsonPayload.get('key')
    name = jsonPayload.get('name')
    email = jsonPayload.get('email')

    if not key or not name or not email:
      return json.dumps({'errorMessage': 'Key, name and email are required'}), 400, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    if key not in activation_keys:
      return json.dumps({'errorMessage': 'Invalid activation key'}), 400, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Check if this key belongs to the agent
    if activation_keys[key].get('agent_key') != agent_key:
      return json.dumps({'errorMessage': 'Unauthorized to edit this key'}), 403, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Update key details
    activation_keys[key]['name'] = name
    activation_keys[key]['email'] = email

    return json.dumps({'success': True}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/agent/remove-access/<username>', methods=['DELETE'])
def remove_user_access(username):
  try:
    agent_key = request.headers.get('Agent-Key')

    if not agent_key or agent_key not in agent_keys:
      return json.dumps({'errorMessage': 'Invalid agent key'}), 401, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    if username not in claimed_users:
      return json.dumps({'errorMessage': 'User not found'}), 404, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Get the user's activation key before removing
    user_data = claimed_users[username]
    activation_key = user_data['key']

    # Check if this key belongs to the agent
    if activation_keys[activation_key].get('agent_key') != agent_key:
      return json.dumps({'errorMessage': 'Unauthorized to remove this user'}), 403, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Remove access using TradingView API
    tv = tradingview()
    pine_ids = ['PUB;2a98f89c2f96420a9bac21052e0c94cf']

    for pine_id in pine_ids:
      access = tv.get_access_details(username, pine_id)
      if access['hasAccess']:
        tv.remove_access(access)

    # Mark the activation key as cancelled
    if activation_key in activation_keys:
      activation_keys[activation_key]['cancelled'] = True

    # Remove from claimed users
    del claimed_users[username]

    # Decrease the key generation count for this agent
    if agent_keys[agent_key]['keys_generated'] > 0:
      agent_keys[agent_key]['keys_generated'] -= 1

    return json.dumps({'success': True, 'message': 'Access removed and key reset successfully'}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/validate-key/<key>', methods=['GET'])
def validate_key(key):
  try:
    if key not in activation_keys:
      return json.dumps({'valid': False, 'message': 'Invalid activation key'}), 200, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    key_data = activation_keys[key]
    if key_data['used']:
      return json.dumps({'valid': False, 'message': 'Activation key already used'}), 200, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    if key_data.get('cancelled', False):
      return json.dumps({'valid': False, 'message': 'Activation key has been cancelled'}), 200, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    return json.dumps({'valid': True, 'name': key_data['name']}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/admin')
def admin():
  return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - TradingView Access</title>
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
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }

        .header p {
            opacity: 0.9;
            font-size: 16px;
        }

        .content {
            padding: 40px;
        }

        .login-form {
            text-align: center;
            margin-bottom: 40px;
        }

        .admin-panel {
            display: none;
        }

        .actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .create-agent-btn {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .create-agent-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(40, 167, 69, 0.3);
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

        input[type="text"], input[type="password"], input[type="number"], input[type="email"] {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: #f8f9fa;
        }

        input[type="text"]:focus, input[type="password"]:focus, input[type="number"]:focus, input[type="email"]:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        button {
            padding: 15px 30px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .login-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .update-btn {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
            color: white;
            width: 100%;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border-left: 4px solid #667eea;
        }

        .stat-number {
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .section {
            margin-bottom: 40px;
        }

        .section-title {
            font-size: 24px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e1e5e9;
        }

        .table-container {
            overflow-x: auto;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }

        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e1e5e9;
        }

        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }

        tr:hover {
            background: #f8f9fa;
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

        .logout-btn {
            background: #dc3545;
            color: white;
            float: right;
            padding: 10px 20px;
            font-size: 14px;
        }

        .copy-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            margin-right: 5px;
            transition: background 0.3s ease;
        }

        .copy-btn:hover {
            background: #218838;
        }

        .edit-btn {
            background: #ffc107;
            color: #212529;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-right: 5px;
        }

        .edit-btn:hover {
            background: #e0a800;
        }

        .remove-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .remove-btn:hover {
            background: #c82333;
            transform: translateY(-1px);
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            animation: fadeIn 0.3s ease;
        }

        .modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            width: 90%;
            max-width: 500px;
            animation: slideIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideIn {
            from { transform: translate(-50%, -60%); opacity: 0; }
            to { transform: translate(-50%, -50%); opacity: 1; }
        }

        .modal h2 {
            color: #333;
            margin-bottom: 10px;
            font-size: 24px;
        }

        .modal p {
            color: #666;
            margin-bottom: 30px;
        }

        .modal-actions {
            display: flex;
            gap: 15px;
            justify-content: flex-end;
            margin-top: 30px;
        }

        .btn-cancel {
            background: #6c757d;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-confirm {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-cancel:hover, .btn-confirm:hover {
            transform: translateY(-1px);
        }

        .key-display {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 14px;
            word-break: break-all;
            margin-top: 15px;
            border: 2px solid #e1e5e9;
        }

        .status-active {
            background: #d4edda;
            color: #155724;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-used {
            background: #f8d7da;
            color: #721c24;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-cancelled {
            background: #fff3cd;
            color: #856404;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }

        .cancelled-key {
            text-decoration: line-through;
            opacity: 0.6;
        }

        .cancelled-name {
            text-decoration: line-through;
            opacity: 0.6;
            color: #6c757d;
        }

        .cancelled-email {
            text-decoration: line-through;
            opacity: 0.6;
            color: #6c757d;
        }

        .agent-info-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
        }

        .agent-info-header h3 {
            margin: 0;
            color: #333;
            font-size: 24px;
        }

        .subsection {
            margin-bottom: 40px;
        }

        .subsection h4 {
            color: #555;
            margin-bottom: 15px;
            font-size: 18px;
            border-bottom: 1px solid #e1e5e9;
            padding-bottom: 10px;
        }

        .manage-btn {
            background: #17a2b8;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-right: 5px;
        }

        .manage-btn:hover {
            background: #138496;
            transform: translateY(-1px);
        }

        .delete-agent-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .delete-agent-btn:hover {
            background: #c82333;
            transform: translateY(-1px);
        }

        .actions-column {
            display: flex;
            gap: 5px;
            justify-content: left;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Admin Panel</h1>
            <p>Manage agents, keys, and access control</p>
        </div>

        <div class="content">
            <!-- Login Form -->
            <div class="login-form" id="loginForm">
                <div class="form-group">
                    <label for="passcode">Admin Passcode</label>
                    <input type="password" id="passcode" placeholder="Enter admin passcode">
                </div>
                <button type="button" class="login-btn" onclick="login()">Login</button>
            </div>

            <!-- Admin Panel -->
            <div class="admin-panel" id="adminPanel">
                <button type="button" class="logout-btn" onclick="logout()">Logout</button>
                <div style="clear: both; margin-bottom: 30px;"></div>

                <div class="actions">
                    <div class="stats" id="stats">
                        <div class="stat-card">
                            <div class="stat-number" id="totalAgents">0</div>
                            <div class="stat-label">Total Agents</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="totalKeys">0</div>
                            <div class="stat-label">Total Keys</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="totalUsers">0</div>
                            <div class="stat-label">Claimed Users</div>
                        </div>
                    </div>
                    <button type="button" class="create-agent-btn" onclick="showCreateAgentModal()">Create Agent</button>
                </div>

                <div class="section">
                    <h2 class="section-title">Agents</h2>
                    <div class="table-container">
                        <table id="agentsTable">
                            <thead>
                                <tr>
                                    <th>Agent Key</th>
                                    <th>Name</th>
                                    <th>Email</th>
                                    <th>Key Limit</th>
                                    <th>Keys Generated</th>
                                    <th>Created</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="agentsTableBody">
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="section">
                    <h2 class="section-title">Agent Details</h2>
                    <div id="agentDetailsSection" style="display: none;">
                        <div class="agent-info-header">
                            <h3 id="selectedAgentName">Agent Name</h3>
                            <button class="btn-cancel" onclick="hideAgentDetails()">← Back to Agents</button>
                        </div>

                        <div class="subsection">
                            <h4>Activation Keys</h4>
                            <div class="table-container">
                                <table id="agentKeysTable">
                                    <thead>
                                        <tr>
                                            <th>Key</th>
                                            <th>Name</th>
                                            <th>Email</th>
                                            <th>Status</th>
                                            <th>Generated</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="agentKeysTableBody">
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <div class="subsection">
                            <h4>Claimed Users</h4>
                            <div class="table-container">
                                <table id="agentUsersTable">
                                    <thead>
                                        <tr>
                                            <th>Username</th>
                                            <th>Name</th>
                                            <th>Email</th>
                                            <th>Claimed Date</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="agentUsersTableBody">
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div id="result" class="result"></div>
        </div>
    </div>

    <!-- Create Agent Modal -->
    <div id="createAgentModal" class="modal">
        <div class="modal-content">
            <h2>Create New Agent</h2>
            <p>Create a new agent account with activation key</p>

            <div class="form-group">
                <label for="agentName">Agent Name</label>
                <input type="text" id="agentName" placeholder="Enter agent name">
            </div>

            <div class="form-group">
                <label for="agentEmail">Agent Email</label>
                <input type="email" id="agentEmail" placeholder="Enter agent email">
            </div>

            <div class="form-group">
                <label for="agentKeyLimit">Key Limit</label>
                <input type="number" id="agentKeyLimit" placeholder="Enter key generation limit" value="10" min="1">
            </div>

            <div class="modal-actions">
                <button class="btn-cancel" onclick="hideCreateAgentModal()">Cancel</button>
                <button class="btn-confirm" onclick="createAgent()">Create Agent</button>
            </div>
        </div>
    </div>

    <!-- Agent Created Modal -->
    <div id="agentCreatedModal" class="modal">
        <div class="modal-content">
            <h2>Agent Created Successfully!</h2>
            <p>Share this agent key with the new agent:</p>

            <div class="key-display" id="agentKeyDisplay"></div>
            <button class="copy-btn" onclick="copyAgentKey()">Copy Agent Key</button>

            <div class="modal-actions">
                <button class="btn-confirm" onclick="hideAgentCreatedModal()">Close</button>
            </div>
        </div>
    </div>

    <!-- Edit Key Limit Modal -->
    <div id="editLimitModal" class="modal">
        <div class="modal-content">
            <h2>Edit Key Limit</h2>
            <p>Set the key generation limit for this agent</p>

            <div class="form-group">
                <label for="newKeyLimit">New Key Limit</label>
                <input type="number" id="newKeyLimit" placeholder="Enter new limit" min="1">
            </div>

            <div class="modal-actions">
                <button class="btn-cancel" onclick="hideEditLimitModal()">Cancel</button>
                <button class="btn-confirm" onclick="updateKeyLimit()">Update Limit</button>
            </div>
        </div>
    </div>

    <!-- Edit Key Details Modal -->
    <div id="editKeyModal" class="modal">
        <div class="modal-content">
            <h2>Edit Key Details</h2>
            <p>Update the name and email for this activation key</p>

            <div class="form-group">
                <label for="editKeyName">Name</label>
                <input type="text" id="editKeyName" placeholder="Enter full name">
            </div>

            <div class="form-group">
                <label for="editKeyEmail">Email</label>
                <input type="email" id="editKeyEmail" placeholder="Enter email address">
            </div>

            <div class="modal-actions">
                <button class="btn-cancel" onclick="hideEditKeyModal()">Cancel</button>
                <button class="btn-confirm" onclick="updateKeyDetails()">Update Details</button>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        let createdAgentKey = '';
        let editingAgentKey = '';
        let editingKey = '';

        // Check if already logged in
        if (sessionStorage.getItem('adminLoggedIn') === 'true') {
            showAdminPanel();
        }

        function login() {
            const passcode = document.getElementById('passcode').value.trim();

            if (!passcode) {
                showResult('Please enter the admin passcode', 'error');
                return;
            }

            fetch(`${API_BASE}/admin/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ passcode: passcode })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    sessionStorage.setItem('adminLoggedIn', 'true');
                    showAdminPanel();
                    showResult('Login successful!', 'success');
                } else {
                    showResult('Invalid passcode', 'error');
                }
            })
            .catch(error => {
                showResult(`Network error: ${error.message}`, 'error');
            });
        }

        function logout() {
            sessionStorage.removeItem('adminLoggedIn');
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('adminPanel').style.display = 'none';
            document.getElementById('passcode').value = '';
            showResult('Logged out successfully', 'success');
        }

        function showAdminPanel() {
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('adminPanel').style.display = 'block';
            loadAdminData();
        }

        function loadAdminData() {
            fetch(`${API_BASE}/admin/data`)
            .then(response => response.json())
            .then(data => {
                updateAdminStats(data);
                updateAgentsTable(data.agents);
            })
            .catch(error => {
                console.error('Error loading admin data:', error);
            });
        }

        function updateAdminStats(data) {
            document.getElementById('totalAgents').textContent = Object.keys(data.agents).length;
            document.getElementById('totalKeys').textContent = Object.keys(data.keys).length;
            document.getElementById('totalUsers').textContent = Object.keys(data.users).length;
        }

        function updateAgentsTable(agents) {
            const tbody = document.getElementById('agentsTableBody');
            tbody.innerHTML = '';

            if (Object.keys(agents).length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" style="text-align: center; padding: 40px; color: #999;">
                            No agents created yet
                        </td>
                    </tr>
                `;
                return;
            }

            Object.entries(agents).forEach(([key, data]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><code>${key.substring(0, 12)}...</code></td>
                    <td>${data.name}</td>
                    <td>${data.email}</td>
                    <td>${data.key_limit}</td>
                    <td>${data.keys_generated}</td>
                    <td>${new Date(data.timestamp * 1000).toLocaleDateString()}</td>
                    <td>
                        <button class="manage-btn" onclick="showAgentDetails('${key}', '${data.name}')">Manage</button>
                        <button class="copy-btn" onclick="copyAgentKeyFromTable('${key}')">Copy Key</button>
                        <button class="edit-btn" onclick="editAgentKeyLimit('${key}')">Edit Limit</button>
                        <button class="delete-agent-btn" onclick="deleteAgent('${key}', '${data.name}')">Delete</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        let currentAgentKey = '';

        function showAgentDetails(agentKey, agentName) {
            currentAgentKey = agentKey;
            document.getElementById('selectedAgentName').textContent = agentName;
            document.getElementById('agentDetailsSection').style.display = 'block';
            loadAgentSpecificData(agentKey);
        }

        function hideAgentDetails() {
            document.getElementById('agentDetailsSection').style.display = 'none';
            currentAgentKey = '';
        }

        function loadAgentSpecificData(agentKey) {
            fetch(`${API_BASE}/admin/agent-data/${encodeURIComponent(agentKey)}`)
            .then(response => response.json())
            .then(data => {
                updateAgentKeysTable(data.keys);
                updateAgentUsersTable(data.users);
            })
            .catch(error => {
                console.error('Error loading agent data:', error);
            });
        }

        function updateAgentKeysTable(keys) {
            const tbody = document.getElementById('agentKeysTableBody');
            tbody.innerHTML = '';

            if (Object.keys(keys).length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" style="text-align: center; padding: 40px; color: #999;">
                            No activation keys generated by this agent
                        </td>
                    </tr>
                `;
                return;
            }

            Object.entries(keys).forEach(([key, data]) => {
                const row = document.createElement('tr');
                let status = 'active';
                let statusText = 'Active';

                if (data.used) {
                    status = 'used';
                    statusText = 'Used';
                } else if (data.cancelled) {
                    status = 'cancelled';
                    statusText = 'Cancelled';
                }

                const keyClass = data.cancelled ? 'cancelled-key' : '';
                const nameClass = data.cancelled ? 'cancelled-name' : '';
                const emailClass = data.cancelled ? 'cancelled-email' : '';

                row.innerHTML = `
                    <td><code class="${keyClass}">${key.substring(0, 12)}...</code></td>
                    <td>${nameClass}">${data.name}</td>
                    <td>${emailClass}">${data.email}</td>
                    <td><span class="status-${status}">${statusText}</span></td>
                    <td>${new Date(data.timestamp * 1000).toLocaleDateString()}</td>
                    <td class="actions-column">
                        <button class="copy-btn" onclick="copyActivationKey('${key}')" ${data.cancelled ? 'disabled' : ''}>Copy</button>
                        <button class="edit-btn" onclick="editKeyDetails('${key}')">Edit</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function updateAgentUsersTable(users) {
            const tbody = document.getElementById('agentUsersTableBody');
            tbody.innerHTML = '';

            if (Object.keys(users).length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 40px; color: #999;">
                            No users have claimed access through this agent
                        </td>
                    </tr>
                `;
                return;
            }

            Object.entries(users).forEach(([username, data]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${username}</strong></td>
                    <td>${data.name}</td>
                    <td>${data.email}</td>
                    <td>${new Date(data.timestamp * 1000).toLocaleDateString()}</td>
                    <td><button class="remove-btn" onclick="removeUserAccessAdmin('${username}')">Remove Access</button></td>
                `;
                tbody.appendChild(row);
            });
        }

        async function deleteAgent(agentKey, agentName) {
            if (!confirm(`Are you sure you want to delete agent "${agentName}"? This will also cancel all their activation keys and remove access for all their users.`)) {
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/admin/delete-agent/${encodeURIComponent(agentKey)}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (response.ok) {
                    alert('Agent deleted successfully');
                    loadAdminData();
                    if (currentAgentKey === agentKey) {
                        hideAgentDetails();
                    }
                } else {
                    alert(`Error: ${data.errorMessage}`);
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }

        function showCreateAgentModal() {
            document.getElementById('createAgentModal').style.display = 'block';
        }

        function hideCreateAgentModal() {
            document.getElementById('createAgentModal').style.display = 'none';
            document.getElementById('agentName').value = '';
            document.getElementById('agentEmail').value = '';
            document.getElementById('agentKeyLimit').value = '10';
        }

        function showAgentCreatedModal(key) {
            createdAgentKey = key;
            document.getElementById('agentKeyDisplay').textContent = key;
            document.getElementById('agentCreatedModal').style.display = 'block';
        }

        function hideAgentCreatedModal() {
            document.getElementById('agentCreatedModal').style.display = 'none';
        }

        function editAgentKeyLimit(agentKey) {
            editingAgentKey = agentKey;

            fetch(`${API_BASE}/admin/data`)
            .then(response => response.json())
            .then(data => {
                const agentData = data.agents[agentKey];
                if (agentData) {
                    document.getElementById('newKeyLimit').value = agentData.key_limit;
                    document.getElementById('editLimitModal').style.display = 'block';
                }
            });
        }

        function hideEditLimitModal() {
            document.getElementById('editLimitModal').style.display = 'none';
            document.getElementById('newKeyLimit').value = '';
            editingAgentKey = '';
        }

        function editKeyDetails(key) {
            editingKey = key;

            fetch(`${API_BASE}/admin/data`)
            .then(response => response.json())
            .then(data => {
                const keyData = data.keys[key];
                if (keyData) {
                    document.getElementById('editKeyName').value = keyData.name;
                    document.getElementById('editKeyEmail').value = keyData.email;
                    document.getElementById('editKeyModal').style.display = 'block';
                }
            });
        }

        function hideEditKeyModal() {
            document.getElementById('editKeyModal').style.display = 'none';
            document.getElementById('editKeyName').value = '';
            document.getElementById('editKeyEmail').value = '';
            editingKey = '';
        }

        async function createAgent() {
            const name = document.getElementById('agentName').value.trim();
            const email = document.getElementById('agentEmail').value.trim();
            const keyLimit = parseInt(document.getElementById('agentKeyLimit').value);

            if (!name || !email || !keyLimit || keyLimit < 1) {
                alert('Please fill in all fields with valid values');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/admin/create-agent`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name, email, key_limit: keyLimit })
                });

                const data = await response.json();

                if (response.ok) {
                    hideCreateAgentModal();
                    showAgentCreatedModal(data.agent_key);
                    loadAdminData();
                } else {
                    alert(`Error: ${data.errorMessage}`);
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }

        async function updateKeyLimit() {
            const newLimit = parseInt(document.getElementById('newKeyLimit').value);

            if (!newLimit || newLimit < 1) {
                alert('Please enter a valid limit');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/admin/update-agent-limit`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ agent_key: editingAgentKey, key_limit: newLimit })
                });

                const data = await response.json();

                if (response.ok) {
                    hideEditLimitModal();
                    loadAdminData();
                    alert('Key limit updated successfully!');
                } else {
                    alert(`Error: ${data.errorMessage}`);
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }

        async function updateKeyDetails() {
            const name = document.getElementById('editKeyName').value.trim();
            const email = document.getElementById('editKeyEmail').value.trim();

            if (!name || !email) {
                alert('Please fill in all fields');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/admin/edit-key`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        key: editingKey,
                        name: name, 
                        email: email 
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    hideEditKeyModal();
                    loadAdminData();
                    alert('Key details updated successfully!');
                } else {
                    alert(`Error: ${data.errorMessage}`);
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }

        async function removeUserAccessAdmin(username) {
            if (!confirm(`Are you sure you want to remove access for ${username}?`)) {
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/admin/remove-access/${encodeURIComponent(username)}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (response.ok) {
                    alert('Access removed successfully');
                    loadAdminData();
                } else {
                    alert(`Error: ${data.errorMessage}`);
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }

        function copyAgentKey() {
            copyToClipboard(createdAgentKey, event.target);
        }

        function copyAgentKeyFromTable(key) {
            copyToClipboard(key, event.target);
        }

        function copyActivationKey(key) {
            copyToClipboard(key, event.target);
        }

        function copyToClipboard(text, button) {
            // Try modern clipboard API first
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(() => {
                    showCopySuccess(button);
                }).catch(err => {
                    console.error('Clipboard API failed:', err);
                    fallbackCopyTextToClipboard(text, button);
                });
            } else {
                // Fallback for non-secure contexts
                fallbackCopyTextToClipboard(text, button);
            }
        }

        function fallbackCopyTextToClipboard(text, button) {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            textArea.style.top = "-999999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    showCopySuccess(button);
                } else {
                    showCopyError(button, text);
                }
            } catch (err) {
                console.error('Fallback copy failed:', err);
                showCopyError(button, text);
            } finally {
                document.body.removeChild(textArea);
            }
        }

        function showCopySuccess(button) {
            const originalText = button.textContent;
            const originalBackground = button.style.background;
            button.textContent = 'Copied!';
            button.style.background = '#28a745';
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = originalBackground;
            }, 2000);
        }

        function showCopyError(button, text) {
            // Show the text in a prompt for manual copying
            prompt('Copy this text manually:', text);
        }

        function showResult(message, type = 'info') {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = message;
            resultDiv.className = `result ${type}`;
            resultDiv.style.display = 'block';

            setTimeout(() => {
                resultDiv.style.display = 'none';
            }, 5000);
        }

        // Close modal when clicking outside
        window.onclick = function(event) {
            const modals = ['createAgentModal', 'agentCreatedModal', 'editLimitModal', 'editKeyModal'];
            modals.forEach(modalId => {
                const modal = document.getElementById(modalId);
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
  '''


@app.route('/admin/data', methods=['GET'])
def admin_data():
  try:
    return json.dumps({
      'agents': agent_keys,
      'keys': activation_keys,
      'users': claimed_users
    }), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }
  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/admin/create-agent', methods=['POST'])
def create_agent():
  try:
    jsonPayload = request.json
    name = jsonPayload.get('name')
    email = jsonPayload.get('email')
    key_limit = jsonPayload.get('key_limit', 10)

    if not name or not email:
      return json.dumps({'errorMessage': 'Name and email are required'}), 400, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Generate a secure random agent key
    agent_key = secrets.token_urlsafe(32)

    # Store agent data
    agent_keys[agent_key] = {
      'name': name,
      'email': email,
      'timestamp': time.time(),
      'key_limit': key_limit,
      'keys_generated': 0
    }

    return json.dumps({'agent_key': agent_key}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/admin/update-agent-limit', methods=['POST'])
def update_agent_limit():
  try:
    jsonPayload = request.json
    agent_key = jsonPayload.get('agent_key')
    key_limit = jsonPayload.get('key_limit')

    if not agent_key or not key_limit or key_limit < 1:
      return json.dumps({'errorMessage': 'Valid agent key and key limit are required'}), 400, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    if agent_key not in agent_keys:
      return json.dumps({'errorMessage': 'Invalid agent key'}), 400, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Update agent key limit
    agent_keys[agent_key]['key_limit'] = key_limit

    return json.dumps({'success': True}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/admin/edit-key', methods=['POST'])
def admin_edit_key():
  try:
    jsonPayload = request.json
    key = jsonPayload.get('key')
    name = jsonPayload.get('name')
    email = jsonPayload.get('email')

    if not key or not name or not email:
      return json.dumps({'errorMessage': 'Key, name and email are required'}), 400, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    if key not in activation_keys:
      return json.dumps({'errorMessage': 'Invalid activation key'}), 400, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Update key details
    activation_keys[key]['name'] = name
    activation_keys[key]['email'] = email

    return json.dumps({'success': True}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/admin/remove-access/<username>', methods=['DELETE'])
def admin_remove_user_access(username):
  try:
    if username not in claimed_users:
      return json.dumps({'errorMessage': 'User not found'}), 404, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Get the user's activation key before removing
    user_data = claimed_users[username]
    activation_key = user_data['key']

    # Remove access using TradingView API
    tv = tradingview()
    pine_ids = ['PUB;2a98f89c2f96420a9bac21052e0c94cf']

    for pine_id in pine_ids:
      access = tv.get_access_details(username, pine_id)
      if access['hasAccess']:
        tv.remove_access(access)

    # Mark the activation key as cancelled
    if activation_key in activation_keys:
      activation_keys[activation_key]['cancelled'] = True
      agent_key = activation_keys[activation_key].get('agent_key')

      # Decrease the key generation count for the associated agent
      if agent_key and agent_key in agent_keys:
        if agent_keys[agent_key]['keys_generated'] > 0:
          agent_keys[agent_key]['keys_generated'] -= 1

    # Remove from claimed users
    del claimed_users[username]

    return json.dumps({'success': True, 'message': 'Access removed and key reset successfully'}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/admin/agent-data/<agent_key>', methods=['GET'])
def admin_agent_data(agent_key):
  try:
    if agent_key not in agent_keys:
      return json.dumps({'errorMessage': 'Agent not found'}), 404, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Filter keys and users for this specific agent
    agent_activation_keys = {k: v for k, v in activation_keys.items() if v.get('agent_key') == agent_key}
    agent_users = {k: v for k, v in claimed_users.items() if v.get('key') in agent_activation_keys}

    return json.dumps({
      'keys': agent_activation_keys,
      'users': agent_users
    }), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }
  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/admin/delete-agent/<agent_key>', methods=['DELETE'])
def admin_delete_agent(agent_key):
  try:
    if agent_key not in agent_keys:
      return json.dumps({'errorMessage': 'Agent not found'}), 404, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    # Get all activation keys for this agent
    agent_activation_keys = [k for k, v in activation_keys.items() if v.get('agent_key') == agent_key]

    # Remove all claimed users that used keys from this agent
    users_to_remove = []
    for username, user_data in claimed_users.items():
      if user_data.get('key') in agent_activation_keys:
        users_to_remove.append(username)

        # Remove TradingView access for each user
        try:
          tv = tradingview()
          pine_ids = ['PUB;2a98f89c2f96420a9bac21052e0c94cf']
          for pine_id in pine_ids:
            access = tv.get_access_details(username, pine_id)
            if access['hasAccess']:
              tv.remove_access(access)
        except Exception as e:
          print(f"[W] Failed to remove TradingView access for {username}: {e}")

    # Remove users from claimed_users
    for username in users_to_remove:
      del claimed_users[username]

    # Remove all activation keys for this agent
    for key in agent_activation_keys:
      del activation_keys[key]

    # Remove the agent
    del agent_keys[agent_key]

    return json.dumps({'success': True, 'message': f'Agent deleted successfully. Removed {len(agent_activation_keys)} keys and {len(users_to_remove)} users.'}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/admin/login', methods=['POST'])
def admin_login():
  try:
    jsonPayload = request.json
    passcode = jsonPayload.get('passcode')

    if passcode == admin_config['passcode']:
      return json.dumps({'success': True}), 200, {
        'Content-Type': 'application/json; charset=utf-8'
      }
    else:
      return json.dumps({'success': False}), 200, {
        'Content-Type': 'application/json; charset=utf-8'
      }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/admin/stats', methods=['GET'])
def admin_stats():
  try:
    return json.dumps({
      'current_limit': admin_config['key_creation_limit'],
      'keys_generated': key_generation_count,
      'remaining_keys': admin_config['key_creation_limit'] - key_generation_count
    }), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
      'Content-Type': 'application/json; charset=utf-8'
    }


@app.route('/admin/update-limit', methods=['POST'])
def admin_update_limit():
  try:
    jsonPayload = request.json
    new_limit = jsonPayload.get('limit')

    if not isinstance(new_limit, int) or new_limit < 1:
      return json.dumps({'success': False, 'errorMessage': 'Invalid limit value'}), 400, {
        'Content-Type': 'application/json; charset=utf-8'
      }

    admin_config['key_creation_limit'] = new_limit

    return json.dumps({'success': True}), 200, {
      'Content-Type': 'application/json; charset=utf-8'
    }

  except Exception as e:
    print("[X] Exception Occurred : ", e)
    return json.dumps({'errorMessage': 'Unknown Exception Occurred'}), 500, {
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
        <h1>TradingView Access Prasad Hoshing Trupti Indicator</h1>
        <p class="subtitle">Claim script access with activation key</p>

        <div class="form-group" id="keyInputGroup">
            <label for="activationKey">Activation Key</label>
            <input type="text" id="activationKey" placeholder="Enter your activation key">
        </div>

        <div class="form-group" id="usernameGroup" style="display: none;">
            <label for="username">TradingView Username</label>
            <input type="text" id="username" placeholder="Enter username to validate">
        </div>

        <div class="button-container">
            <button type="button" class="validate-btn" id="validateKeyBtn" onclick="validateActivationKey()">
                Validate Key
            </button>
            <button type="button" class="validate-btn" id="validateUserBtn" onclick="validateUsername()" style="display: none;">
                Validate User
            </button>
            <button type="button" class="claim-btn" id="claimBtn" onclick="claimAccess()" style="display: none;">
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
        let validatedKey = null;

        // Show validate key button when activation key is entered
        document.getElementById('activationKey').addEventListener('input', function() {
            const key = this.value.trim();
            const validateKeyBtn = document.getElementById('validateKeyBtn');

            if (key) {
                validateKeyBtn.style.display = 'block';
            } else {
                validateKeyBtn.style.display = 'none';
                resetFlow();
            }
        });

        // Show validate user button when username is entered
        document.getElementById('username').addEventListener('input', function() {
            const username = this.value.trim();
            const validateUserBtn = document.getElementById('validateUserBtn');
            const claimBtn = document.getElementById('claimBtn');

            if (username && validatedKey) {
                validateUserBtn.style.display = 'block';
                claimBtn.style.display = 'none';
                validatedUsername = null;
                document.getElementById('userInfo').style.display = 'none';
                document.getElementById('result').style.display = 'none';
            } else {
                validateUserBtn.style.display = 'none';
                claimBtn.style.display = 'none';
            }
        });

        function resetFlow() {
            validatedKey = null;
            validatedUsername = null;
            document.getElementById('usernameGroup').style.display = 'none';
            document.getElementById('validateUserBtn').style.display = 'none';
            document.getElementById('claimBtn').style.display = 'none';
            document.getElementById('userInfo').style.display = 'none';
            document.getElementById('result').style.display = 'none';
        }

        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }

        function showResult(message, type = 'info') {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = message;
            resultDiv.className = `result ${type}`;
            resultDiv.style.display = 'block';
        }

        async function validateActivationKey() {
            const key = document.getElementById('activationKey').value.trim();
            if (!key) {
                showResult('Please enter an activation key', 'error');
                return;
            }

            showLoading(true);
            document.getElementById('result').style.display = 'none';

            try {
                const response = await fetch(`${API_BASE}/validate-key/${encodeURIComponent(key)}`);
                const data = await response.json();

                if (response.ok && data.valid) {
                    validatedKey = key;

                    // Hide key validation, show username input
                    document.getElementById('validateKeyBtn').style.display = 'none';
                    document.getElementById('usernameGroup').style.display = 'block';

                    showResult(`✅ Activation key validated successfully! Welcome, ${data.name}`, 'success');
                } else {
                    showResult(`❌ ${data.message || 'Invalid activation key'}`, 'error');
                }
            } catch (error) {
                showResult(`Network error: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        }

        async function validateUsername() {
            const username = document.getElementById('username').value.trim();
            if (!username || !validatedKey) {
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
                        document.getElementById('validateUserBtn').style.display = 'none';
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
            if (!validatedUsername || !validatedKey) {
                showResult('Please validate both activation key and username first', 'error');
                return;
            }

            // Hardcoded Pine IDs for the claim access functionality
            const pineIds = ['PUB;2a98f89c2f96420a9bac21052e0c94cf'];
            const duration = 'L'; // Lifetime access

            showLoading(true);
            document.getElementById('result').style.display = 'none';

            try {
                const response = await fetch(`${API_BASE}/access/${encodeURIComponent(validatedUsername)}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        pine_ids: pineIds, 
                        duration: duration,
                        activation_key: validatedKey
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    const successMessage = `🎉 Access granted successfully!\\n\\nUser: ${validatedUsername}\\nAccess Level: Lifetime\\nStatus: Active\\n\\nYour activation key has been used and is no longer valid.`;
                    showResult(successMessage, 'success');

                    // Disable all inputs and buttons after successful claim
                    document.getElementById('activationKey').disabled = true;
                    document.getElementById('username').disabled = true;
                    document.getElementById('claimBtn').disabled = true;
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


def start_server():
  app.run(host='0.0.0.0', port=5000, debug=True)