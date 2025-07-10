import logging
import os


def get_logger(name):
    """
    Configura e retorna um logger com formatação padronizada.
    
    Args:
        name (str): Nome do logger (normalmente __name__)
    
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Se o logger já foi configurado, retorna ele
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Cria o diretório de logs se não existir
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configura o arquivo de log
    log_file = os.path.join(log_dir, 'anotaja.log')
    
    # Cria o handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Cria o handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Define o formato das mensagens de log
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Adiciona os handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
