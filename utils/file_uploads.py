# utils/uploads.py
import hashlib
import os
from django.utils.timezone import now

def encrypted_filename(instance, filename, base_folder, app_name=False):
    """
    Retorna o caminho completo com nome de arquivo criptografado.
    
    Args:
        instance: instância do model
        filename: nome original do arquivo
        base_folder: pasta base (ex: 'profile-pictures')
        app_name: nome do app (opcional). Se None, pega instance._meta.app_label
    """
    ext = filename.split('.')[-1]
    hash_input = f"{now().timestamp()}_{filename}".encode('utf-8')
    hashed_name = hashlib.sha256(hash_input).hexdigest()
    new_filename = f"{hashed_name}.{ext}"

    if app_name:
        app_name = instance._meta.app_label
        return os.path.join(base_folder, app_name, new_filename)

    return os.path.join(base_folder, new_filename)