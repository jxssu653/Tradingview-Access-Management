from flask import Flask, request
from tradingview import tradingview
import json
import secrets
import time
from flask_cors import CORS
#from threading import Thread
app = Flask('')
CORS(app)

# In-memory storage for activation keys and claimed users
activation_keys = {}  # {key: {email, name, timestamp, used}}
claimed_users = {}   # {username: {name, email, key, timestamp}}

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
        
        .content {
            padding: 40px;
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
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        .form-group input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Agent Management</h1>
            <p>Manage activation keys and user access</p>
        </div>
        
        <div class="content">
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
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadData();
        });
        
        async function loadData() {
            try {
                const response = await fetch(`${API_BASE}/agent/data`);
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
            
            // Update the stats display to show limit information
            const statsContainer = document.querySelector('.stats');
            const limitCard = document.createElement('div');
            limitCard.className = 'stat-card';
            
            // Calculate remaining keys excluding cancelled ones
            const totalKeys = Object.keys(data.keys).length;
            const cancelledKeys = Object.values(data.keys).filter(k => k.cancelled).length;
            const usedKeys = Object.values(data.keys).filter(k => k.used && !k.cancelled).length;
            const remainingKeys = data.key_limit - (totalKeys - cancelledKeys);
            
            limitCard.innerHTML = `
                <div class="stat-number">${Math.max(0, remainingKeys)}</div>
                <div class="stat-label">Keys Remaining</div>
            `;
            
            // Remove existing limit card if present
            const existingLimitCard = statsContainer.querySelector('.limit-card');
            if (existingLimitCard) {
                existingLimitCard.remove();
            }
            
            limitCard.classList.add('limit-card');
            statsContainer.appendChild(limitCard);
            
            // Show warning if close to limit
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
            
            if (Object.keys(keys).length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 40px; color: #999;">
                            No activation keys generated yet
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
                    <td class="${nameClass}">${data.name}</td>
                    <td class="${emailClass}">${data.email}</td>
                    <td><span class="status-${status}">${statusText}</span></td>
                    <td>${new Date(data.timestamp * 1000).toLocaleDateString()}</td>
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
                    },
                    body: JSON.stringify({ name, email })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    hideGenerateModal();
                    showKeyGeneratedModal(data.key);
                    loadData(); // Reload data
                } else {
                    if (data.errorMessage && data.errorMessage.includes('limit reached')) {
                        // Show limit reached alert
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
            navigator.clipboard.writeText(generatedKey).then(() => {
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.style.background = '#28a745';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '#28a745';
                }, 2000);
            });
        }
        
        async function removeUserAccess(username) {
            if (!confirm(`Are you sure you want to remove access for ${username}?`)) {
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/agent/remove-access/${encodeURIComponent(username)}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('Access removed successfully');
                    loadData(); // Reload data
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
            
            if (event.target === generateModal) {
                hideGenerateModal();
            }
            if (event.target === keyGeneratedModal) {
                hideKeyGeneratedModal();
            }
        }
    </script>
</body>
</html>
  '''


@app.route('/agent/data', methods=['GET'])
def agent_data():
  try:
    return json.dumps({
      'keys': activation_keys,
      'users': claimed_users,
      'key_limit': admin_config['key_creation_limit'],
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


@app.route('/agent/generate-key', methods=['POST'])
def generate_key():
  try:
    global key_generation_count
    
    # Check if limit is reached
    if key_generation_count >= admin_config['key_creation_limit']:
      return json.dumps({'errorMessage': f'Key generation limit reached ({admin_config["key_creation_limit"]}). Contact admin for more keys.'}), 400, {
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
      'cancelled': False
    }
    
    # Increment key generation count
    key_generation_count += 1
    
    return json.dumps({'key': key}), 200, {
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
    global key_generation_count
    
    if username not in claimed_users:
      return json.dumps({'errorMessage': 'User not found'}), 404, {
        'Content-Type': 'application/json; charset=utf-8'
      }
    
    # Get the user's activation key before removing
    user_data = claimed_users[username]
    activation_key = user_data['key']
    
    # Remove access using TradingView API
    tv = tradingview()
    pine_ids = ['PUB;a34266bd1a4f46c4a6b541b7922c026c']  # Hardcoded Pine ID
    
    for pine_id in pine_ids:
      access = tv.get_access_details(username, pine_id)
      if access['hasAccess']:
        tv.remove_access(access)
    
    # Mark the activation key as cancelled instead of resetting it
    if activation_key in activation_keys:
      activation_keys[activation_key]['cancelled'] = True
    
    # Remove from claimed users
    del claimed_users[username]
    
    # Increase the key generation limit by 1 (reset one key usage)
    if key_generation_count > 0:
      key_generation_count -= 1
    
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
            max-width: 800px;
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
        
        input[type="text"], input[type="password"], input[type="number"] {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: #f8f9fa;
        }
        
        input[type="text"]:focus, input[type="password"]:focus, input[type="number"]:focus {
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Admin Panel</h1>
            <p>Manage key creation limits</p>
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
                
                <div class="stats" id="stats">
                    <div class="stat-card">
                        <div class="stat-number" id="currentLimit">0</div>
                        <div class="stat-label">Current Limit</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="keysGenerated">0</div>
                        <div class="stat-label">Keys Generated</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="remainingKeys">0</div>
                        <div class="stat-label">Remaining Keys</div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="newLimit">Set New Key Creation Limit</label>
                    <input type="number" id="newLimit" placeholder="Enter new limit (e.g., 50)" min="1">
                </div>
                
                <button type="button" class="update-btn" onclick="updateLimit()">Update Limit</button>
            </div>
            
            <div id="result" class="result"></div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        
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
            loadStats();
        }
        
        function loadStats() {
            fetch(`${API_BASE}/admin/stats`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('currentLimit').textContent = data.current_limit;
                document.getElementById('keysGenerated').textContent = data.keys_generated;
                document.getElementById('remainingKeys').textContent = data.remaining_keys;
                document.getElementById('newLimit').value = data.current_limit;
            })
            .catch(error => {
                console.error('Error loading stats:', error);
            });
        }
        
        function updateLimit() {
            const newLimit = parseInt(document.getElementById('newLimit').value);
            
            if (!newLimit || newLimit < 1) {
                showResult('Please enter a valid limit (minimum 1)', 'error');
                return;
            }
            
            fetch(`${API_BASE}/admin/update-limit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ limit: newLimit })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showResult(`Key creation limit updated to ${newLimit}`, 'success');
                    loadStats();
                } else {
                    showResult(`Error: ${data.errorMessage}`, 'error');
                }
            })
            .catch(error => {
                showResult(`Network error: ${error.message}`, 'error');
            });
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
    </script>
</body>
</html>
  '''


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
        <h1>TradingView Access</h1>
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


# def run():
#   app.run(host='0.0.0.0', port=5000)

# def start_server_async():
#   server = Thread(target=run)
#   server.start()


def start_server():
  app.run(host='0.0.0.0', port=5000)
