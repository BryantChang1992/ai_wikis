"""Validate public sync metadata without enumerating excluded documents."""
def validate_public_scope(manifest):
    errors = []
    if 'excluded_mixed_documents' in manifest:
        errors.append('Public manifest must not enumerate excluded documents.')
    scope = manifest.get('excluded_scope')
    if not isinstance(scope, str) or not scope.strip():
        errors.append('Public manifest needs a generic excluded_scope statement.')
    elif any(token in scope for token in ('/', '\\', '.md', 'http:', 'https:')):
        errors.append('Excluded scope must not contain document paths or URLs.')
    return errors
