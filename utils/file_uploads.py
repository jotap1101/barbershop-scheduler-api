# utils/uploads.py
import hashlib
import os
from django.utils.timezone import now


def encrypted_filename(
    instance,
    filename,
    base_folder="",
    app_name=True,
    subfolder_func=None,
    subfolder_map=None,
    subfolder_attr=None,
):
    """
    Gera caminho de upload com hash no nome do arquivo.

    Estrutura:
        <app_name>/<base_folder>/<subfolder>/<hash>.<ext>

    - app_name: nome do app do model (instance._meta.app_label)
    - base_folder: pasta base (ex: 'profile_pictures', 'logos', etc.)
    - subfolder_func: função que recebe `instance` e retorna subpasta (modo avançado)
    - subfolder_map: dict de {valor: subpasta} para mapear por atributo
    - subfolder_attr: nome do atributo da instância usado para buscar no map
    """
    # extensão + hash
    ext = filename.split(".")[-1].lower()
    hash_input = f"{now().timestamp()}_{filename}".encode("utf-8")
    hashed_name = hashlib.sha256(hash_input).hexdigest()
    new_filename = f"{hashed_name}.{ext}"

    # partes do caminho
    path_parts = []

    if app_name:
        path_parts.append(instance._meta.app_label)

    if base_folder:
        path_parts.append(base_folder)

    # modo func
    if subfolder_func:
        subfolder = subfolder_func(instance)
        if subfolder:
            path_parts.append(subfolder)

    # modo map
    elif subfolder_map and subfolder_attr:
        value = getattr(instance, subfolder_attr, None)
        if value in subfolder_map:
            path_parts.append(subfolder_map[value])

    path_parts.append(new_filename)

    return os.path.join(*path_parts)
