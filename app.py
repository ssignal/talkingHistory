import json
import os
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from functools import wraps
import uuid
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
STAGE = os.environ.get("STAGE", "dev")

dynamodb = boto3.resource("dynamodb")
users_table = dynamodb.Table(os.environ["USERS_TABLE"])
history_table = dynamodb.Table(os.environ["HISTORY_TABLE"])

# CORS configuration
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

def ensure_admin_user():
    """Ensure admin email is in the users table"""
    if ADMIN_EMAIL:
        try:
            users_table.put_item(Item={'email': ADMIN_EMAIL})
        except Exception as e:
            print(f"Error adding admin user: {e}")

ensure_admin_user()


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(f"/{STAGE}/login")
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(f"/{STAGE}/login")
        if session.get("email") != ADMIN_EMAIL:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    if "user" in session:
        return redirect(f"/{STAGE}/secret")
    return redirect(f"/{STAGE}/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", google_client_id=GOOGLE_CLIENT_ID, stage=STAGE)
    
    data = request.get_json()
    token = data.get("credential")

    try:
        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )

        email = idinfo.get("email")
        print(f"Login attempt for email: {email}")

        if not email:
            return jsonify(
                {"success": False, "message": "Email not found in token"}
            ), 400

        # Admin can always login
        if email == ADMIN_EMAIL:
            session["user"] = email
            session["email"] = email
            session["name"] = idinfo.get("name", "")
            session["is_admin"] = True
            return jsonify({"success": True, "redirect": f"/{STAGE}/secret"})

        # Check if user is in allowed list
        response = users_table.get_item(Key={"email": email})
        if "Item" in response:
            session["user"] = email
            session["email"] = email
            session["name"] = idinfo.get("name", "")
            session["is_admin"] = False
            return jsonify({"success": True, "redirect": f"/{STAGE}/secret"})
        else:
            return jsonify({
                "success": False, 
                "message": "You are not allowed to access this application. Please wait for the admin to add your email to the allowed user's email list."
            }), 403
    except ValueError as e:
        return jsonify({"success": False, "message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(f"/{STAGE}/login")


@app.route("/secret")
@login_required
def secret_page():
    return render_template("secret.html", stage=STAGE)


@app.route("/data")
@login_required
def data_page():
    return render_template("data.html", stage=STAGE)


@app.route("/add")
@login_required
def add_page():
    return render_template("add.html", stage=STAGE)


@app.route("/search")
@login_required
def search_page():
    return render_template("search.html", stage=STAGE)


@app.route("/users")
@admin_required
def users_page():
    return render_template("users.html", stage=STAGE)


@app.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    try:
        response = users_table.scan()
        items = response.get("Items", [])
        return json.dumps({"users": items}, cls=DecimalEncoder)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users", methods=["POST"])
@admin_required
def add_user():
    try:
        data = request.get_json()
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        users_table.put_item(Item={"email": email})
        return jsonify({"success": True, "email": email})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<email>", methods=["DELETE"])
@admin_required
def delete_user(email):
    try:
        # Prevent admin from deleting their own email
        if email == ADMIN_EMAIL:
            return jsonify({"error": "Cannot delete admin email"}), 400
        
        users_table.delete_item(Key={"email": email})
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
@login_required
def get_history():
    try:
        start_date = request.args.get("startDate")
        end_date = request.args.get("endDate")
        user_email = session.get("email")

        if not start_date or not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(weeks=2)
            start_timestamp = int(start_date.timestamp() * 1000)
            end_timestamp = int(end_date.timestamp() * 1000)
        else:
            # Remove 'Z' and parse as ISO format
            start_date_clean = start_date.replace('Z', '+00:00')
            end_date_clean = end_date.replace('Z', '+00:00')
            start_timestamp = int(datetime.fromisoformat(start_date_clean).timestamp() * 1000)
            end_timestamp = int(datetime.fromisoformat(end_date_clean).timestamp() * 1000)

        # Filter by user email and date range
        response = history_table.scan(
            FilterExpression="userId = :userId AND createdAt BETWEEN :start AND :end",
            ExpressionAttributeValues={
                ":userId": user_email,
                ":start": start_timestamp,
                ":end": end_timestamp,
            },
        )

        items = response.get("Items", [])
        items.sort(key=lambda x: x["createdAt"], reverse=True)

        return json.dumps({"items": items}, cls=DecimalEncoder)
    except Exception as e:
        print(f"Error in get_history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["POST"])
@login_required
def create_history():
    try:
        data = request.get_json()
        
        # Handle date field - could be timestamp or date string
        item_date = data.get('date')
        if item_date:
            # If it's a date string, parse it
            if isinstance(item_date, str):
                try:
                    # Try parsing as ISO date
                    item_date_clean = item_date.replace('Z', '+00:00')
                    created_at = int(datetime.fromisoformat(item_date_clean).timestamp() * 1000)
                except:
                    # If parsing fails, use current time
                    created_at = int(datetime.now().timestamp() * 1000)
            else:
                created_at = int(item_date)
        else:
            created_at = int(datetime.now().timestamp() * 1000)
        
        item = {
            "id": str(uuid.uuid4()),
            "createdAt": created_at,
            "name": data.get("name"),
            "description": data.get("description", ""),
            "text": data.get("text", ""),
            "userId": session["user"],
        }

        history_table.put_item(Item=item)
        return json.dumps({"success": True, "item": item}, cls=DecimalEncoder)
    except Exception as e:
        print(f"Error in create_history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/history/<item_id>", methods=["PUT"])
@login_required
def update_history(item_id):
    try:
        data = request.get_json()
        created_at = int(data.get("createdAt"))

        response = history_table.update_item(
            Key={"id": item_id, "createdAt": created_at},
            UpdateExpression="SET #name = :name, description = :description",
            ExpressionAttributeNames={"#name": "name"},
            ExpressionAttributeValues={
                ":name": data.get("name"),
                ":description": data.get("description"),
            },
            ReturnValues="ALL_NEW",
        )

        return json.dumps(
            {"success": True, "item": response["Attributes"]}, cls=DecimalEncoder
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history/<item_id>", methods=["DELETE"])
@login_required
def delete_history(item_id):
    try:
        created_at = int(request.args.get("createdAt"))

        history_table.delete_item(Key={"id": item_id, "createdAt": created_at})

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search", methods=["GET"])
@login_required
def search_history():
    try:
        start_date = request.args.get("startDate")
        end_date = request.args.get("endDate")
        name = request.args.get("name")
        search_text = request.args.get("searchText")
        match_mode = request.args.get("matchMode", "all")  # 'all' or 'any'
        case_sensitive = request.args.get("caseSensitive", "false").lower() == "true"
        user_email = session.get("email")

        # Get all items for this user
        response = history_table.scan(
            FilterExpression="userId = :userId",
            ExpressionAttributeValues={
                ":userId": user_email
            }
        )
        items = response.get("Items", [])

        # Apply filters based on match mode
        filtered_items = []
        
        for item in items:
            matches = []
            
            # Date range filter
            if start_date and end_date:
                start_date_clean = start_date.replace('Z', '+00:00')
                end_date_clean = end_date.replace('Z', '+00:00')
                start_timestamp = int(datetime.fromisoformat(start_date_clean).timestamp() * 1000)
                end_timestamp = int(datetime.fromisoformat(end_date_clean).timestamp() * 1000)
                matches.append(start_timestamp <= item.get("createdAt", 0) <= end_timestamp)
            
            # Name filter
            if name:
                item_name = str(item.get("name", ""))
                if case_sensitive:
                    matches.append(name in item_name)
                else:
                    matches.append(name.lower() in item_name.lower())
            
            # Text search filter
            if search_text:
                searchable_fields = [
                    str(item.get("name", "")),
                    str(item.get("description", "")),
                    str(item.get("text", ""))
                ]
                searchable_text = " ".join(searchable_fields)
                
                if case_sensitive:
                    matches.append(search_text in searchable_text)
                else:
                    matches.append(search_text.lower() in searchable_text.lower())
            
            # Apply match mode logic
            if not matches:
                # No filters specified, include all items
                filtered_items.append(item)
            elif match_mode == "all":
                # All conditions must match
                if all(matches):
                    filtered_items.append(item)
            else:  # match_mode == "any"
                # At least one condition must match
                if any(matches):
                    filtered_items.append(item)

        filtered_items.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
        return json.dumps({"items": filtered_items}, cls=DecimalEncoder)
    except Exception as e:
        print(f"Error in search_history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def handler(event, context):
    from serverless_wsgi import handle_request

    return handle_request(app, event, context)
