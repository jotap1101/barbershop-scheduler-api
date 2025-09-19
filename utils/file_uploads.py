# utils/uploads.py
import hashlib
import os

from django.utils.timezone import now


def encrypted_filename(
    instance, filename, base_folder="", app_name=True, subfolder_func=None
):
    """
    Retorna o caminho completo com nome de arquivo criptografado.

    Estrutura do caminho:
        <nome_app>/<base_folder>/<subfolder_optional>/<hash>.<ext>

    Args:
        instance: instância do model
        filename: nome original do arquivo
        base_folder: pasta base (ex: 'profile-pictures', 'logos', etc.)
        app_name: se True, adiciona o nome do app (instance._meta.app_label) no início do caminho
        subfolder_func: função opcional que recebe `instance` e retorna uma subpasta adicional (str)
                        Exemplo: lambda inst: "barbers" se inst.role == "barber" else "clients"
    """
    # extensão e hash do arquivo
    ext = filename.split(".")[-1]
    hash_input = f"{now().timestamp()}_{filename}".encode("utf-8")
    hashed_name = hashlib.sha256(hash_input).hexdigest()
    new_filename = f"{hashed_name}.{ext}"

    # lista de partes do caminho
    path_parts = []

    if app_name:
        path_parts.append(instance._meta.app_label)

    if base_folder:
        path_parts.append(base_folder)

    if subfolder_func:
        subfolder = subfolder_func(instance)
        if subfolder:
            path_parts.append(subfolder)

    path_parts.append(new_filename)

    return os.path.join(*path_parts)
