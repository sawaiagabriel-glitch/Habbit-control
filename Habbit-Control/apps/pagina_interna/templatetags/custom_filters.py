from django import template

register = template.Library()

@register.filter
def format_modelo_aparelho(value):
    """Converte valor do modelo do aparelho para formato legível"""
    aparelho_map = {
        'iphone14': 'iPhone 14',
        'iphone13': 'iPhone 13',
        'iphone12': 'iPhone 12',
        'samsung_s23': 'Samsung Galaxy S23',
        'samsung_s22': 'Samsung Galaxy S22',
        'outro': 'Outro',
    }
    return aparelho_map.get(value, value)

@register.filter
def format_telefone(value):
    """Formata telefone para (XX) XXXXX-XXXX"""
    if not value:
        return value
    
    # Remove qualquer caractere que não seja dígito
    digits = ''.join(filter(str.isdigit, str(value)))
    
    # Se tiver 11 dígitos, formata
    if len(digits) == 11:
        return f"({digits[0:2]}) {digits[2:7]}-{digits[7:11]}"
    
    return value
