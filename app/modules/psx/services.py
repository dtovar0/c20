import os
import xml.etree.ElementTree as ET

def process_item(item):
    """Procesa un item individual, expandiéndolo si es un rango."""
    item = item.strip()
    if not item: return []
    
    if '-' in item:
        try:
            parts = item.split('-')
            # Limpiar caracteres no numéricos excepto el guion
            s_str = "".join(c for c in parts[0] if c.isdigit())
            e_str = "".join(c for c in parts[1] if c.isdigit())
            
            if s_str and e_str:
                start = int(s_str)
                end = int(e_str)
                if start <= end:
                    return [str(x) for x in range(start, end + 1)]
                else:
                    return [str(x) for x in range(end, start + 1)]
        except:
            pass
    
    # Si no es rango o falló expansión, solo números
    clean = "".join(c for c in item if c.isdigit())
    return [clean] if clean else []

def extract_records(accion_tipo, datos, upload_folder):
    """
    Extrae la lista de números (ANI) desde datos manuales o archivos.
    Soporta formato rango: 1147777000-1147777005
    """
    records = []
    if accion_tipo == 'Manual':
        raw_data = datos or ""
        # Separadores comunes: coma, punto y coma, espacio, nueva línea
        items = raw_data.replace(';', '\n').replace(',', '\n').replace(' ', '\n').split('\n')
        for item in items:
            records.extend(process_item(item))
    
    elif accion_tipo == 'Archivo':
        file_path = os.path.join(upload_folder, datos)
        if not os.path.exists(file_path):
            alt_path = os.path.join('/home/dtovar/bayblade/c20/uploads/psx5k', datos)
            if os.path.exists(alt_path):
                file_path = alt_path
            else:
                return []
        
        ext = datos.split('.')[-1].lower()
        
        try:
            if ext == 'xml':
                tree = ET.parse(file_path)
                root = tree.getroot()
                for ani_tag in root.findall('.//ANI'):
                    if ani_tag.text:
                        records.extend(process_item(ani_tag.text))
                if not records:
                    for elem in root.iter():
                        if elem.tag.upper() == 'ANI' and elem.text:
                            records.extend(process_item(elem.text))
            
            elif ext in ['xlsx', 'xls', 'csv']:
                import pandas as pd
                if ext == 'csv':
                    df = pd.read_csv(file_path, header=None, dtype=str)
                else:
                    df = pd.read_excel(file_path, header=None, dtype=str)
                
                if not df.empty:
                    # Buscamos en todas las celdas de la primera fila/columna por si acaso
                    first_col = df.iloc[:, 0].dropna()
                    for val in first_col:
                        records.extend(process_item(str(val)))
            else:
                # Texto plano
                with open(file_path, 'r') as f:
                    for line in f:
                        records.extend(process_item(line))
        except Exception as e:
            print(f"⚠️ Error procesando archivo {datos}: {e}")
            pass
                
    # Eliminar duplicados manteniendo orden
    seen = set()
    return [x for x in records if x and not (x in seen or seen.add(x))]

def chunk_list(lst, n):
    """Divide una lista en trozos de tamaño n."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
