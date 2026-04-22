import os
import xml.etree.ElementTree as ET

def extract_records(accion_tipo, datos, upload_folder):
    """
    Extrae la lista de números (ANI) desde datos manuales o archivos.
    """
    records = []
    if accion_tipo == 'Manual':
        raw_data = datos or ""
        items = raw_data.replace(';', '\n').replace(',', '\n').split('\n')
        for item in items:
            item = item.strip()
            if not item: continue
            if '-' in item:
                try:
                    parts = item.split('-')
                    start = int(parts[0].strip())
                    end = int(parts[1].strip())
                    if start <= end:
                        records.extend([str(x) for x in range(start, end + 1)])
                    else:
                        records.extend([str(x) for x in range(end, start + 1)])
                except:
                    pass
            else:
                records.append(item)
    
    elif accion_tipo == 'Archivo':
        file_path = os.path.join(upload_folder, datos)
        if not os.path.exists(file_path):
            # Reintentar con ruta absoluta si es necesario
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
                        records.append(ani_tag.text.strip())
                if not records:
                    for elem in root.iter():
                        if elem.tag.upper() == 'ANI' and elem.text:
                            records.append(elem.text.strip())
            
            elif ext in ['xlsx', 'xls', 'csv']:
                import pandas as pd
                if ext == 'csv':
                    df = pd.read_csv(file_path, header=None)
                else:
                    df = pd.read_excel(file_path, header=None)
                
                # Tomar la primera columna y convertir a string, removiendo .0 si son floats
                if not df.empty:
                    first_col = df.iloc[:, 0].dropna()
                    for val in first_col:
                        clean_val = str(val).split('.')[0].strip()
                        if clean_val.isdigit():
                            records.append(clean_val)
            else:
                # Fallback para archivos de texto plano
                with open(file_path, 'r') as f:
                    records = [line.strip() for line in f if line.strip() and line.strip().isdigit()]
        except Exception as e:
            print(f"⚠️ Error procesando archivo {datos}: {e}")
            pass
                
    # Eliminar duplicados manteniendo orden inicial aprox
    seen = set()
    return [x for x in records if not (x in seen or seen.add(x))]

def chunk_list(lst, n):
    """Divide una lista en trozos de tamaño n."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
