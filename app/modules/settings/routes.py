from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.modules.settings.models import SystemConfig
from app.modules.audit.models import AuditLog

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")

@settings_bp.route("/")
@login_required
def index():
    config = SystemConfig.query.first()
    return render_template("settings.html", config=config)

@settings_bp.route("/save", methods=["POST"])
@login_required
def save():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        config = SystemConfig.query.first()
        if not config:
            config = SystemConfig()
            db.session.add(config)
            
        # Update General Config
        if "portal_name" in data: config.portal_name = data["portal_name"]
        
        # Identity Logic (Icon vs Image)
        identity_type = data.get("portal_identity_type", "icon")
        config.portal_identity_type = identity_type
        
        raw_identity = data.get("portal_icon", "")
        
        if identity_type == "image" and raw_identity.startswith("data:image"):
            # PHYSICAL SAVING LOGIC
            import base64
            import os
            
            # 1. Define Paths
            branding_dir = os.path.join(os.getcwd(), 'assets', 'img', 'branding')
            if not os.path.exists(branding_dir):
                os.makedirs(branding_dir)
                
            # 2. Extract Base64 Data
            try:
                header, encoded = raw_identity.split(",", 1)
                file_ext = header.split("/")[1].split(";")[0] # png, jpeg, etc
                filename = f"portal_logo.{file_ext}"
                filepath = os.path.join(branding_dir, filename)
                
                # 3. Write File
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(encoded))
                    
                # 4. Store Relative Path in DB
                config.portal_icon = f"/assets/img/branding/{filename}"
            except Exception as e:
                print(f"Error saving physical file: {e}")
                config.portal_icon = raw_identity # Fallback to base64 if fails
        else:
            # For Icons, store the SVG/string as is
            config.portal_icon = raw_identity
            
        if "bg_color" in data: config.bg_color = data["bg_color"]
        if "text_color" in data: config.text_color = data["text_color"]
        
        # Add Audit Log Entry
        audit = AuditLog(
            user=current_user.username,
            action="SET_IDENTITY",
            ip_address=request.remote_addr,
            status="success",
            detail=f"Identidad actualizada ({identity_type}): {config.portal_name}"
        )
        db.session.add(audit)
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Ajustes e Historial Sincronizados"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
