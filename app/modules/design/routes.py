from flask import Blueprint, render_template, request, jsonify
import os
import re

design_bp = Blueprint("design", __name__, url_prefix="/design")

def hex_to_rgb_str(hex_color):
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    rgb = tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return f"{rgb[0]} {rgb[1]} {rgb[2]}"

@design_bp.route("/")
def index():
    return render_template("design.html")

@design_bp.route("/update", methods=["POST"])
def update_tokens():
    try:
        data = request.json
        token_path = os.path.join(os.getcwd(), 'static', 'css', 'tokens.css')
        
        with open(token_path, 'r') as f:
            content = f.read()

        # Update Logic (Regex based for safety)
        mappings = {
            'light_primary': r'--color-primary:\s*[^;]+;',
            'light_secondary': r'--color-secondary:\s*[^;]+;',
            'light_bg': r'--color-body-bg:\s*[^;]+;',
            'light_panel': r'--color-panel-fill:\s*[^;]+;',
            'radius_base': r'--radius-base:\s*[^;]+;',
            'space_scale': r'--space-1:\s*[^;]+;' 
        }

        rgb_tokens = ['primary', 'secondary', 'panel']

        for key, pattern in mappings.items():
            if key in data:
                val = data[key]
                # Determine if we need RGB or Hex
                is_rgb = any(token in key for token in rgb_tokens)
                
                if is_rgb and '#' in val:
                    val = hex_to_rgb_str(val)
                elif key == 'radius_base': 
                    val = f"{val}px"
                elif key == 'space_scale': 
                    val = f"{int(float(val)*4)}px"
                
                # Replace only first occurrence (root)
                content = re.sub(pattern, f'{pattern.split(":")[0]}: {val};', content, count=1)

        # Dark Mode Updates (Specific block)
        dark_mappings = {
            'dark_bg': r'--color-body-bg:\s*[^;]+;',
            'dark_panel': r'--color-panel-fill:\s*[^;]+;'
        }

        # Find the dark mode block and update inside it
        # This is a bit more manual to avoid breaking the file
        if 'dark_bg' in data or 'dark_panel' in data:
            dark_block_match = re.search(r'html\.dark\s*\{([^}]+)\}', content)
            if dark_block_match:
                dark_block = dark_block_match.group(1)
                if 'dark_bg' in data:
                    dark_block = re.sub(r'--color-body-bg:\s*[^;]+;', f'--color-body-bg: {data["dark_bg"]};', dark_block)
                if 'dark_panel' in data:
                    rgb = hex_to_rgb_str(data['dark_panel'])
                    dark_block = re.sub(r'--color-panel-fill:\s*[^;]+;', f'--color-panel-fill: {rgb};', dark_block)
                content = content.replace(dark_block_match.group(1), dark_block)

        with open(token_path, 'w') as f:
            f.write(content)

        return jsonify({"status": "success", "message": "Diseño actualizado correctamente"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
