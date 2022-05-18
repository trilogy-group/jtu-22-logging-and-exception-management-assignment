from logger import logger


def get_user_role(token):
    '''
    [Dummy function]
        Returns the user role based on the provided token
            Args:
                token: user's token
            Returns:
                provider, role
    '''
    if token == '0':
        return 'ADMIN'
    elif token == '1':
        return '3PL'
    else:
        logger.error('Invalid token')
        raise Exception('Invalid token')
